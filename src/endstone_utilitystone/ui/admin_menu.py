from __future__ import annotations

import time
from typing import TYPE_CHECKING

from endstone_utilitystone.ui.components import (
    addDivider,
    addHeader,
    addLabel,
    addButton,
    buildActionMenu,
)
from endstone_utilitystone.ui.permissions import hasAdminGui

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


def openAdminPanel(plugin: UtilityStone, player) -> bool:
    fm = plugin.gui

    if not hasAdminGui(player):
        plugin.messages.failure(player, "You do not have permission to access the admin panel.")
        return False

    form = buildActionMenu("Admin Panel", "Server administration")

    addButton(form, "Player Management", on_click=fm.wrapClick(player, lambda: _openPlayerManagement(plugin, player), "admin_players"))
    addButton(form, "Homes", on_click=fm.wrapClick(player, lambda: _openAdminHomes(plugin, player), "admin_homes"))
    addButton(form, "Warps", on_click=fm.wrapClick(player, lambda: _openAdminWarps(plugin, player), "admin_warps"))
    addButton(form, "Spawn", on_click=fm.wrapClick(player, lambda: _openAdminSpawn(plugin, player), "admin_spawn"))
    addButton(form, "Kits", on_click=fm.wrapClick(player, lambda: _openAdminKits(plugin, player), "admin_kits"))
    addButton(form, "Safe Areas", on_click=fm.wrapClick(player, lambda: _openSafeAreas(plugin, player), "admin_safeareas"))
    addButton(form, "Ranks", on_click=fm.wrapClick(player, lambda: _openRanks(plugin, player), "admin_ranks"))

    addDivider(form)
    addHeader(form, "Server Tools")
    addButton(form, "Plugin Info", on_click=fm.wrapClick(player, lambda: _openPluginInfo(plugin, player), "admin_info"))
    addButton(form, "Reload Config", on_click=fm.wrapClick(player, lambda: _confirmReload(plugin, player), "admin_reload"))

    addDivider(form)
    addButton(form, "Configuration", on_click=fm.wrapClick(player, lambda: fm.navigator.openConfigEditor(player), "admin_config"))

    addButton(form, "Back to Menu", on_click=fm.wrapClick(player, lambda: fm.navigator.openPlayerMenu(player), "back"))

    return fm.sendForm(player, form, label="admin_panel")


def _openPlayerManagement(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.admin_player_tools import openPlayerList
    openPlayerList(plugin, player)


def _openPlayerDetail(plugin: UtilityStone, player, target) -> None:
    fm = plugin.gui

    from endstone_utilitystone.util.durations import formatDuration, formatTimestamp
    from endstone_utilitystone.util.locations import describeLocation

    form = buildActionMenu(f"{target.name}", "Player management")

    session = plugin.sessions.of(target)
    mute = plugin.punishments.muteFor(str(target.unique_id))

    addLabel(form, f"Health: {target.health}/{target.max_health}")
    addLabel(form, f"Location: {describeLocation(target.location)}")
    addLabel(form, f"Device: {target.device_os} on {target.game_version}")

    total = plugin.profiles.playtimeOf(str(target.unique_id), session)
    addLabel(form, f"Playtime: {formatDuration(total, 3)}")

    if session and session.isAfk:
        addLabel(form, f"Status: AFK for {formatDuration(time.time() - session.afkSince)}")

    if mute:
        remaining = plugin.punishments.remainingMute(mute)
        addLabel(form, f"Muted: {formatDuration(remaining)} left")
        addButton(
            form,
            "Unmute",
            on_click=fm.wrapClick(player, lambda p=player, t=target: _unmutePlayer(plugin, p, t), f"unmute:{target.name}"),
        )
    else:
        addButton(
            form,
            "Mute (30m)",
            on_click=fm.wrapClick(player, lambda p=player, t=target: _mutePlayer(plugin, p, t, 1800), f"mute30:{target.name}"),
        )
        addButton(
            form,
            "Mute (1h)",
            on_click=fm.wrapClick(player, lambda p=player, t=target: _mutePlayer(plugin, p, t, 3600), f"mute1h:{target.name}"),
        )
        addButton(
            form,
            "Mute (24h)",
            on_click=fm.wrapClick(player, lambda p=player, t=target: _mutePlayer(plugin, p, t, 86400), f"mute24h:{target.name}"),
        )

    addDivider(form)
    addButton(form, "Heal", on_click=fm.wrapClick(player, lambda p=player, t=target: _healPlayer(plugin, p, t), f"heal:{target.name}"))
    addButton(form, "Feed", on_click=fm.wrapClick(player, lambda p=player, t=target: _feedPlayer(plugin, p, t), f"feed:{target.name}"))

    flyState = "Disable Fly" if target.allow_flight else "Enable Fly"
    addButton(form, flyState, on_click=fm.wrapClick(player, lambda p=player, t=target: _toggleFly(plugin, p, t), f"fly:{target.name}"))

    godState = "Disable God" if target.unique_id in plugin.godPlayers else "Enable God"
    addButton(form, godState, on_click=fm.wrapClick(player, lambda p=player, t=target: _toggleGod(plugin, p, t), f"god:{target.name}"))

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openPlayerManagement(plugin, player), "back"))
    fm.sendForm(player, form, label=f"admin_player:{target.name}")


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
    plugin.gui.untrack(player)


