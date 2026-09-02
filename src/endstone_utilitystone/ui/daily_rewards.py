"""
Daily Rewards UI — player menu button, daily reward screen, and admin inspection.

Navigation:
    Player Menu → Utilities → Daily Reward
    Admin Panel → Daily Rewards → Select Player → Reward Detail
    Player Inspector → Daily Rewards → Reward Detail
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from endstone_utilitystone.ui.components import (
    addDivider,
    addHeader,
    addLabel,
    addButton,
    buildActionMenu,
)
from endstone_utilitystone.ui.permissions import hasPermission

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone

# Permission nodes
PERM_VIEW = "utilitystone.admin.dailyrewards.view"
PERM_RESET = "utilitystone.admin.dailyrewards.reset"

# Player-facing permission node
PLAYER_PERMISSION = "utilitystone.command.dailyreward"


# ---------------------------------------------------------------------------
# Player-facing Daily Reward screen
# ---------------------------------------------------------------------------

def openDailyReward(plugin: "UtilityStone", player) -> bool:
    fm = plugin.gui

    form = buildActionMenu("Daily Reward")

    if not plugin.dailyRewards or not plugin.dailyRewards.isEnabled():
        addLabel(form, "Daily Rewards are disabled.")
        addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _backToPlayerMenu(plugin, player), "back"))
        return fm.sendForm(player, form, label="daily_reward_disabled")

    service = plugin.dailyRewards
    uid = str(player.unique_id)
    state = service.getPlayerState(uid)
    streak = state["streak"]
    total = state["total_claims"]
    canClaim = service.canClaim(uid)

    addLabel(form, f"Streak: {streak} day(s)")
    addLabel(form, f"Total Claims: {total}")

    if canClaim:
        addLabel(form, "Claim available today!")
        addDivider(form)
        addHeader(form, "Today's Reward")
        desc = service.describeReward(uid)
        for line in desc.split("\n"):
            addLabel(form, line)
        addDivider(form)
        addButton(
            form,
            "Claim Reward",
            on_click=fm.wrapClick(player, lambda: _claimReward(plugin, player), "daily_claim"),
        )
    else:
        addLabel(form, "Already claimed today.")
        nextDate = service.nextClaimDate(uid)
        waiting = service.timeUntilNextClaim(uid)
        from endstone_utilitystone.util.durations import formatDuration

        addLabel(form, f"Next reward: {nextDate}")
        addLabel(form, f"Time remaining: {formatDuration(waiting)}")

    addDivider(form)
    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _backToPlayerMenu(plugin, player), "back"))
    return fm.sendForm(player, form, label="daily_reward")


def _claimReward(plugin: "UtilityStone", player) -> None:
    success, message = plugin.dailyRewards.claim(player)
    if success:
        plugin.messages.success(player, message)
    else:
        plugin.messages.failure(player, message)
    plugin.gui.untrack(player)


def _backToPlayerMenu(plugin: "UtilityStone", player) -> None:
    from endstone_utilitystone.ui.player_menu import openPlayerMenu
    openPlayerMenu(plugin, player)


# ---------------------------------------------------------------------------
# Admin — system status + player selector
# ---------------------------------------------------------------------------

def openDailyRewardsAdmin(plugin: "UtilityStone", player) -> bool:
    """Admin entry point: shows system status and lets you pick an online player."""
    fm = plugin.gui

    if not hasPermission(player, PERM_VIEW):
        plugin.messages.failure(player, "You do not have permission to view daily rewards.")
        return False

    form = buildActionMenu("Daily Rewards", "Server daily rewards administration")

    service = plugin.dailyRewards
    if service is None or not service.isEnabled():
        addLabel(form, "Daily Rewards are DISABLED.")
    else:
        addLabel(form, "Daily Rewards are ENABLED.")
        addLabel(form, f"Players tracked: {len(service.players)}")

    addDivider(form)
    addHeader(form, "Select Player")

    online = [p for p in plugin.server.online_players if p.unique_id != player.unique_id]
    if not online:
        addLabel(form, "No other players online.")
    else:
        addLabel(form, f"{len(online)} players online")
        for target in online:
            targetName = target.name
            addButton(
                form,
                targetName,
                on_click=fm.wrapClick(player, lambda p=player, t=target: _openPlayerDetail(plugin, p, t), f"dr_player:{targetName}"),
            )

    addDivider(form)
    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _backToAdminPanel(plugin, player), "back"))
    return fm.sendForm(player, form, label="admin_daily_rewards")


def _backToAdminPanel(plugin: "UtilityStone", player) -> None:
    from endstone_utilitystone.ui.admin_menu import openAdminPanel
    openAdminPanel(plugin, player)


# ---------------------------------------------------------------------------
# Admin — player detail
# ---------------------------------------------------------------------------

def _openPlayerDetail(plugin: "UtilityStone", player, target, backTo: str = "admin") -> None:
    fm = plugin.gui

    if not hasPermission(player, PERM_VIEW):
        plugin.messages.failure(player, "You do not have permission to view daily rewards.")
        return

    service = plugin.dailyRewards
    uid = str(target.unique_id)
    state = service.getPlayerState(uid) if service else {"last_claim": None, "streak": 0, "total_claims": 0}

    form = buildActionMenu(f"Rewards: {target.name}", "Daily reward state")

    addHeader(form, "Information")
    addLabel(form, f"UUID: {target.unique_id}")
    addLabel(form, f"Streak: {state['streak']} day(s)")
    addLabel(form, f"Total Claims: {state['total_claims']}")
    addLabel(form, f"Last Claim: {state['last_claim'] or 'never'}")
    if service and service.isEnabled():
        addLabel(form, f"Can Claim: {service.canClaim(uid)}")
    else:
        addLabel(form, "Can Claim: (disabled)")

    addDivider(form)
    addHeader(form, "Actions")

    if hasPermission(player, PERM_RESET):
        addButton(
            form,
            "Reset Streak",
            on_click=fm.wrapClick(player, lambda p=player, t=target: _resetStreak(plugin, p, t), f"dr_reset_streak:{target.name}"),
        )
        addButton(
            form,
            "Clear History",
            on_click=fm.wrapClick(player, lambda p=player, t=target: _clearHistory(plugin, p, t), f"dr_clear_history:{target.name}"),
        )
    else:
        addLabel(form, "No admin permissions for rewards.")

    if backTo == "inspector":
        from endstone_utilitystone.ui.admin_player_tools import _openPlayerInspector
        addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openPlayerInspector(plugin, player, target), "back"))
    else:
        addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openDailyRewardsAdmin(plugin, player), "back"))
    fm.sendForm(player, form, label=f"admin_daily_rewards:{target.name}")


def openPlayerDailyRewardDetail(plugin: "UtilityStone", admin, target) -> None:
    """Public entry from the Player Inspector: show a player's daily reward detail."""
    _openPlayerDetail(plugin, admin, target, backTo="inspector")


def _resetStreak(plugin: "UtilityStone", player, target) -> None:
    _audit(plugin, player, "reset daily reward streak of", target.name)
    ok, msg = plugin.dailyRewards.resetStreak(str(target.unique_id))
    if ok:
        plugin.messages.success(player, msg)
        plugin.messages.notice(target, f"An admin reset your daily reward streak.")
    else:
        plugin.messages.failure(player, msg)
    plugin.gui.untrack(player)


def _clearHistory(plugin: "UtilityStone", player, target) -> None:
    _audit(plugin, player, "cleared daily reward history of", target.name)
    ok, msg = plugin.dailyRewards.clearHistory(str(target.unique_id))
    if ok:
        plugin.messages.success(player, msg)
        plugin.messages.notice(target, f"An admin cleared your daily reward history.")
    else:
        plugin.messages.failure(player, msg)
    plugin.gui.untrack(player)


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------

def _audit(plugin: "UtilityStone", admin, action: str, target_name: str) -> None:
    plugin.logger.info(f"Admin {admin.name} {action} {target_name}")
