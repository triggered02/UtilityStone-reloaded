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
PERM_MANAGE = "utilitystone.admin.dailyrewards.manage"

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

    # Admin-only reward milestone management
    if hasPermission(player, PERM_MANAGE):
        addButton(
            form,
            "Manage Rewards",
            on_click=fm.wrapClick(player, lambda: _openManageRewards(plugin, player), "dr_manage"),
        )
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
# Admin — reward milestone management
# ---------------------------------------------------------------------------

def _requireManagePermission(plugin: "UtilityStone", player) -> bool:
    if not hasPermission(player, PERM_MANAGE):
        plugin.messages.failure(player, "You do not have permission to manage daily rewards.")
        return False
    return True


def _backToAdminDailyRewards(plugin: "UtilityStone", player) -> None:
    openDailyRewardsAdmin(plugin, player)


def _openManageRewards(plugin: "UtilityStone", player) -> bool:
    fm = plugin.gui

    if not _requireManagePermission(plugin, player):
        return False

    service = plugin.dailyRewards
    rewards = service.getRewards()

    form = buildActionMenu("Daily Reward Milestones", "Configure reward milestones")

    if not rewards:
        addLabel(form, "No milestones configured yet.")
    else:
        addLabel(form, f"{len(rewards)} milestone(s) configured")
        for day in sorted(rewards.keys()):
            count = len(rewards[day])
            countLabel = "command" if count == 1 else "commands"
            addButton(
                form,
                f"Day {day} ({count} {countLabel})",
                on_click=fm.wrapClick(player, lambda d=day: _openRewardDetail(plugin, player, d), f"dr_edit:{day}"),
            )

    addDivider(form)
    addButton(form, "Add Reward", on_click=fm.wrapClick(player, lambda: _openAddReward(plugin, player), "dr_add"))
    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _backToAdminDailyRewards(plugin, player), "back"))
    return fm.sendForm(player, form, label="daily_rewards_manage")


def _parseMilestoneText(text: str) -> tuple[int, str]:
    """Parse and validate a milestone-day string.  Returns (day, '') or (0, error)."""
    token = (text or "").strip()
    if not token:
        return 0, "Milestone cannot be empty."
    try:
        day = int(token)
    except (ValueError, TypeError):
        return 0, "Milestone must be a whole number."
    if day <= 0:
        return 0, "Milestone must be a positive integer greater than zero."
    return day, ""


def _openAddReward(plugin: "UtilityStone", player) -> None:
    """Ask for a new milestone day, then open the rewards detail to add commands."""
    from endstone_utilitystone.ui.dialogs import askTextInput

    def _onMilestone(text):
        day, err = _parseMilestoneText(text)
        if err:
            plugin.messages.failure(player, err)
            _openAddReward(plugin, player)
            return

        if plugin.dailyRewards.getReward(day) is not None:
            plugin.messages.failure(player, f"A Day {day} reward already exists. Edit it instead.")
            _openAddReward(plugin, player)
            return

        ok, msg = plugin.dailyRewards.createReward(day, [])
        if ok:
            plugin.messages.success(player, f"Day {day} reward created. Now add commands.")
            plugin.gui.untrack(player)
            _openRewardDetail(plugin, player, day)
        else:
            plugin.messages.failure(player, msg)
            plugin.gui.untrack(player)
            _openManageRewards(plugin, player)

    askTextInput(
        plugin,
        player,
        title="Add Reward Milestone",
        label="Milestone day (streak)",
        placeholder="e.g. 7",
        current="",
        onSubmit=_onMilestone,
    )


def _openRewardDetail(plugin: "UtilityStone", player, day: int) -> None:
    fm = plugin.gui

    if not _requireManagePermission(plugin, player):
        return

    service = plugin.dailyRewards
    commands = service.getReward(day)
    if commands is None:
        plugin.messages.failure(player, f"No Day {day} reward exists.")
        plugin.gui.untrack(player)
        _openManageRewards(plugin, player)
        return

    form = buildActionMenu(f"Reward - Day {day}")

    if not commands:
        addLabel(form, "No commands yet. Add one below.")
    else:
        addLabel(form, f"{len(commands)} command(s):")
        for i, command in enumerate(commands):
            addLabel(form, f"{i + 1}. {command}")

    addDivider(form)
    addHeader(form, "Actions")
    addButton(form, "Add Command", on_click=fm.wrapClick(player, lambda: _addCommandInput(plugin, player, day), f"dr_addcmd:{day}"))
    addButton(form, "Edit Command", on_click=fm.wrapClick(player, lambda: _editCommandPicker(plugin, player, day), f"dr_editcmds:{day}"))
    if commands:
        addButton(form, "Remove Command", on_click=fm.wrapClick(player, lambda: _removeCommandPicker(plugin, player, day), f"dr_rmcmd:{day}"))

    addDivider(form)
    addButton(form, "Delete Reward", on_click=fm.wrapClick(player, lambda: _confirmDeleteReward(plugin, player, day), f"dr_del:{day}"))
    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openManageRewards(plugin, player), "back"))
    fm.sendForm(player, form, label=f"daily_rewards_detail:{day}")