def _unmutePlayer(plugin: UtilityStone, player, target) -> None:
    if plugin.punishments.liftMute(str(target.unique_id)):
        plugin.messages.success(player, f"Unmuted {target.name}.")
        plugin.messages.success(target, "You can chat again.")
    else:
        plugin.messages.failure(player, f"{target.name} is not muted.")
    plugin.gui.untrack(player)


def _openAdminHomes(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    form = buildActionMenu("Manage Homes")
    addLabel(form, "Player homes are managed by each player.")
    addLabel(form, "Use the Player Management section to assist specific players.")

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openAdminPanel(plugin, player), "back"))
    fm.sendForm(player, form, label="admin_homes")


def _openAdminWarps(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    form = buildActionMenu("Manage Warps")

    warps = plugin.warps
    names = warps.nameList()

    if not names:
        addLabel(form, "No warps have been created yet.")
        addLabel(form, "Use /setwarp while standing at the location.")
    else:
        addLabel(form, f"{len(names)} warps active")
        for name in names:
            addButton(
                form,
                f"Delete {name}",
                on_click=fm.wrapClick(player, lambda p=player, n=name: _confirmDeleteWarp(plugin, p, n), f"del_warp:{name}"),
            )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openAdminPanel(plugin, player), "back"))
    fm.sendForm(player, form, label="admin_warps")


def _confirmDeleteWarp(plugin: UtilityStone, player, name: str) -> None:
    from endstone_utilitystone.ui.dialogs import askConfirmation

    def _doDelete(p):
        if plugin.warps.deleteWarp(name):
            plugin.messages.success(player, f"Deleted warp {name}.")
        else:
            plugin.messages.failure(player, f"There is no warp called {name}.")
        plugin.gui.untrack(player)

    askConfirmation(plugin, player, "Delete Warp", f"Delete warp '{name}'?", onYes=_doDelete)


def _openAdminSpawn(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    form = buildActionMenu("Spawn Management")

    if plugin.spawns.hasSpawn():
        from endstone_utilitystone.util.locations import describeLocation
        location = plugin.spawns.resolve()
        if location:
            addLabel(form, f"Current spawn: {describeLocation(location)}")
        addButton(form, "Set Spawn Here", on_click=fm.wrapClick(player, lambda: _setSpawn(plugin, player), "setspawn"))
    else:
        addLabel(form, "No spawn point has been set.")
        addButton(form, "Set Spawn Here", on_click=fm.wrapClick(player, lambda: _setSpawn(plugin, player), "setspawn"))

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openAdminPanel(plugin, player), "back"))
    fm.sendForm(player, form, label="admin_spawn")


