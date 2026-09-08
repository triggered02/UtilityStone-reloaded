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
    stylePlayerMenu,
)
from endstone_utilitystone.ui.permissions import hasAdminGui, hasPermission

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


def openPlayerMenu(plugin: UtilityStone, player) -> bool:
    fm = plugin.gui

    def _build():
        form = stylePlayerMenu("Server Menu", "Server navigation & utilities")

        hasHomesAccess = hasPermission(player, "utilitystone.command.homes")
        hasWarpsAccess = hasPermission(player, "utilitystone.command.warp")
        hasSpawnAccess = hasPermission(player, "utilitystone.command.spawn")
        hasTpaAccess = hasPermission(player, "utilitystone.command.tpa")
        hasKitAccess = hasPermission(player, "utilitystone.command.kit")
        hasAfkAccess = hasPermission(player, "utilitystone.command.afk")
        hasDailyRewardAccess = hasPermission(player, "utilitystone.command.dailyreward")

        hasAnyTravel = hasHomesAccess or hasSpawnAccess

        if hasAnyTravel:
            addButton(
                form,
                "Travel",
                icon="textures/icons/LandClaims",
                on_click=fm.wrapClick(
                    player,
                    lambda: _openTravel(plugin, player),
                    "section:travel",
                ),
            )

        if hasWarpsAccess:
            if hasAnyTravel:
                addDivider(form)
            addButton(
                form,
                "Warps",
                icon="textures/icons/TPA_Globe",
                on_click=fm.wrapClick(
                    player,
                    lambda: _openWarps(plugin, player),
                    "section:warps",
                ),
            )

        hasAnyUtility = hasKitAccess or hasAfkAccess or hasDailyRewardAccess or hasTpaAccess or True
        if hasAnyUtility:
            if hasAnyTravel or hasWarpsAccess:
                addDivider(form)
            addButton(
                form,
                "Utilities",
                icon="textures/icons/crate_icon",
                on_click=fm.wrapClick(
                    player,
                    lambda: _openUtilities(plugin, player),
                    "section:utilities",
                ),
            )

        if not hasAnyTravel and not hasWarpsAccess and not hasAnyUtility:
            addLabel(form, "No features available.")

        if hasAdminGui(player):
            addDivider(form)
            addButton(
                form,
                "Admin Panel",
                icon="textures/icons/admin",
                on_click=fm.wrapClick(
                    player,
                    lambda: fm.navigator.openAdminPanel(player),
                    "admin",
                ),
            )

        addDivider(form)
        addButton(
            form,
            "Back",
            icon="textures/icons/Arrow_Left_Curved",
            on_click=fm.wrapClick(
                player,
                lambda: player.close_form(),
                "player_menu:back",
            ),
        )

        return form

    return fm.sendForm(player, _build(), label="player_menu")


# ---------------------------------------------------------------------------
# Section submenu openers
# ---------------------------------------------------------------------------
# Each section opener builds a submenu that contains ONLY items from that
# section. They reuse the existing _open* callbacks for the items themselves
# (Homes, Warps, etc.) so the underlying business logic is not duplicated.
# Only the section-level wrapper is new.

def _openTravel(plugin: UtilityStone, player) -> None:
    """Open the Travel submenu: only Homes / Warps / Spawn, gated by perms."""
    fm = plugin.gui

    hasHomesAccess = hasPermission(player, "utilitystone.command.homes")
    hasWarpsAccess = hasPermission(player, "utilitystone.command.warp")
    hasSpawnAccess = hasPermission(player, "utilitystone.command.spawn")

    if not (hasHomesAccess or hasWarpsAccess or hasSpawnAccess):
        return  # nothing to show; main menu shouldn't have offered this

    form = buildActionMenu("Travel", "Homes, warps, and spawn")

    if hasHomesAccess:
        addButton(
            form,
            "Homes",
            icon="textures/icons/Homes_Bed",
            on_click=fm.wrapClick(player, lambda: _openHomes(plugin, player), "travel:homes"),
        )
    if hasWarpsAccess:
        addButton(
            form,
            "Warps",
            icon="textures/icons/LandClaims",
            on_click=fm.wrapClick(player, lambda: _openWarps(plugin, player), "travel:warps"),
        )
    if hasSpawnAccess:
        addButton(
            form,
            "Spawn",
            icon="textures/icons/UpArrow",
            on_click=fm.wrapClick(player, lambda: player.perform_command("spawn"), "travel:spawn"),
        )

    addDivider(form)
    addButton(
        form,
        "Back",
        icon="textures/icons/Arrow_Left_Curved",
        on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "travel:back"),
    )

    fm.sendForm(player, form, label="travel")