def _addCommandInput(plugin: "UtilityStone", player, day: int) -> None:
    from endstone_utilitystone.ui.dialogs import askTextInput

    def _onSubmit(text):
        ok, msg = plugin.dailyRewards.addRewardCommand(day, text)
        if ok:
            plugin.messages.success(player, msg)
        else:
            plugin.messages.failure(player, msg)
        plugin.gui.untrack(player)
        _openRewardDetail(plugin, player, day)

    askTextInput(
        plugin,
        player,
        title=f"Add Command - Day {day}",
        label="Command",
        placeholder="give {player} diamond 3",
        current="",
        onSubmit=_onSubmit,
    )


def _editCommandPicker(plugin: "UtilityStone", player, day: int) -> None:
    fm = plugin.gui

    commands = plugin.dailyRewards.getReward(day) or []
    if not commands:
        plugin.messages.failure(player, "No commands to edit yet.")
        plugin.gui.untrack(player)
        _openRewardDetail(plugin, player, day)
        return

    form = buildActionMenu(f"Edit Command - Day {day}", "Pick the command to edit")

    for i, command in enumerate(commands):
        label = f"Edit #{i + 1}: {command}"
        addButton(
            form,
            label,
            on_click=fm.wrapClick(player, lambda idx=i: _editCommandInput(plugin, player, day, idx), f"dr_editcmd:{day}:{i}"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openRewardDetail(plugin, player, day), "back"))
    fm.sendForm(player, form, label=f"daily_rewards_edit_pick:{day}")


def _editCommandInput(plugin: "UtilityStone", player, day: int, index: int) -> None:
    from endstone_utilitystone.ui.dialogs import askTextInput

    commands = plugin.dailyRewards.getReward(day) or []
    current = commands[index] if 0 <= index < len(commands) else ""

    def _onSubmit(text):
        ok, msg = plugin.dailyRewards.updateRewardCommand(day, index, text)
        if ok:
            plugin.messages.success(player, msg)
        else:
            plugin.messages.failure(player, msg)
        plugin.gui.untrack(player)
        _openRewardDetail(plugin, player, day)

    askTextInput(
        plugin,
        player,
        title=f"Edit Command {index + 1} - Day {day}",
        label="Command",
        placeholder="e.g. give {player} diamond 3",
        current=str(current),
        onSubmit=_onSubmit,
    )


def _removeCommandPicker(plugin: "UtilityStone", player, day: int) -> None:
    fm = plugin.gui

    commands = plugin.dailyRewards.getReward(day) or []
    if not commands:
        _openRewardDetail(plugin, player, day)
        return

    form = buildActionMenu(f"Remove Command - Day {day}", "Pick one command to remove")

    for i, command in enumerate(commands):
        addButton(
            form,
            f"Remove #{i + 1}: {command}",
            on_click=fm.wrapClick(player, lambda idx=i: _doRemoveCommand(plugin, player, day, idx), f"dr_rmcmd:{day}:{i}"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openRewardDetail(plugin, player, day), "back"))
    fm.sendForm(player, form, label=f"daily_rewards_remove_pick:{day}")


def _doRemoveCommand(plugin: "UtilityStone", player, day: int, index: int) -> None:
    ok, msg = plugin.dailyRewards.removeRewardCommand(day, index)
    if ok:
        plugin.messages.success(player, msg)
    else:
        plugin.messages.failure(player, msg)
    plugin.gui.untrack(player)
    _openRewardDetail(plugin, player, day)


def _confirmDeleteReward(plugin: "UtilityStone", player, day: int) -> None:
    from endstone_utilitystone.ui.dialogs import askConfirmation

    def _doDelete(p):
        ok, msg = plugin.dailyRewards.deleteReward(day)
        if ok:
            plugin.messages.success(player, msg)
        else:
            plugin.messages.failure(player, msg)
        plugin.gui.untrack(player)
        _openManageRewards(plugin, player)

    askConfirmation(
        plugin,
        player,
        "Delete Reward",
        f"Delete Day {day} reward? This removes its configured commands.",
        onYes=_doDelete,
    )


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
