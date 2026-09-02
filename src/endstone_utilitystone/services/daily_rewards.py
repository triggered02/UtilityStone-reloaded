"""
Daily Rewards Service.

Players claim a reward once per calendar day.  Streaks are tracked and
rewards are selected via configurable milestone thresholds.

Storage structure (daily_rewards.json):
{
  "players": {
    "player-uuid": {
      "last_claim": "2026-09-01",   // ISO date string (YYYY-MM-DD)
      "streak": 4,
      "total_claims": 27
    }
  }
}

Calendar-day streak rules
-------------------------
* First ever claim:          streak = 1
* Claim on consecutive day:  streak += 1
* One or more days missed:   streak = 1
* Same calendar day:         claim denied

Reward selection
----------------
The streak value *after* a successful claim determines the reward.
The highest configured milestone whose day number is <= the streak wins.
If no milestone qualifies, no command is executed (but the claim succeeds).

Claim ordering
--------------
Player state is persisted *before* reward commands run, so a server crash
or restart can never hand out a duplicate reward.  If a command fails it is
logged but the claim is still consumed — admins can investigate failures
from the console.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone

_REWARDS_HEADER = "[dailyRewards.rewards]"


def _tomlString(text) -> str:
    """Escape a string for use in a TOML double-quoted literal."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _rewriteRewardsSection(tomlText: str, milestones: dict) -> str:
    """Replace the [dailyRewards.rewards] block in *tomlText* with *milestones*.

    Everything else in the file is preserved verbatim.  If the section header
    is missing it is appended at the end of the file.
    """
    lines = tomlText.splitlines()
    headerIdx = None
    for i, line in enumerate(lines):
        if line.strip() == _REWARDS_HEADER:
            headerIdx = i
            break

    block = [_REWARDS_HEADER]
    for day in sorted(int(key) for key in milestones.keys()):
        commands = milestones[day]
        block.append(f"{day} = [")
        for command in commands:
            block.append(f"    {_tomlString(command)},")
        block.append("]")

    if headerIdx is None:
        if lines and lines[-1].strip() != "":
            lines.append("")
        return "\n".join(lines + block)

    endIdx = len(lines)
    for j in range(headerIdx + 1, len(lines)):
        if lines[j].strip().startswith("["):
            endIdx = j
            break

    before = lines[:headerIdx]
    after = lines[endIdx:]
    while before and before[-1].strip() == "":
        before.pop()
    while after and after[0].strip() == "":
        after.pop(0)

    return "\n".join(before + [""] + block + [""] + after)


