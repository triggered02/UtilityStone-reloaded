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

    addHeader(form, "Players & Moderation")
    addButton(form, "Player Management", icon="textures/icons/Stats_Icon", on_click=fm.wrapClick(player, lambda: _openPlayerManagement(plugin, player), "admin_players"))
    addButton(form, "Homes", icon="textures/icons/Homes_Bed", on_click=fm.wrapClick(player, lambda: _openAdminHomes(plugin, player), "admin_homes"))
    addButton(form, "Warps", icon="textures/icons/LandClaims", on_click=fm.wrapClick(player, lambda: _openAdminWarps(plugin, player), "admin_warps"))
    addButton(form, "Spawn", icon="textures/icons/UpArrow", on_click=fm.wrapClick(player, lambda: _openAdminSpawn(plugin, player), "admin_spawn"))
    addButton(form, "Kits", icon="textures/icons/crate_icon", on_click=fm.wrapClick(player, lambda: _openAdminKits(plugin, player), "admin_kits"))

    addDivider(form)
    addHeader(form, "Ranks & Permissions")
    addButton(form, "Ranks", icon="textures/icons/admin", on_click=fm.wrapClick(player, lambda: _openRanks(plugin, player), "admin_ranks"))

    addDivider(form)
    addHeader(form, "Server & World")
    addButton(form, "Broadcasts", icon="textures/icons/TPA_Globe", on_click=fm.wrapClick(player, lambda: openBroadcastManager(plugin, player), "admin_broadcasts"))
    addButton(form, "Safe Areas", icon="textures/icons/LandClaims", on_click=fm.wrapClick(player, lambda: _openSafeAreas(plugin, player), "admin_safeareas"))
    addButton(form, "Daily Rewards", icon="textures/icons/loot", on_click=fm.wrapClick(player, lambda: _openDailyRewards(plugin, player), "admin_daily_rewards"))

    addDivider(form)
    addHeader(form, "Server Tools")
    addButton(form, "Plugin Info", icon="textures/icons/Stats_Icon", on_click=fm.wrapClick(player, lambda: _openPluginInfo(plugin, player), "admin_info"))
    addButton(form, "Reload Config", icon="textures/icons/admin", on_click=fm.wrapClick(player, lambda: _confirmReload(plugin, player), "admin_reload"))

    addDivider(form)
    addButton(form, "Configuration", icon="textures/icons/admin", on_click=fm.wrapClick(player, lambda: fm.navigator.openConfigEditor(player), "admin_config"))

    addButton(form, "Back to Menu", icon="textures/icons/Arrow_Left_Curved", on_click=fm.wrapClick(player, lambda: fm.navigator.openPlayerMenu(player), "back"))

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


