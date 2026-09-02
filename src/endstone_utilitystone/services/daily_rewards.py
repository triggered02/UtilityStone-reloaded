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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


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