def _setSpawn(plugin: UtilityStone, player) -> None:
    plugin.spawns.setSpawn(player.location, player.name)
    from endstone_utilitystone.util.locations import describeLocation
    plugin.messages.success(player, f"Spawn point set to {describeLocation(player.location)}.")
    plugin.gui.untrack(player)


def _openAdminKits(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    form = buildActionMenu("Kit Management")

    kitNames = plugin.settings.kitNames()
    if not kitNames:
        addLabel(form, "No kits are defined in the config.")
        addLabel(form, "Edit config.toml to add kits.")
    else:
        addLabel(form, f"{len(kitNames)} kits defined")
        addLabel(form, "Kits are configured via config.toml")
        for name in kitNames:
            definition = plugin.settings.kitDefinition(name)
            cooldown = plugin.settings.kitCooldownSeconds(definition) if definition else 0
            from endstone_utilitystone.util.durations import formatDuration
            cooldownStr = formatDuration(cooldown) if cooldown > 0 else "none"
            perm = definition.get("permission") if definition else None
            permStr = f" (requires: {perm})" if perm else ""
            addLabel(form, f"  {name} - cooldown: {cooldownStr}{permStr}")

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openAdminPanel(plugin, player), "back"))
    fm.sendForm(player, form, label="admin_kits")


def _openPluginInfo(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    form = buildActionMenu("Plugin Info")

    teleports = plugin.teleports

    addLabel(form, f"Version: {plugin.pluginVersion}")
    addLabel(form, f"Commands: {plugin.router.count}")
    addLabel(form, f"Tracked players: {plugin.sessions.count}")
    addLabel(form, f"Pending teleports: {teleports.pendingCount}")
    addLabel(form, f"Open requests: {teleports.requestCount}")

    try:
        addLabel(form, f"Server TPS: {plugin.server.average_tps:.2f}")
    except Exception:
        pass

    discord = plugin.discord
    if discord is not None:
        state = "connected" if discord.connected else discord.state
        addLabel(form, f"Discord relay: {state}")

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openAdminPanel(plugin, player), "back"))
    fm.sendForm(player, form, label="admin_info")


def _confirmReload(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.dialogs import askConfirmation

    def _doReload(p):
        success = plugin.reloadSettings()
        if success:
            plugin.messages.success(player, "Configuration reloaded.")
        else:
            plugin.messages.failure(player, "Reload failed. Check the console for details.")
        plugin.gui.untrack(player)

    askConfirmation(plugin, player, "Reload Config", "Reload the configuration now?", onYes=_doReload)


def _openSafeAreas(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    form = buildActionMenu("Safe Areas")

    areas = plugin.safeareas.listAll()

    if not areas:
        addLabel(form, "No safe areas have been created yet.")
        addLabel(form, "Use /safearea set <name> <radius> while standing at the location.")
    else:
        addLabel(form, f"{len(areas)} safe areas active")
        for area in areas:
            status = "ON" if area.get("enabled", False) else "OFF"
            radius = area.get("radius", 0)
            addButton(
                form,
                f"{area['name']} ({status}) R:{radius}",
                on_click=fm.wrapClick(player, lambda p=player, n=area['name']: _openSafeAreaDetail(plugin, p, n), f"safearea_detail:{area['name']}"),
            )

    addDivider(form)
    addButton(form, "Create Here", on_click=fm.wrapClick(player, lambda: _createSafeArea(plugin, player), "safearea_create"))
    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openAdminPanel(plugin, player), "back"))
    fm.sendForm(player, form, label="admin_safeareas")


