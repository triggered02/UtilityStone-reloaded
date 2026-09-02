"""
Daily Rewards commands.

/dailyreward               Claim today's reward (or show status if already claimed).
/dailyreward claim         Claim today's reward explicitly.
/dailyreward status        Show current streak, total claims, and next claim date.
"""

from __future__ import annotations

from endstone_utilitystone.commands.base import CommandGroup
from endstone_utilitystone.util.durations import formatDuration
from endstone_utilitystone.util.text import colorize

PLAYER_PERMISSION = "utilitystone.command.dailyreward"


class DailyRewardsCommands(CommandGroup):
    def bindings(self) -> dict:
        return {
            "dailyreward": self.route,
        }

    def route(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.command.dailyreward"):
            self.messages.failure(sender, "You do not have permission to use daily rewards.")
            return True

        action = args[0].lower() if args else ""

        if action in ("", "claim"):
            return self._claim(sender)
        if action == "status":
            return self._status(sender)

        self.messages.info(sender, "Usage: /dailyreward [claim|status]")
        return True

    # ------------------------------------------------------------------
    # /dailyreward claim
    # ------------------------------------------------------------------
    def _claim(self, sender) -> bool:
        player = self.asPlayer(sender)
        if player is None:
            return True

        if self.plugin.dailyRewards is None:
            self.messages.failure(player, "Daily Rewards are not available.")
            return True

        success, message = self.plugin.dailyRewards.claim(player)
        if success:
            self.messages.success(player, message)
        else:
            self.messages.failure(player, message)
        return True

    # ------------------------------------------------------------------
    # /dailyreward status
    # ------------------------------------------------------------------
    def _status(self, sender) -> bool:
        player = self.asPlayer(sender)
        if player is None:
            return True

        if self.plugin.dailyRewards is None:
            self.messages.failure(player, "Daily Rewards are not available.")
            return True

        service = self.plugin.dailyRewards
        uid = str(player.unique_id)
        state = service.getPlayerState(uid)
        streak = state["streak"]
        total = state["total_claims"]
        lastClaim = state["last_claim"] or "never"

        player.send_message(colorize(f"&eDaily Rewards &7— &fStreak: &6{streak} &7| &fTotal Claims: &b{total}"))
        player.send_message(colorize(f"&7Last claim: &f{lastClaim}"))

        if service.canClaim(uid):
            player.send_message(colorize("&aAvailable to claim!"))
            desc = service.describeReward(uid)
            for line in desc.split("\n"):
                player.send_message(colorize(f"&7  {line}"))
        else:
            nextDate = service.nextClaimDate(uid)
            waiting = service.timeUntilNextClaim(uid)
            player.send_message(colorize("&cAlready claimed today."))
            player.send_message(colorize(f"&7Next available: &f{nextDate}"))
            player.send_message(colorize(f"&7Time remaining: &f{formatDuration(waiting)}"))

        return True