class DailyRewardsService:
    def __init__(self, plugin: "UtilityStone"):
        self.plugin = plugin
        self.store = plugin.storage.open("daily_rewards", {"players": {}})
        self.store.data.setdefault("players", {})

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------
    @property
    def players(self) -> dict:
        return self.store.data["players"]

    def _key(self, player_uuid) -> str:
        return str(player_uuid)

    def _findRecord(self, player_uuid) -> dict | None:
        return self.players.get(self._key(player_uuid))

    def _getOrCreateRecord(self, player_uuid) -> dict:
        key = self._key(player_uuid)
        record = self.players.get(key)
        if record is None:
            record = {"last_claim": None, "streak": 0, "total_claims": 0}
            self.players[key] = record
        return record

    # ------------------------------------------------------------------
    # Date helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _today() -> datetime.date:
        return datetime.date.today()

    @staticmethod
    def _parseDate(dateStr: str | None) -> datetime.date | None:
        if not dateStr:
            return None
        try:
            return datetime.date.fromisoformat(str(dateStr))
        except (ValueError, TypeError):
            return None

    def _todayIso(self) -> str:
        return self._today().isoformat()

    # ------------------------------------------------------------------
    # Configuration access
    # ------------------------------------------------------------------
    def isEnabled(self) -> bool:
        return self.plugin.settings.dailyRewardsEnabled

    def _milestones(self) -> dict[int, list[str]]:
        return self.plugin.settings.dailyRewardsRewards

    # ------------------------------------------------------------------
    # Player state queries
    # ------------------------------------------------------------------
    def getPlayerState(self, player_uuid) -> dict:
        """Return (last_claim, streak, total_claims) without creating a record."""
        record = self._findRecord(player_uuid)
        if record is None:
            return {"last_claim": None, "streak": 0, "total_claims": 0}
        return {
            "last_claim": record.get("last_claim"),
            "streak": record.get("streak", 0),
            "total_claims": record.get("total_claims", 0),
        }

    def canClaim(self, player_uuid) -> bool:
        """Return True if the player is eligible to claim today."""
        if not self.isEnabled():
            return False
        record = self._findRecord(player_uuid)
        if record is None:
            return True
        lastClaim = self._parseDate(record.get("last_claim"))
        if lastClaim is not None and lastClaim >= self._today():
            return False
        return True

    def _computeStreak(self, record: dict | None) -> int:
        """Compute the streak a player will have after claiming today."""
        today = self._today()
        yesterday = today - datetime.timedelta(days=1)

        if record is None:
            return 1

        lastClaim = self._parseDate(record.get("last_claim"))
        try:
            currentStreak = int(record.get("streak", 0))
        except (TypeError, ValueError):
            currentStreak = 0

        if lastClaim is None:
            return 1
        if lastClaim >= today:
            return max(0, currentStreak)
        if lastClaim == yesterday:
            return max(0, currentStreak) + 1
        # One or more full days missed
        return 1

    def _nextStreak(self, player_uuid) -> int:
        """Compute the streak the player will have after their next claim."""
        return self._computeStreak(self._findRecord(player_uuid))

    def nextClaimDate(self, player_uuid) -> str | None:
        """ISO date string of the next claim, or today if the player can claim now."""
        record = self._findRecord(player_uuid)
        today = self._today()

        if record is not None:
            lastClaim = self._parseDate(record.get("last_claim"))
            if lastClaim is not None and lastClaim >= today:
                return (today + datetime.timedelta(days=1)).isoformat()

        return today.isoformat()

    def timeUntilNextClaim(self, player_uuid) -> float:
        """Seconds until the next claim becomes available (0 if claimable now)."""
        record = self._findRecord(player_uuid)
        today = self._today()

        if record is None:
            return 0.0

        lastClaim = self._parseDate(record.get("last_claim"))
        if lastClaim is None or lastClaim < today:
            return 0.0

        tomorrow = today + datetime.timedelta(days=1)
        now = datetime.datetime.now()
        nextMidnight = datetime.datetime.combine(tomorrow, datetime.time.min)
        return max(0.0, (nextMidnight - now).total_seconds())

    # ------------------------------------------------------------------
    # Milestone / reward selection
    # ------------------------------------------------------------------
    def _findMilestoneDay(self, streak: int) -> int | None:
        """Highest configured milestone day <= streak, or None."""
        milestones = self._milestones()
        if not milestones:
            return None
        selected = None
        for day in sorted(milestones.keys()):
            if day <= streak:
                selected = day
            else:
                break
        return selected

    def getMilestoneReward(self, streak: int) -> list[str]:
        """Return the command list for the given streak."""
        day = self._findMilestoneDay(streak)
        if day is None:
            return []
        return list(self._milestones().get(day, []))

    def describeReward(self, player_uuid) -> str:
        """Human-readable description of the reward the player will receive on next claim."""
        if not self.isEnabled():
            return "Daily Rewards are disabled."

        nextStreak = self._nextStreak(player_uuid)
        commands = self.getMilestoneReward(nextStreak)

        if not commands:
            return f"Day {nextStreak}: no reward configured. Tell an admin."

        day = self._findMilestoneDay(nextStreak)
        lines = [f"Day {day} milestone:"]
        for cmd in commands:
            lines.append(f"  {cmd}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Reward execution
    # ------------------------------------------------------------------
    def _executeCommands(self, player, commands: list[str]) -> list[tuple[str, bool, str | None]]:
        """Dispatch each command as console with {player} replaced.

        Returns a list of (command, success, error) tuples.
        """
        console = self.plugin.server.command_sender
        results: list[tuple[str, bool, str | None]] = []

        for rawCmd in commands:
            try:
                resolved = str(rawCmd).replace("{player}", player.name)
            except Exception:
                resolved = str(rawCmd)

            try:
                self.plugin.server.dispatch_command(console, resolved)
                results.append((resolved, True, None))
            except Exception as exc:
                self.plugin.logger.warning(
                    f"Daily reward command failed for {player.name}: {resolved}: {exc}"
                )
                results.append((resolved, False, str(exc)))

        return results

    # ------------------------------------------------------------------
    # Claim logic
    # ------------------------------------------------------------------
    def claim(self, player) -> tuple[bool, str]:
        """Attempt to claim the daily reward for *player*.

        Returns (success, message).  State is written before commands run
        so a crash cannot cause a duplicate claim.
        """
        uuid = self._key(player.unique_id)

        if not self.isEnabled():
            return False, "Daily Rewards are disabled."

        if not self.canClaim(uuid):
            record = self._findRecord(uuid)
            lastClaim = self._parseDate(record.get("last_claim")) if record else None
            if lastClaim is not None and lastClaim >= self._today():
                nextDate = self.nextClaimDate(uuid)
                return False, f"You already claimed today. Next reward: {nextDate}."
            return False, "You cannot claim a daily reward right now."

        record = self._getOrCreateRecord(uuid)
        newStreak = self._computeStreak(record)

        try:
            priorTotal = int(record.get("total_claims", 0))
        except (TypeError, ValueError):
            priorTotal = 0

        # Persist state BEFORE executing rewards
        record["last_claim"] = self._todayIso()
        record["streak"] = newStreak
        record["total_claims"] = priorTotal + 1
        self.store.markDirty()

        commands = self.getMilestoneReward(newStreak)
        if not commands:
            self.plugin.logger.warning(
                f"No reward commands configured for streak day {newStreak} (player {player.name})"
            )
            streakWord = "first" if newStreak == 1 else f"{newStreak}-day"
            return True, (
                f"Claimed your {streakWord} daily reward! "
                f"No items were configured. Tell an admin."
            )

        results = self._executeCommands(player, commands)
        failedCount = sum(1 for _, ok, _ in results if not ok)

        streakWord = "first" if newStreak == 1 else f"{newStreak}-day"
        totalClaims = int(record.get("total_claims", 0))

        if failedCount:
            msg = (
                f"Claimed your {streakWord} daily reward! "
                f"Streak: {newStreak} days. Total claims: {totalClaims}. "
                f"({failedCount} command(s) failed — check console.)"
            )
        else:
            msg = (
                f"Claimed your {streakWord} daily reward! "
                f"Streak: {newStreak} days. Total claims: {totalClaims}."
            )

        return True, msg

    # ------------------------------------------------------------------
    # Admin operations
    # ------------------------------------------------------------------
    def resetStreak(self, player_uuid) -> tuple[bool, str]:
        """Reset a player's streak to 0 (does NOT clear history)."""
        record = self._findRecord(player_uuid)
        if record is None:
            return False, "Player has no daily reward data."

        record["streak"] = 0
        self.store.markDirty()
        self.plugin.logger.info(
            f"Admin reset daily reward streak for {player_uuid}"
        )
        return True, "Player's daily reward streak has been reset to 0."

    def clearHistory(self, player_uuid) -> tuple[bool, str]:
        """Wipe a player's entire daily reward history."""
        key = self._key(player_uuid)
        if key not in self.players:
            return False, "Player has no daily reward data."

        del self.players[key]
        self.store.markDirty()
        self.plugin.logger.info(
            f"Admin cleared daily reward history for {player_uuid}"
        )
        return True, "Player's daily reward history has been cleared."

    # ------------------------------------------------------------------
    # Reward milestone management (admin)
    #
    # These methods edit the configured reward milestones.  Each write
    # updates the in-memory settings immediately (so the service sees it
    # right away) and then persists the [dailyRewards.rewards] section of
    # config.toml so the change survives a restart.
    # ------------------------------------------------------------------
    def getRewards(self) -> dict[int, list[str]]:
        """Return a copy of all configured reward milestones."""
        rewards = {}
        for day, commands in self._milestones().items():
            try:
                key = int(day)
            except (TypeError, ValueError):
                key = day
            rewards[key] = list(commands)
        return rewards

    def getReward(self, milestone) -> list[str] | None:
        """Return a milestone's commands, or None if it does not exist."""
        day, err = self._validateMilestone(milestone)
        if err:
            return None
        commands = self._milestones().get(day)
        return list(commands) if commands is not None else None

    @staticmethod
    def _validateMilestone(value) -> tuple[int, str]:
        """Validate a milestone day.  Returns (day, '') or (0, error)."""
        try:
            day = int(value)
        except (TypeError, ValueError):
            return 0, "Milestone must be a whole number."
        if day <= 0:
            return 0, "Milestone must be a positive integer greater than zero."
        return day, ""

    @staticmethod
    def _normalizeCommands(commands) -> list[str]:
        """Coerce and strip a commands input into a clean list of strings."""
        if isinstance(commands, str):
            commands = [commands]
        cleaned = []
        if isinstance(commands, (list, tuple)):
            for command in commands:
                if isinstance(command, str) and command.strip():
                    cleaned.append(command.strip())
        return cleaned

    def _commitMilestones(self, milestones: dict, successMessage: str) -> tuple[bool, str]:
        """Apply milestone changes to settings and persist to config.toml."""
        self.plugin.settings.dailyRewardsRewards = milestones
        if not self._persistMilestones(milestones):
            self.plugin.logger.warning(
                "Daily reward milestones changed in memory but config.toml could not be saved."
            )
        return True, successMessage

    def createReward(self, milestone, commands) -> tuple[bool, str]:
        """Create a new reward milestone.  Refuses an existing milestone."""
        day, err = self._validateMilestone(milestone)
        if err:
            return False, err
        if day in self._milestones():
            return False, f"A Day {day} reward already exists. Edit it instead."
        cleaned = self._normalizeCommands(commands)
        new = dict(self._milestones())
        new[day] = cleaned
        return self._commitMilestones(new, f"Day {day} reward created.")

    def setReward(self, milestone, commands) -> tuple[bool, str]:
        """Create or overwrite a milestone's commands."""
        day, err = self._validateMilestone(milestone)
        if err:
            return False, err
        cleaned = self._normalizeCommands(commands)
        new = dict(self._milestones())
        new[day] = cleaned
        action = "updated" if day in self._milestones() else "created"
        return self._commitMilestones(new, f"Day {day} reward {action}.")

    def deleteReward(self, milestone) -> tuple[bool, str]:
        """Remove a milestone entirely."""
        day, err = self._validateMilestone(milestone)
        if err:
            return False, err
        if day not in self._milestones():
            return False, f"No Day {day} reward exists."
        new = dict(self._milestones())
        del new[day]
        return self._commitMilestones(new, f"Day {day} reward deleted.")

    def addRewardCommand(self, milestone, command) -> tuple[bool, str]:
        """Append a single command to an existing milestone."""
        day, err = self._validateMilestone(milestone)
        if err:
            return False, err
        command = self._normalizeCommands([command])
        if not command:
            return False, "Reward command cannot be empty."
        if day not in self._milestones():
            return False, f"No Day {day} reward exists. Add the milestone first."
        updated = list(self._milestones()[day]) + command
        new = dict(self._milestones())
        new[day] = updated
        return self._commitMilestones(new, f"Command added to Day {day} reward.")

    def updateRewardCommand(self, milestone, index, command) -> tuple[bool, str]:
        """Replace the command at *index* on a milestone."""
        day, err = self._validateMilestone(milestone)
        if err:
            return False, err
        command = self._normalizeCommands([command])
        if not command:
            return False, "Reward command cannot be empty."
        current = self._milestones().get(day)
        if current is None:
            return False, f"No Day {day} reward exists."
        try:
            idx = int(index)
        except (TypeError, ValueError):
            return False, "Invalid command index."
        if not 0 <= idx < len(current):
            return False, f"Command index out of range (0-{len(current) - 1})."
        updated = list(current)
        updated[idx] = command[0]
        new = dict(self._milestones())
        new[day] = updated
        return self._commitMilestones(new, f"Command {idx + 1} on Day {day} updated.")

    def removeRewardCommand(self, milestone, index) -> tuple[bool, str]:
        """Remove the command at *index* from a milestone."""
        day, err = self._validateMilestone(milestone)
        if err:
            return False, err
        current = self._milestones().get(day)
        if current is None:
            return False, f"No Day {day} reward exists."
        try:
            idx = int(index)
        except (TypeError, ValueError):
            return False, "Invalid command index."
        if not 0 <= idx < len(current):
            return False, f"Command index out of range (0-{len(current) - 1})."
        updated = list(current)
        removed = updated.pop(idx)
        new = dict(self._milestones())
        new[day] = updated
        return self._commitMilestones(new, f"Removed command {idx + 1} ({removed}) from Day {day}.")

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------
    def _configPath(self) -> Path:
        folder = getattr(self.plugin, "data_folder", None) or ""
        return Path(folder) / "config.toml"

    def _persistMilestones(self, milestones: dict) -> bool:
        """Write the rewards section to config.toml.  Returns True on success."""
        path = self._configPath()
        if not path.exists():
            self.plugin.logger.warning(f"config.toml not found at {path} - rewards not saved to disk.")
            return False

        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            self.plugin.logger.warning(f"Could not read config.toml: {exc}")
            return False

        try:
            updated = _rewriteRewardsSection(raw, milestones)
        except Exception as exc:
            self.plugin.logger.error(f"Could not build config.toml update: {exc}")
            return False

        try:
            temporary = path.with_name("config.toml.tmp")
            temporary.write_text(updated, encoding="utf-8")
            os.replace(temporary, path)
        except OSError as exc:
            self.plugin.logger.error(f"Could not write config.toml: {exc}")
            try:
                temporary = path.with_name("config.toml.tmp")
                if temporary.exists():
                    temporary.unlink()
            except Exception:
                pass
            return False
        return True