def _openUtilities(plugin: UtilityStone, player) -> None:
    """Open the Utilities submenu: Kits / Daily Reward / Player Info / Homes / Teleport / AFK."""
    fm = plugin.gui

    hasKitAccess = hasPermission(player, "utilitystone.command.kit")
    hasAfkAccess = hasPermission(player, "utilitystone.command.afk")
    hasDailyRewardAccess = hasPermission(player, "utilitystone.command.dailyreward")
    hasHomesAccess = hasPermission(player, "utilitystone.command.homes")
    hasTpaAccess = hasPermission(player, "utilitystone.command.tpa")

    form = buildActionMenu("Utilities", "Kits, info, and tools")

    if hasKitAccess:
        addButton(
            form,
            "Kits",
            icon="textures/icons/crate_icon",
            on_click=fm.wrapClick(player, lambda: _openKits(plugin, player), "utilities:kits"),
        )
    if hasDailyRewardAccess:
        addButton(
            form,
            "Daily Reward",
            icon="textures/icons/loot",
            on_click=fm.wrapClick(player, lambda: _openDailyReward(plugin, player), "utilities:dailyreward"),
        )
    addButton(
        form,
        "Player Info",
        icon="textures/icons/Stats_Icon",
        on_click=fm.wrapClick(player, lambda: _openPlayerInfo(plugin, player), "utilities:playerinfo"),
    )
    if hasHomesAccess:
        addButton(
            form,
            "Homes",
            icon="textures/icons/Homes_Bed",
            on_click=fm.wrapClick(player, lambda: _openHomes(plugin, player), "utilities:homes"),
        )
    if hasTpaAccess:
        addButton(
            form,
            "Teleport",
            icon="textures/icons/TPA_Globe",
            on_click=fm.wrapClick(player, lambda: _openTeleport(plugin, player), "utilities:teleport"),
        )
    if hasAfkAccess:
        addButton(
            form,
            "AFK",
            icon="textures/icons/AFK",
            on_click=fm.wrapClick(player, lambda: player.perform_command("afk"), "utilities:afk"),
        )

    addDivider(form)
    addButton(
        form,
        "Back",
        icon="textures/icons/Arrow_Left_Curved",
        on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "utilities:back"),
    )

    fm.sendForm(player, form, label="utilities")


def _openHomes(plugin: UtilityStone, player) -> None:
    fm = plugin.gui
    homes = plugin.homes

    form = buildActionMenu("Your Homes")

    owned = homes.nameList(player)
    limit = homes.limitFor(player)
    allowance = "unlimited" if limit is None else str(limit)

    addLabel(form, f"Using {len(owned)} of {allowance} homes")

    if not owned:
        addButton(
            form,
            "Create Home",
            icon="textures/icons/Homes_Bed",
            on_click=fm.wrapClick(player, lambda: _createHome(plugin, player), "create_home"),
        )
        addButton(
            form,
            "Back",
            icon="textures/icons/Arrow_Left_Curved",
            on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"),
        )
        fm.sendForm(player, form, label="homes_list")
        return

    for name in owned:
        addButton(
            form,
            name,
            icon="textures/icons/Homes_Bed",
            on_click=fm.wrapClick(player, lambda p=player, n=name: _goHome(plugin, p, n), f"go_home:{name}"),
        )

    addDivider(form)
    if limit is None or len(owned) < limit:
        addButton(
            form,
            "Create Home",
            icon="textures/icons/Homes_Bed",
            on_click=fm.wrapClick(player, lambda: _createHome(plugin, player), "create_home"),
        )

    for name in owned:
        targetName = name
        addButton(
            form,
            f"Delete {name}",
            icon="textures/icons/Homes_Bed",
            on_click=fm.wrapClick(player, lambda p=player, n=targetName: _confirmDeleteHome(plugin, p, n), f"del_home:{name}"),
        )

    addButton(
        form,
        "Back",
        icon="textures/icons/Arrow_Left_Curved",
        on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"),
    )
    fm.sendForm(player, form, label="homes_list")


def _goHome(plugin: UtilityStone, player, name: str) -> None:
    destination = plugin.homes.resolve(player, name)
    if destination is None:
        plugin.messages.failure(player, f"No home called {name}.")
        return
    plugin.teleports.queueTeleport(player, destination, f"your home {name}")