def _openDailyRewards(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.daily_rewards import openDailyRewardsAdmin
    openDailyRewardsAdmin(plugin, player)


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


# ---------------------------------------------------------------------------
# Broadcast Manager
# ---------------------------------------------------------------------------
PERM_BROADCASTS = "utilitystone.admin.broadcasts"


def openBroadcastManager(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.permissions import hasPermission
    fm = plugin.gui

    if not hasPermission(player, PERM_BROADCASTS):
        plugin.messages.failure(player, "You do not have permission to manage broadcasts.")
        return

    form = buildActionMenu("Manage Broadcasts", "Automated server broadcast system")

    broadcasts = plugin.broadcasts
    enabled = broadcasts.enabled if broadcasts else False
    interval_secs = broadcasts.intervalSeconds if broadcasts else 1200.0
    messages = broadcasts.messages if broadcasts else []

    from endstone_utilitystone.util.durations import formatDuration
    status_str = "ENABLED" if enabled else "DISABLED"
    interval_str = formatDuration(interval_secs)

    addLabel(form, f"Status: {status_str}")
    addLabel(form, f"Interval: {interval_str}")
    addLabel(form, f"Configured Messages: {len(messages)}")

    addDivider(form)

    # Toggle Enable / Disable
    toggle_text = "Disable Broadcasts" if enabled else "Enable Broadcasts"
    addButton(
        form,
        toggle_text,
        icon="textures/icons/admin",
        on_click=fm.wrapClick(player, lambda: _toggleBroadcasts(plugin, player, not enabled), "toggle_broadcasts"),
    )

    # Change Interval
    addButton(
        form,
        "Change Interval",
        icon="textures/icons/Stats_Icon",
        on_click=fm.wrapClick(player, lambda: _promptChangeInterval(plugin, player, interval_secs), "change_interval"),
    )

    # Send Test Broadcast
    if messages:
        addButton(
            form,
            "Send Test Broadcast",
            icon="textures/icons/TPA_Globe",
            on_click=fm.wrapClick(player, lambda: _sendTestBroadcast(plugin, player), "test_broadcast"),
        )

    # Add Message
    addButton(
        form,
        "Add Broadcast Message",
        icon="textures/icons/crate_icon",
        on_click=fm.wrapClick(player, lambda: _promptAddMessage(plugin, player), "add_broadcast_msg"),
    )

    # List Messages
    if messages:
        addDivider(form)
        addHeader(form, "Messages")
        for i, msg in enumerate(messages):
            first_line = msg.split("\n")[0]
            preview = first_line[:30] + ("..." if len(first_line) > 30 or "\n" in msg else "")
            idx = i
            addButton(
                form,
                f"#{i + 1}: {preview}",
                icon="textures/icons/loot",
                on_click=fm.wrapClick(player, lambda p=player, ix=idx: _openMessageDetail(plugin, p, ix), f"msg_detail:{i}"),
            )

    addDivider(form)
    addButton(
        form,
        "Back",
        icon="textures/icons/Arrow_Left_Curved",
        on_click=fm.wrapClick(player, lambda: openAdminPanel(plugin, player), "back"),
    )

    fm.sendForm(player, form, label="broadcast_manager")


def _saveBroadcastConfigAndReload(plugin: UtilityStone) -> None:
    from pathlib import Path
    path = Path(plugin.data_folder) / "config.toml"
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8")
            from endstone_utilitystone.ui.config_menu import _writeTomlValue
            text = _writeTomlValue(text, "broadcasts.enabled", plugin.settings.broadcastsEnabled)
            text = _writeTomlValue(text, "broadcasts.intervalSeconds", plugin.settings.broadcastsIntervalSeconds)
            text = _writeTomlValue(text, "broadcasts.cycle", plugin.settings.broadcastsCycle)
            text = _writeTomlValue(text, "broadcasts.prefix", plugin.settings.broadcastsPrefix)
            text = _writeTomlValue(text, "broadcasts.messages", plugin.settings.broadcastsMessages)
            path.write_text(text, encoding="utf-8")
        except Exception:
            pass

    plugin.reloadSettings()


def _toggleBroadcasts(plugin: UtilityStone, player, enable: bool) -> None:
    plugin.settings.broadcastsEnabled = enable
    if plugin.broadcasts:
        plugin.broadcasts.setEnabled(enable)
    _saveBroadcastConfigAndReload(plugin)
    state = "enabled" if enable else "disabled"
    plugin.messages.success(player, f"Automated broadcasts are now {state}.")
    openBroadcastManager(plugin, player)


def _promptChangeInterval(plugin: UtilityStone, player, current_secs: float) -> None:
    from endstone.form import TextInput
    from endstone_utilitystone.ui.components import buildModal
    fm = plugin.gui

    controls = [
        TextInput(label="Interval in seconds (min 5s, e.g. 1200 for 20m)", placeholder="1200", default_value=str(int(current_secs))),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if not parsed or len(parsed) < 1:
            openBroadcastManager(plugin, player)
            return

        raw = str(parsed[0]).strip()
        try:
            val = float(raw)
            if val < 5.0:
                plugin.messages.failure(player, "Interval must be at least 5 seconds.")
                openBroadcastManager(plugin, player)
                return
        except ValueError:
            plugin.messages.failure(player, "Please enter a valid number of seconds.")
            openBroadcastManager(plugin, player)
            return

        plugin.settings.broadcastsIntervalSeconds = val
        if plugin.broadcasts:
            plugin.broadcasts.setInterval(val)
        _saveBroadcastConfigAndReload(plugin)
        from endstone_utilitystone.util.durations import formatDuration
        plugin.messages.success(player, f"Broadcast interval set to {formatDuration(val)}.")
        openBroadcastManager(plugin, player)

    form = buildModal(
        "Change Broadcast Interval",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, "change_interval"),
        submitText="Save",
    )
    fm.sendForm(player, form, label="change_interval_modal")


def _sendTestBroadcast(plugin: UtilityStone, player) -> None:
    if plugin.broadcasts and plugin.broadcasts.broadcastNext():
        plugin.messages.success(player, "Broadcast sent to online players.")
    else:
        plugin.messages.failure(player, "No broadcast messages available to send.")
    openBroadcastManager(plugin, player)


def _promptAddMessage(plugin: UtilityStone, player) -> None:
    from endstone.form import TextInput
    from endstone_utilitystone.ui.components import buildModal
    fm = plugin.gui

    controls = [
        TextInput(label="Broadcast Message (use \\n for line breaks)", placeholder="e.g. Join our Discord! \\n https://discord.gg/xyz"),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if not parsed or len(parsed) < 1:
            openBroadcastManager(plugin, player)
            return

        msg = str(parsed[0]).strip().replace("\\n", "\n")
        if not msg:
            plugin.messages.failure(player, "Message cannot be empty.")
            openBroadcastManager(plugin, player)
            return

        plugin.settings.broadcastsMessages.append(msg)
        if plugin.broadcasts:
            plugin.broadcasts.addMessage(msg)
        _saveBroadcastConfigAndReload(plugin)
        plugin.messages.success(player, "Added new broadcast message.")
        openBroadcastManager(plugin, player)

    form = buildModal(
        "Add Broadcast Message",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, "add_message"),
        submitText="Add",
    )
    fm.sendForm(player, form, label="add_message_modal")


def _openMessageDetail(plugin: UtilityStone, player, index: int) -> None:
    fm = plugin.gui

    messages = plugin.settings.broadcastsMessages
    if index < 0 or index >= len(messages):
        openBroadcastManager(plugin, player)
        return

    msg_text = messages[index]

    form = buildActionMenu(f"Broadcast #{index + 1}")
    addLabel(form, f"Message Content:\n\n{msg_text}")
    addDivider(form)

    # Edit
    idx = index
    addButton(
        form,
        "Edit Message",
        icon="textures/icons/crate_icon",
        on_click=fm.wrapClick(player, lambda p=player, i=idx: _promptEditMessage(plugin, p, i), f"edit_msg:{index}"),
    )

    # Delete
    addButton(
        form,
        "Delete Message",
        icon="textures/icons/admin",
        on_click=fm.wrapClick(player, lambda p=player, i=idx: _confirmDeleteMessage(plugin, p, i), f"del_msg:{index}"),
    )

    # Send Now
    addButton(
        form,
        "Send This Message Now",
        icon="textures/icons/TPA_Globe",
        on_click=fm.wrapClick(player, lambda p=player, txt=msg_text: _sendSpecificBroadcast(plugin, p, txt), f"send_msg:{index}"),
    )

    addButton(
        form,
        "Back",
        icon="textures/icons/Arrow_Left_Curved",
        on_click=fm.wrapClick(player, lambda: openBroadcastManager(plugin, player), "back"),
    )

    fm.sendForm(player, form, label=f"msg_detail:{index}")


def _promptEditMessage(plugin: UtilityStone, player, index: int) -> None:
    from endstone.form import TextInput
    from endstone_utilitystone.ui.components import buildModal
    fm = plugin.gui

    messages = plugin.settings.broadcastsMessages
    if index < 0 or index >= len(messages):
        openBroadcastManager(plugin, player)
        return

    current = messages[index].replace("\n", "\\n")
    controls = [
        TextInput(label="Broadcast Message (use \\n for line breaks)", placeholder="", default_value=current),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if not parsed or len(parsed) < 1:
            openBroadcastManager(plugin, player)
            return

        new_msg = str(parsed[0]).strip().replace("\\n", "\n")
        if not new_msg:
            plugin.messages.failure(player, "Message cannot be empty.")
            openBroadcastManager(plugin, player)
            return

        if 0 <= index < len(plugin.settings.broadcastsMessages):
            plugin.settings.broadcastsMessages[index] = new_msg
            if plugin.broadcasts:
                plugin.broadcasts.editMessage(index, new_msg)
            _saveBroadcastConfigAndReload(plugin)
            plugin.messages.success(player, f"Updated broadcast message #{index + 1}.")

        openBroadcastManager(plugin, player)

    form = buildModal(
        f"Edit Message #{index + 1}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, f"edit_message:{index}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"edit_message_modal:{index}")


def _confirmDeleteMessage(plugin: UtilityStone, player, index: int) -> None:
    from endstone_utilitystone.ui.dialogs import askConfirmation

    def _doDelete(p):
        if 0 <= index < len(plugin.settings.broadcastsMessages):
            plugin.settings.broadcastsMessages.pop(index)
            if plugin.broadcasts:
                plugin.broadcasts.deleteMessage(index)
            _saveBroadcastConfigAndReload(plugin)
            plugin.messages.success(player, f"Deleted broadcast message #{index + 1}.")
        openBroadcastManager(plugin, player)

    askConfirmation(plugin, player, "Delete Message", f"Are you sure you want to delete broadcast message #{index + 1}?", onYes=_doDelete)


def _sendSpecificBroadcast(plugin: UtilityStone, player, text: str) -> None:
    if plugin.broadcasts and plugin.broadcasts.broadcastNext(specific_message=text):
        plugin.messages.success(player, "Broadcast sent to online players.")
    else:
        plugin.messages.failure(player, "Could not send broadcast.")
    openBroadcastManager(plugin, player)
