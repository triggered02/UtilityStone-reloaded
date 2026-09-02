"""
Admin Player Tools — Player Inspector, Homes, Inventory, Ender Chest.

Navigation:
    Admin Panel → Players → Select Player → Player Inspector
    Admin Panel → Players → Select Player → View Homes
    Admin Panel → Players → Select Player → View Inventory
    Admin Panel → Players → Select Player → View Ender Chest
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from endstone_utilitystone.ui.components import (
    addDivider,
    addHeader,
    addLabel,
    addButton,
    buildActionMenu,
    emptyState,
)
from endstone_utilitystone.ui.permissions import hasAdminGui, hasPermission

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone

# ---------------------------------------------------------------------------
# Permission nodes
# ---------------------------------------------------------------------------
PERM_INSPECT = "utilitystone.admin.players.inspect"
PERM_HOMES_VIEW = "utilitystone.admin.homes.view"
PERM_HOMES_TELEPORT = "utilitystone.admin.homes.teleport"
PERM_HOMES_DELETE = "utilitystone.admin.homes.delete"
PERM_INVENTORY_VIEW = "utilitystone.admin.inventory.view"
PERM_ENDERCHEST_VIEW = "utilitystone.admin.enderchest.view"

ITEMS_PER_PAGE = 7


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------
def _audit(plugin: UtilityStone, admin, action: str, target_name: str) -> None:
    plugin.logger.info(f"Admin {admin.name} {action} {target_name}")


# ---------------------------------------------------------------------------
# Permission gate
# ---------------------------------------------------------------------------
def _requirePermission(plugin: UtilityStone, player, perm: str, label: str) -> bool:
    if not hasPermission(player, perm):
        plugin.messages.failure(player, f"You do not have permission to {label}.")
        return False
    return True


# ---------------------------------------------------------------------------
# Player List (Feature 5)
# ---------------------------------------------------------------------------
def openPlayerList(plugin: UtilityStone, player) -> bool:
    fm = plugin.gui

    if not _requirePermission(plugin, player, PERM_INSPECT, "view the player list"):
        return False

    form = buildActionMenu("Player Management", "Select a player to inspect")

    online = list(plugin.server.online_players)
    if not online:
        addLabel(form, "No players online.")
    else:
        addLabel(form, f"{len(online)} players online")
        for target in online:
            targetName = target.name
            session = plugin.sessions.of(target)
            afkTag = " [AFK]" if session and session.isAfk else ""
            addButton(
                form,
                f"{targetName}{afkTag}",
                on_click=fm.wrapClick(player, lambda p=player, t=target: _openPlayerInspector(plugin, p, t), f"inspect:{targetName}"),
            )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openAdminPanel(plugin, player), "back"))
    return fm.sendForm(player, form, label="admin_player_list")


def _openAdminPanel(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.admin_menu import openAdminPanel
    openAdminPanel(plugin, player)


# ---------------------------------------------------------------------------
# Player Inspector (Feature 1)
# ---------------------------------------------------------------------------
def _openPlayerInspector(plugin: UtilityStone, player, target) -> None:
    fm = plugin.gui

    if not _requirePermission(plugin, player, PERM_INSPECT, "inspect players"):
        return

    _audit(plugin, player, "inspected player", target.name)

    form = buildActionMenu(f"Inspect: {target.name}", "Player information and actions")

    # ── Information ──
    addHeader(form, "Information")

    from endstone_utilitystone.util.locations import describeLocation

    addLabel(form, f"Username: {target.name}")
    addLabel(form, f"UUID: {target.unique_id}")
    addLabel(form, f"Gamemode: {target.game_mode.name.title()}")
    addLabel(form, f"Dimension: {target.location.dimension.name}")
    addLabel(form, f"Coordinates: {target.location.block_x}, {target.location.block_y}, {target.location.block_z}")
    addLabel(form, f"Health: {target.health:.0f}/{target.max_health:.0f}")
    addLabel(form, f"Ping: {target.ping}ms")

    session = plugin.sessions.of(target)
    if session and session.isAfk:
        addLabel(form, f"Status: AFK")

    profile = plugin.profiles.profileFor(target)
    if profile:
        from endstone_utilitystone.util.durations import formatTimestamp
        addLabel(form, f"First seen: {formatTimestamp(float(profile.get('firstSeen', 0.0)))}")

    # Rank display
    if plugin.ranks is not None:
        rank_name = plugin.ranks.getEffectiveRankName(target)
        rank_def = plugin.ranks.getRankDefinition(rank_name)
        rank_priority = rank_def.get("priority", 0) if rank_def else 0
        addLabel(form, f"Rank: {rank_name} (priority: {rank_priority})")

    # ── Actions ──
    addDivider(form)
    addHeader(form, "Actions")

    # Change Rank button
    if plugin.ranks is not None and hasPermission(player, "utilitystone.admin.ranks.assign"):
        addButton(
            form,
            "Change Rank",
            on_click=fm.wrapClick(player, lambda: _openChangeRank(plugin, player, target), f"change_rank:{target.name}"),
        )

    # Daily Rewards button
    if hasPermission(player, "utilitystone.admin.dailyrewards.view"):
        addButton(
            form,
            "Daily Rewards",
            on_click=fm.wrapClick(player, lambda: _openDailyRewards(plugin, player, target), f"daily_rewards:{target.name}"),
        )

    if hasPermission(player, PERM_HOMES_TELEPORT):
        addButton(
            form,
            "Teleport To Player",
            on_click=fm.wrapClick(player, lambda: _teleportToTarget(plugin, player, target), f"tp_to:{target.name}"),
        )
        addButton(
            form,
            "Teleport Player To Me",
            on_click=fm.wrapClick(player, lambda: _teleportTargetToMe(plugin, player, target), f"tp_target:{target.name}"),
        )

    if hasPermission(player, PERM_HOMES_VIEW):
        addButton(
            form,
            "View Homes",
            on_click=fm.wrapClick(player, lambda: _openAdminHomesForPlayer(plugin, player, target), f"homes:{target.name}"),
        )

    if hasPermission(player, PERM_INVENTORY_VIEW):
        addButton(
            form,
            "View Inventory",
            on_click=fm.wrapClick(player, lambda: _openInventoryView(plugin, player, target, 0), f"inv:{target.name}"),
        )

    if hasPermission(player, PERM_ENDERCHEST_VIEW):
        addButton(
            form,
            "View Ender Chest",
            on_click=fm.wrapClick(player, lambda: _openEnderChestView(plugin, player, target, 0), f"ender:{target.name}"),
        )

    # ── Player Actions ──
    addDivider(form)
    addHeader(form, "Player Actions")

    addButton(
        form,
        "Heal",
        on_click=fm.wrapClick(player, lambda: _healPlayer(plugin, player, target), f"heal:{target.name}"),
    )
    addButton(
        form,
        "Feed",
        on_click=fm.wrapClick(player, lambda: _feedPlayer(plugin, player, target), f"feed:{target.name}"),
    )

    flyState = "Disable Fly" if target.allow_flight else "Enable Fly"
    addButton(
        form,
        flyState,
        on_click=fm.wrapClick(player, lambda: _toggleFly(plugin, player, target), f"fly:{target.name}"),
    )

    godState = "Disable God" if target.unique_id in plugin.godPlayers else "Enable God"
    addButton(
        form,
        godState,
        on_click=fm.wrapClick(player, lambda: _toggleGod(plugin, player, target), f"god:{target.name}"),
    )

    # Mute section
    mute = plugin.punishments.muteFor(str(target.unique_id))
    if mute:
        remaining = plugin.punishments.remainingMute(mute)
        from endstone_utilitystone.util.durations import formatDuration
        addLabel(form, f"Muted: {formatDuration(remaining)} left")
        addButton(
            form,
            "Unmute",
            on_click=fm.wrapClick(player, lambda: _unmutePlayer(plugin, player, target), f"unmute:{target.name}"),
        )
    else:
        addButton(
            form,
            "Mute (30m)",
            on_click=fm.wrapClick(player, lambda: _mutePlayer(plugin, player, target, 1800), f"mute30:{target.name}"),
        )
        addButton(
            form,
            "Mute (1h)",
            on_click=fm.wrapClick(player, lambda: _mutePlayer(plugin, player, target, 3600), f"mute1h:{target.name}"),
        )
        addButton(
            form,
            "Mute (24h)",
            on_click=fm.wrapClick(player, lambda: _mutePlayer(plugin, player, target, 86400), f"mute24h:{target.name}"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openPlayerList(plugin, player), "back"))
    fm.sendForm(player, form, label=f"inspector:{target.name}")


# ---------------------------------------------------------------------------
# Teleport actions
# ---------------------------------------------------------------------------
def _teleportToTarget(plugin: UtilityStone, player, target) -> None:
    if not _requirePermission(plugin, player, PERM_HOMES_TELEPORT, "teleport to a player"):
        return

    plugin.teleports.queueTeleport(player, target.location, f"{target.name}")
    _audit(plugin, player, "teleported to", target.name)
    plugin.gui.untrack(player)


def _teleportTargetToMe(plugin: UtilityStone, player, target) -> None:
    if not _requirePermission(plugin, player, PERM_HOMES_TELEPORT, "teleport a player"):
        return

    target.teleport(player.location)
    plugin.messages.success(player, f"Teleported {target.name} to you.")
    _audit(plugin, player, "teleported", target.name)
    plugin.gui.untrack(player)


# ---------------------------------------------------------------------------
# Admin Homes View (Feature 2)
# ---------------------------------------------------------------------------
def _openAdminHomesForPlayer(plugin: UtilityStone, player, target) -> None:
    fm = plugin.gui

    if not _requirePermission(plugin, player, PERM_HOMES_VIEW, "view player homes"):
        return

    _audit(plugin, player, "viewed homes of", target.name)

    form = buildActionMenu(f"Homes: {target.name}", "Saved homes")

    homesData = plugin.homes.homesOf(target)
    owned = sorted(homesData.keys()) if homesData else []

    if not owned:
        addLabel(form, f"{target.name} has no homes.")
    else:
        addLabel(form, f"{len(owned)} homes")

        for homeName in owned:
            addHeader(form, homeName)

            payload = homesData[homeName]
            from endstone_utilitystone.util.locations import decodeLocation
            location = decodeLocation(plugin.server, payload)

            if location is not None:
                addLabel(form, f"Dimension: {location.dimension.name}")
                addLabel(form, f"X: {location.block_x}, Y: {location.block_y}, Z: {location.block_z}")
            else:
                addLabel(form, "Location unavailable")

            if hasPermission(player, PERM_HOMES_TELEPORT):
                targetCopy = target
                addButton(
                    form,
                    f"Teleport To {homeName}",
                    on_click=fm.wrapClick(player, lambda p=player, t=targetCopy, h=homeName, d=homesData: _teleportToHome(plugin, p, t, h, d), f"tp_home:{target.name}:{homeName}"),
                )

            if hasPermission(player, PERM_HOMES_DELETE):
                targetCopy2 = target
                addButton(
                    form,
                    f"Delete {homeName}",
                    on_click=fm.wrapClick(player, lambda p=player, t=targetCopy2, h=homeName: _confirmDeleteAdminHome(plugin, p, t, h), f"del_home:{target.name}:{homeName}"),
                )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openPlayerInspector(plugin, player, target), "back"))
    fm.sendForm(player, form, label=f"admin_homes:{target.name}")


def _teleportToHome(plugin: UtilityStone, player, target, homeName: str, homesData: dict) -> None:
    if not _requirePermission(plugin, player, PERM_HOMES_TELEPORT, "teleport to a home"):
        return

    payload = homesData.get(homeName)
    if payload is None:
        plugin.messages.failure(player, f"Home '{homeName}' not found.")
        return

    from endstone_utilitystone.util.locations import decodeLocation
    location = decodeLocation(plugin.server, payload)
    if location is None:
        plugin.messages.failure(player, f"Cannot resolve location for home '{homeName}'.")
        return

    plugin.teleports.queueTeleport(player, location, f"{target.name}'s home {homeName}")
    _audit(plugin, player, f"teleported to home {homeName} belonging to", target.name)
    plugin.gui.untrack(plugin.gui)


def _confirmDeleteAdminHome(plugin: UtilityStone, player, target, homeName: str) -> None:
    if not _requirePermission(plugin, player, PERM_HOMES_DELETE, "delete a home"):
        return

    from endstone_utilitystone.ui.dialogs import askConfirmation

    def _doDelete(p):
        if plugin.homes.deleteHome(target, homeName):
            plugin.messages.success(player, f"Deleted home '{homeName}' from {target.name}.")
            _audit(plugin, player, f"deleted home {homeName} of", target.name)
        else:
            plugin.messages.failure(player, f"Failed to delete home '{homeName}'.")
        plugin.gui.untrack(player)

    askConfirmation(plugin, player, "Delete Home", f"Delete '{homeName}' from {target.name}?", onYes=_doDelete)


# ---------------------------------------------------------------------------
# Inventory View (Feature 3)
# ---------------------------------------------------------------------------
def _openInventoryView(plugin: UtilityStone, player, target, page: int = 0) -> None:
    fm = plugin.gui

    if not _requirePermission(plugin, player, PERM_INVENTORY_VIEW, "view inventories"):
        return

    _audit(plugin, player, "viewed inventory of", target.name)

    inventory = target.inventory
    invSize = len(inventory)
    totalPages = max(1, (invSize + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, totalPages - 1))

    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, invSize)

    form = buildActionMenu(
        f"Inventory: {target.name}",
        f"Page {page + 1}/{totalPages}  (slots {start + 1}-{end} of {invSize})",
    )

    for slot in range(start, end):
        try:
            item = inventory[slot]
        except Exception:
            item = None

        if item is None:
            addLabel(form, f"Slot {slot + 1}: Empty")
        else:
            itemName = _getItemDisplayName(item)
            amount = item.amount
            if amount > 1:
                addLabel(form, f"Slot {slot + 1}: {itemName} x{amount}")
            else:
                addLabel(form, f"Slot {slot + 1}: {itemName}")

    if page > 0:
        targetCopy = target
        addButton(
            form,
            "Previous Page",
            on_click=fm.wrapClick(player, lambda p=player, t=targetCopy, pg=page - 1: _openInventoryView(plugin, p, t, pg), f"inv_prev:{target.name}:{page}"),
        )

    if page < totalPages - 1:
        targetCopy2 = target
        addButton(
            form,
            "Next Page",
            on_click=fm.wrapClick(player, lambda p=player, t=targetCopy2, pg=page + 1: _openInventoryView(plugin, p, t, pg), f"inv_next:{target.name}:{page}"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openPlayerInspector(plugin, player, target), "back"))
    fm.sendForm(player, form, label=f"inventory:{target.name}:{page}")


# ---------------------------------------------------------------------------
# Ender Chest View (Feature 4)
# ---------------------------------------------------------------------------
def _openEnderChestView(plugin: UtilityStone, player, target, page: int = 0) -> None:
    fm = plugin.gui

    if not _requirePermission(plugin, player, PERM_ENDERCHEST_VIEW, "view ender chests"):
        return

    _audit(plugin, player, "viewed Ender Chest of", target.name)

    enderChest = target.ender_chest
    invSize = len(enderChest)
    totalPages = max(1, (invSize + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, totalPages - 1))

    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, invSize)

    form = buildActionMenu(
        f"Ender Chest: {target.name}",
        f"Page {page + 1}/{totalPages}  (slots {start + 1}-{end} of {invSize})",
    )

    for slot in range(start, end):
        try:
            item = enderChest[slot]
        except Exception:
            item = None

        if item is None:
            addLabel(form, f"Slot {slot + 1}: Empty")
        else:
            itemName = _getItemDisplayName(item)
            amount = item.amount
            if amount > 1:
                addLabel(form, f"Slot {slot + 1}: {itemName} x{amount}")
            else:
                addLabel(form, f"Slot {slot + 1}: {itemName}")

    if page > 0:
        targetCopy = target
        addButton(
            form,
            "Previous Page",
            on_click=fm.wrapClick(player, lambda p=player, t=targetCopy, pg=page - 1: _openEnderChestView(plugin, p, t, pg), f"ender_prev:{target.name}:{page}"),
        )

    if page < totalPages - 1:
        targetCopy2 = target
        addButton(
            form,
            "Next Page",
            on_click=fm.wrapClick(player, lambda p=player, t=targetCopy2, pg=page + 1: _openEnderChestView(plugin, p, t, pg), f"ender_next:{target.name}:{page}"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openPlayerInspector(plugin, player, target), "back"))
    fm.sendForm(player, form, label=f"enderchest:{target.name}:{page}")


# ---------------------------------------------------------------------------
# Item display helper
# ---------------------------------------------------------------------------
def _getItemDisplayName(item) -> str:
    """Return a human-readable name for an ItemStack."""
    try:
        meta = item.item_meta
        if meta is not None and meta.display_name:
            return meta.display_name
    except Exception:
        pass

    try:
        itemType = item.type
        translationKey = itemType.translation_key
        if translationKey:
            clean = translationKey.replace("item.", "").replace("minecraft:", "").replace(".", " ").replace("_", " ")
            return clean.title()
    except Exception:
        pass

    try:
        return str(item.type)
    except Exception:
        return "Unknown Item"


# ---------------------------------------------------------------------------
# Player action helpers
# ---------------------------------------------------------------------------
def _healPlayer(plugin: UtilityStone, player, target) -> None:
    from endstone_utilitystone.util.player_actions import healPlayer
    healPlayer(plugin, target, player)
    plugin.gui.untrack(player)


def _feedPlayer(plugin: UtilityStone, player, target) -> None:
    from endstone_utilitystone.util.player_actions import feedPlayer
    feedPlayer(plugin, target, player)
    plugin.gui.untrack(player)


def _toggleFly(plugin: UtilityStone, player, target) -> None:
    from endstone_utilitystone.util.player_actions import toggleFlight
    toggleFlight(plugin, target, player)
    plugin.gui.untrack(player)


def _toggleGod(plugin: UtilityStone, player, target) -> None:
    from endstone_utilitystone.util.player_actions import toggleGod
    toggleGod(plugin, target, player)
    plugin.gui.untrack(player)


def _mutePlayer(plugin: UtilityStone, player, target, seconds: float) -> None:
    from endstone_utilitystone.util.durations import formatDuration

    plugin.punishments.applyMute(str(target.unique_id), target.name, seconds, "Muted via admin GUI", player.name)
    window = formatDuration(seconds)
    plugin.messages.success(player, f"Muted {target.name} for {window}.")
    plugin.messages.failure(target, f"You have been muted for {window}.")
    _audit(plugin, player, f"muted {target.name} for {window}", target.name)
    plugin.gui.untrack(player)


def _unmutePlayer(plugin: UtilityStone, player, target) -> None:
    if plugin.punishments.liftMute(str(target.unique_id)):
        plugin.messages.success(player, f"Unmuted {target.name}.")
        plugin.messages.success(target, "You can chat again.")
        _audit(plugin, player, "unmuted", target.name)
    else:
        plugin.messages.failure(player, f"{target.name} is not muted.")
    plugin.gui.untrack(player)


# ---------------------------------------------------------------------------
# Change Rank (for Player Inspector)
# ---------------------------------------------------------------------------
def _openChangeRank(plugin: UtilityStone, player, target) -> None:
    fm = plugin.gui

    if plugin.ranks is None:
        plugin.messages.failure(player, "Rank system is not available.")
        return

    form = buildActionMenu(f"Change Rank: {target.name}", "Select a rank")

    current_rank = plugin.ranks.getPlayerRank(str(target.unique_id))
    ranks = plugin.ranks.listRanks()

    addLabel(form, f"Current rank: {current_rank or '(default)'}")

    for rank_name in ranks:
        definition = plugin.ranks.getRankDefinition(rank_name)
        priority = definition.get("priority", 0) if definition else 0
        prefix = definition.get("prefix", "") if definition else ""
        display = f"{rank_name} (pri: {priority})"
        if prefix:
            display += f"  {prefix}"

        is_current = rank_name == (current_rank or "default")
        marker = " > " if is_current else "   "

        addButton(
            form,
            f"{marker}{display}",
            on_click=fm.wrapClick(player, lambda p=player, t=target, r=rank_name: _setPlayerRank(plugin, p, t, r), f"set_rank:{target.name}:{rank_name}"),
        )

    # Remove rank option
    addDivider(form)
    addButton(
        form,
        "Remove Rank (revert to default)",
        on_click=fm.wrapClick(player, lambda p=player, t=target: _removePlayerRank(plugin, p, t), f"remove_rank:{target.name}"),
    )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openPlayerInspector(plugin, player, target), "back"))
    fm.sendForm(player, form, label=f"change_rank:{target.name}")


def _setPlayerRank(plugin: UtilityStone, player, target, rank_name: str) -> None:
    ok, msg = plugin.ranks.setPlayerRank(str(target.unique_id), rank_name)
    if ok:
        plugin.messages.success(player, f"Set {target.name}'s rank to '{rank_name}'.")
        _audit(plugin, player, f"set rank to {rank_name} for", target.name)
    else:
        plugin.messages.failure(player, msg)
    plugin.gui.untrack(player)


def _removePlayerRank(plugin: UtilityStone, player, target) -> None:
    ok, msg = plugin.ranks.removePlayerRank(str(target.unique_id))
    if ok:
        plugin.messages.success(player, f"Removed {target.name}'s rank.")
        _audit(plugin, player, "removed rank of", target.name)
    else:
        plugin.messages.failure(player, msg)
    plugin.gui.untrack(player)


def _openDailyRewards(plugin: UtilityStone, player, target) -> None:
    from endstone_utilitystone.ui.daily_rewards import openPlayerDailyRewardDetail
    openPlayerDailyRewardDetail(plugin, player, target)