def _openRanks(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.rank_menu import openRankList
    openRankList(plugin, player)


def _openSafeAreaDetail(plugin: UtilityStone, player, name: str) -> None:
    fm = plugin.gui

    area = plugin.safeareas.get(name)
    if area is None:
        plugin.messages.failure(player, f"Area '{name}' not found.")
        plugin.gui.untrack(player)
        return

    form = buildActionMenu(f"Safe Area: {name}")

    status = "ENABLED" if area.get("enabled", False) else "DISABLED"
    addLabel(form, f"Status: {status}")
    addLabel(form, f"Dimension: {area.get('dimension', '?')}")
    addLabel(form, f"Center: X={area.get('centerX', 0):.1f}, Z={area.get('centerZ', 0):.1f}")
    addLabel(form, f"Radius: {area.get('radius', 0)}")
    addLabel(form, f"Created by: {area.get('createdBy', '?')}")

    addDivider(form)

    if area.get("enabled", False):
        addButton(
            form,
            "Disable",
            on_click=fm.wrapClick(player, lambda p=player, n=name: _toggleSafeArea(plugin, p, n, False), f"safearea_disable:{name}"),
        )
    else:
        addButton(
            form,
            "Enable",
            on_click=fm.wrapClick(player, lambda p=player, n=name: _toggleSafeArea(plugin, p, n, True), f"safearea_enable:{name}"),
        )

    addButton(
        form,
        "Delete",
        on_click=fm.wrapClick(player, lambda p=player, n=name: _confirmDeleteSafeArea(plugin, p, n), f"safearea_delete:{name}"),
    )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openSafeAreas(plugin, player), "back"))
    fm.sendForm(player, form, label=f"admin_safearea:{name}")


def _createSafeArea(plugin: UtilityStone, player) -> None:
    from endstone.form import TextInput
    from endstone_utilitystone.ui.components import buildModal

    fm = plugin.gui
    controls = [
        TextInput(label="Area Name", placeholder="e.g., spawn"),
        TextInput(label="Radius (blocks)", placeholder="e.g., 100"),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if not parsed or len(parsed) < 2:
            plugin.messages.failure(player, "Please fill in both fields.")
            fm.untrack(player)
            return

        name = str(parsed[0]).strip()
        radiusStr = str(parsed[1]).strip()

        if not name:
            plugin.messages.failure(player, "Please enter an area name.")
            fm.untrack(player)
            return

        try:
            radius = float(radiusStr)
        except (ValueError, TypeError):
            plugin.messages.failure(player, "Radius must be a number.")
            fm.untrack(player)
            return

        location = player.location
        dimensionName = location.dimension.name
        centerX = location.x
        centerZ = location.z

        success, message = plugin.safeareas.create(
            name=name,
            dimension=dimensionName,
            centerX=centerX,
            centerZ=centerZ,
            radius=radius,
            createdBy=player.name,
        )

        if success:
            plugin.messages.success(player, message)
        else:
            plugin.messages.failure(player, message)

        fm.untrack(player)

    form = buildModal(
        "Create Safe Area",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, "safearea_create"),
        submitText="Create",
    )
    fm.sendForm(player, form, label="safearea_create_modal")


def _toggleSafeArea(plugin: UtilityStone, player, name: str, enabled: bool) -> None:
    success, message = plugin.safeareas.setEnabled(name, enabled)
    if success:
        plugin.messages.success(player, message)
    else:
        plugin.messages.failure(player, message)
    plugin.gui.untrack(player)


def _confirmDeleteSafeArea(plugin: UtilityStone, player, name: str) -> None:
    from endstone_utilitystone.ui.dialogs import askConfirmation

    def _doDelete(p):
        success, message = plugin.safeareas.delete(name)
        if success:
            plugin.messages.success(player, message)
        else:
            plugin.messages.failure(player, message)
        plugin.gui.untrack(player)

    askConfirmation(plugin, player, "Delete Safe Area", f"Delete safe area '{name}'?", onYes=_doDelete)