def _createHome(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.dialogs import askTextInput

    askTextInput(
        plugin,
        player,
        title="Create Home",
        label="Home name",
        placeholder="e.g. base, farm, nether",
        current="home",
        onSubmit=lambda name: _doCreateHome(plugin, player, name),
    )


def _doCreateHome(plugin: UtilityStone, player, name: str) -> None:
    name = name.strip()
    if not name:
        plugin.messages.failure(player, "Home name cannot be empty.")
        return

    result = plugin.homes.setHome(player, name)
    if result == "invalid":
        plugin.messages.failure(player, "Home names may only use letters, numbers, dashes and underscores.")
    elif result == "limit":
        limit = plugin.homes.limitFor(player)
        plugin.messages.failure(player, f"You have reached your limit of {limit} homes.")
    else:
        plugin.messages.success(player, f"Saved home {name.lower()}.")
        plugin.gui.untrack(player)


def _confirmDeleteHome(plugin: UtilityStone, player, name: str) -> None:
    from endstone_utilitystone.ui.dialogs import askConfirmation

    askConfirmation(
        plugin,
        player,
        "Delete Home",
        f"Are you sure you want to delete home '{name}'?",
        onYes=lambda p: _doDeleteHome(plugin, player, name),
    )


def _doDeleteHome(plugin: UtilityStone, player, name: str) -> None:
    if plugin.homes.deleteHome(player, name):
        plugin.messages.success(player, f"Deleted home {name}.")
    else:
        plugin.messages.failure(player, f"You do not have a home called {name}.")
    plugin.gui.untrack(player)


def _openWarps(plugin: UtilityStone, player) -> None:
    fm = plugin.gui
    warps = plugin.warps

    form = buildActionMenu("Warps")

    visible = warps.visibleTo(player)
    if not visible:
        addLabel(form, "No warps are available to you.")
        addButton(
            form,
            "Back",
            icon="textures/icons/Arrow_Left_Curved",
            on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"),
        )
        fm.sendForm(player, form, label="warps_list")
        return

    addLabel(form, f"{len(visible)} warps available")

    for name in visible:
        addButton(
            form,
            name,
            icon="textures/icons/LandClaims",
            on_click=fm.wrapClick(player, lambda p=player, n=name: _goWarp(plugin, p, n), f"go_warp:{name}"),
        )

    addButton(
        form,
        "Back",
        icon="textures/icons/Arrow_Left_Curved",
        on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"),
    )
    fm.sendForm(player, form, label="warps_list")


def _goWarp(plugin: UtilityStone, player, name: str) -> None:
    destination = plugin.warps.resolve(name)
    if destination is None:
        plugin.messages.failure(player, f"There is no warp called {name}.")
        return
    plugin.teleports.queueTeleport(player, destination, f"warp {name}")


def _openTeleport(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    form = buildActionMenu("Teleport")

    incoming = plugin.teleports.incomingFor(player)
    if incoming:
        addHeader(form, "Incoming Requests")
        for entry in incoming:
            requesterName = entry.requester.name
            addButton(
                form,
                f"Accept {requesterName}",
                on_click=fm.wrapClick(player, lambda p=player, r=entry.requester: _acceptRequest(plugin, p, r), f"tpa_accept:{requesterName}"),
            )
            addButton(
                form,
                f"Deny {requesterName}",
                on_click=fm.wrapClick(player, lambda p=player, r=entry.requester: _denyRequest(plugin, p, r), f"tpa_deny:{requesterName}"),
            )
        addDivider(form)

    addHeader(form, "Send Request")
    online = [p for p in plugin.server.online_players if p.unique_id != player.unique_id]
    if not online:
        addLabel(form, "No other players online.")
    else:
        for other in online[:20]:
            otherName = other.name
            addButton(
                form,
                f"TPA to {otherName}",
                on_click=fm.wrapClick(player, lambda p=player, t=other: _sendTpa(plugin, p, t, False), f"tpa:{otherName}"),
            )
            addButton(
                form,
                f"TPAHERE {otherName}",
                on_click=fm.wrapClick(player, lambda p=player, t=other: _sendTpa(plugin, p, t, True), f"tpahere:{otherName}"),
            )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"))
    fm.sendForm(player, form, label="teleport_menu")


def _sendTpa(plugin: UtilityStone, player, target, hereMode: bool) -> None:
    outcome = plugin.teleports.request(player, target, hereMode)
    if outcome == "self":
        plugin.messages.failure(player, "You cannot send a request to yourself.")
    elif outcome == "duplicate":
        plugin.messages.warn(player, f"{target.name} already has a pending request from you.")
    else:
        mode = "to teleport to you" if hereMode else "to teleport to them"
        plugin.messages.success(player, f"Request sent to {target.name}.")
        plugin.messages.notice(target, f"{player.name} would like {mode}.")


def _acceptRequest(plugin: UtilityStone, player, requester) -> None:
    entry = plugin.teleports.takeRequest(player, requester)
    if entry is None:
        plugin.messages.failure(player, "That request is no longer valid.")
        return
    if entry.hereMode:
        plugin.teleports.queueTeleport(player, entry.requester.location, entry.requester.name)
        plugin.messages.notice(entry.requester, f"{player.name} accepted your request.")
    else:
        plugin.teleports.queueTeleport(entry.requester, player.location, player.name)
        plugin.messages.success(player, f"Accepted the request from {entry.requester.name}.")


def _denyRequest(plugin: UtilityStone, player, requester) -> None:
    entry = plugin.teleports.takeRequest(player, requester)
    if entry is None:
        plugin.messages.failure(player, "That request is no longer valid.")
        return
    plugin.messages.success(player, f"Turned down the request from {entry.requester.name}.")
    plugin.messages.warn(entry.requester, f"{player.name} turned down your teleport request.")


def _openKits(plugin: UtilityStone, player) -> None:
    fm = plugin.gui
    kits = plugin.kits

    form = buildActionMenu("Kits")

    available = kits.availableTo(player)
    if not available:
        addLabel(form, "There are no kits available to you.")
        addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"))
        fm.sendForm(player, form, label="kits_list")
        return

    addLabel(form, f"{len(available)} kits available")

    for name in available:
        definition = plugin.settings.kitDefinition(name)
        if definition is None:
            continue
        cooldown = kits.cooldownRemaining(player, name, definition)
        suffix = "" if cooldown <= 0 else " (on cooldown)"
        addButton(
            form,
            f"{name}{suffix}",
            on_click=fm.wrapClick(player, lambda p=player, n=name, d=definition: _claimKit(plugin, p, n, d), f"kit:{name}"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"))
    fm.sendForm(player, form, label="kits_list")


def _claimKit(plugin: UtilityStone, player, name: str, definition: dict) -> None:
    from endstone_utilitystone.util.durations import formatDuration

    kits = plugin.kits

    if not kits.canUse(player, name, definition):
        plugin.messages.failure(player, f"You do not have access to the {name} kit.")
        return

    waiting = kits.cooldownRemaining(player, name, definition)
    if waiting > 0.0:
        plugin.messages.failure(player, f"You can claim the {name} kit again in {formatDuration(waiting)}.")
        return

    granted, count, rejected = kits.grant(player, name, definition)
    if not granted:
        plugin.messages.failure(player, f"The {name} kit is not set up correctly. Tell an admin.")
        return

    kits.markUsed(player, name)
    plugin.messages.success(player, f"You claimed the {name} kit ({count} stacks).")
    plugin.gui.untrack(player)


def _openPlayerInfo(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    from endstone_utilitystone.util.durations import formatDuration, formatTimestamp
    from endstone_utilitystone.util.locations import describeLocation

    session = plugin.sessions.of(player)
    profile = plugin.profiles.profileFor(player)
    mute = plugin.punishments.muteFor(str(player.unique_id))

    form = buildActionMenu(f"{player.name}", "Player information")

    addLabel(form, f"Health: {player.health}/{player.max_health}")
    addLabel(form, f"Location: {describeLocation(player.location)}")
    addLabel(form, f"Game mode: {player.game_mode.name.title()}")
    addLabel(form, f"Ping: {player.ping}ms")

    total = plugin.profiles.playtimeOf(str(player.unique_id), session)
    addLabel(form, f"Playtime: {formatDuration(total, 3)}")

    addLabel(form, f"First seen: {formatTimestamp(float(profile.get('firstSeen', 0.0)))}")
    addLabel(form, f"Last seen: {formatTimestamp(float(profile.get('lastSeen', 0.0)))}")

    if session is not None and session.isAfk:
        reason = f" ({session.afkReason})" if session.afkReason else ""
        addLabel(form, f"Status: AFK for {formatDuration(time.time() - session.afkSince)}{reason}")

    if mute is not None:
        remaining = plugin.punishments.remainingMute(mute)
        addLabel(form, f"Muted for {formatDuration(remaining)} ({mute.get('reason', '')})")

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openPlayerMenu(plugin, player), "back"))
    fm.sendForm(player, form, label="player_info")


def _openDailyReward(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.daily_rewards import openDailyReward
    openDailyReward(plugin, player)
