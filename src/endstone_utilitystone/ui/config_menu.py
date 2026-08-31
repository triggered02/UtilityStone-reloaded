from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from endstone.form import Toggle, Slider, TextInput, Dropdown, Label, Header, Divider

from endstone_utilitystone.ui.components import (
    addDivider,
    addHeader,
    addLabel,
    addButton,
    buildActionMenu,
    buildModal,
)

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone

_configLock = threading.Lock()


class ConfigField:
    __slots__ = ("key", "label", "description", "fieldType", "default", "minVal", "maxVal", "step", "options", "secret")

    def __init__(self, key: str, label: str, description: str, fieldType: str, default: Any = None,
                 minVal: float = 0, maxVal: float = 100, step: float = 1, options: list | None = None, secret: bool = False):
        self.key = key
        self.label = label
        self.description = description
        self.fieldType = fieldType
        self.default = default
        self.minVal = minVal
        self.maxVal = maxVal
        self.step = step
        self.options = options or []
        self.secret = secret


CONFIG_CATEGORIES = {
    "Homes": [
        ConfigField("homes.defaultLimit", "Default Home Limit", "Maximum homes per player", "int", 3, 0, 500, 1),
    ],
    "Warps": [
        ConfigField("warps.requirePerWarpPermission", "Per-Warp Permissions", "Require permission for each warp", "bool", False),
    ],
    "Spawn": [
        ConfigField("spawn.teleportOnFirstJoin", "Teleport on First Join", "Send new players to spawn on first join", "bool", False),
    ],
    "Teleport": [
        ConfigField("teleport.warmupSeconds", "Warmup Seconds", "Delay before teleport (0 = instant)", "float", 3.0, 0.0, 60.0, 0.5),
        ConfigField("teleport.cooldownSeconds", "Cooldown Seconds", "Wait between teleports", "float", 5.0, 0.0, 3600.0, 1.0),
        ConfigField("teleport.requestTimeoutSeconds", "Request Timeout", "How long TPA requests stay open", "float", 60.0, 10.0, 600.0, 5.0),
        ConfigField("teleport.cancelOnMove", "Cancel on Move", "Cancel warmup if player moves", "bool", True),
        ConfigField("teleport.moveTolerance", "Move Tolerance", "How far player may drift during warmup (blocks)", "float", 0.75, 0.1, 16.0, 0.25),
        ConfigField("teleport.pollTicks", "Poll Ticks", "How often warmups are checked (20 ticks = 1s)", "int", 10, 2, 40, 1),
        ConfigField("teleport.rememberDeathLocation", "Remember Death Location", "Allow /back to return to death point", "bool", True),
        ConfigField("teleport.historySize", "Back History Size", "How many positions /back remembers", "int", 5, 1, 25, 1),
    ],
    "Chat": [
        ConfigField("chat.manageFormat", "Manage Chat Format", "Let UtilityStone deliver chat (enables /ignore in chat)", "bool", True),
        ConfigField("chat.format", "Chat Format", "Chat layout ({name} and {message} are replaced)", "string", "<{name}> {message}"),
        ConfigField("chat.afkTag", "AFK Tag", "Prefix for AFK players in chat", "string", "&7[AFK] &r"),
    ],
    "AFK": [
        ConfigField("afk.enabled", "AFK Detection", "Automatic AFK detection", "bool", True),
        ConfigField("afk.timeoutSeconds", "AFK Timeout", "Idle time before marked AFK (seconds)", "float", 300.0, 30.0, 7200.0, 30.0),
        ConfigField("afk.sampleSeconds", "Sample Interval", "How often positions are sampled", "float", 5.0, 1.0, 60.0, 1.0),
        ConfigField("afk.announce", "Announce AFK", "Announce AFK changes in chat", "bool", True),
    ],
    "Connection Messages": [
        ConfigField("connection.joinMessage", "Join Message", "Custom join message ({name} replaced, empty = default, 'none' = hidden)", "string", ""),
        ConfigField("connection.quitMessage", "Quit Message", "Custom quit message ({name} replaced, empty = default, 'none' = hidden)", "string", ""),
        ConfigField("connection.welcomeMessage", "Welcome Message", "Private message sent on join ({name} replaced, empty = none)", "string", ""),
    ],
    "Storage": [
        ConfigField("storage.saveIntervalSeconds", "Save Interval", "How often data is flushed to disk (seconds)", "float", 30.0, 5.0, 900.0, 5.0),
        ConfigField("storage.playtimeSyncSeconds", "Playtime Sync", "How often playtime totals are synced", "float", 120.0, 15.0, 1800.0, 15.0),
    ],
    "Messages": [
        ConfigField("messages.usePrefix", "Use Prefix", "Show prefix in plugin messages", "bool", True),
        ConfigField("messages.prefix", "Prefix", "Message prefix (supports & colour codes)", "string", "&8[&bUtilityStone&8]&r "),
    ],
    "Discord": [
        ConfigField("discord.enabled", "Relay Enabled", "Master switch for Discord relay", "bool", True),
        ConfigField("discord.relayChat", "Relay Chat", "Send player chat to Discord", "bool", True),
        ConfigField("discord.relayDeaths", "Relay Deaths", "Send death messages to Discord", "bool", True),
        ConfigField("discord.relayJoinLeave", "Relay Join/Leave", "Send join and leave messages to Discord", "bool", True),
        ConfigField("discord.relayServerState", "Relay Server State", "Send server start/shutdown to Discord", "bool", True),
        ConfigField("discord.sendIntervalSeconds", "Send Interval", "How often messages are batched and sent", "float", 1.5, 0.5, 30.0, 0.5),
        ConfigField("discord.inboundPollTicks", "Inbound Poll Ticks", "How often Discord messages are handed to game", "int", 10, 2, 40, 1),
        ConfigField("discord.maxInboundLength", "Max Inbound Length", "Truncate longer Discord messages in game", "int", 256, 32, 1024, 32),
        ConfigField("discord.chatFormat", "Chat Format", "Discord chat layout ({name} and {message})", "string", "**{name}**: {message}"),
        ConfigField("discord.eventFormat", "Event Format", "Discord event layout ({message})", "string", "_{message}_"),
        ConfigField("discord.inboundFormat", "Inbound Format", "In-game Discord message layout", "string", "&9[Discord] &b{name}&7: &f{message}"),
    ],
}

SECRET_FIELDS = {"discord.token", "discord.channel_id"}

# Build the set of allowed keys from CONFIG_CATEGORIES for validation
ALLOWED_CONFIG_KEYS: set[str] = set()
for _catFields in CONFIG_CATEGORIES.values():
    for _field in _catFields:
        ALLOWED_CONFIG_KEYS.add(_field.key)
# Also include the menu item keys which are managed separately but still valid
ALLOWED_CONFIG_KEYS.update({
    "menuItem.enabled", "menuItem.itemType", "menuItem.name",
    "menuItem.lore", "menuItem.slot",
})


def _readTomlValue(tomlText: str, dottedKey: str) -> Any:
    keys = dottedKey.split(".")
    lines = tomlText.split("\n")
    currentSection = []
    result = None
    inArray = False
    arrayDepth = 0

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("[["):
            inArray = True
            arrayDepth = stripped.count("[[")
            sectionMatch = stripped.lstrip("[")
            sectionMatch = sectionMatch.rstrip("]")
            currentSection = sectionMatch.split(".")
            continue

        if stripped.startswith("[") and not stripped.startswith("[["):
            inArray = False
            arrayDepth = 0
            sectionMatch = stripped.lstrip("[").rstrip("]")
            currentSection = sectionMatch.split(".")
            continue

        if inArray:
            continue

        if "=" in stripped:
            eqIndex = stripped.index("=")
            key = stripped[:eqIndex].strip().strip('"')
            value = stripped[eqIndex + 1:].strip()

            expectedPath = currentSection + [key]
            if expectedPath == keys:
                result = _parseTomlValue(value)
                break

    return result


def _parseTomlValue(value: str) -> Any:
    value = value.strip()

    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    return value


def _writeTomlValue(tomlText: str, dottedKey: str, newValue: Any) -> str:
    keys = dottedKey.split(".")
    lines = tomlText.split("\n")
    result = []
    currentSection = []
    found = False
    inArray = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("[["):
            inArray = True
            sectionMatch = stripped.lstrip("[[").rstrip("]]")
            currentSection = sectionMatch.split(".")
            result.append(line)
            continue

        if stripped.startswith("[") and not stripped.startswith("[["):
            inArray = False
            sectionMatch = stripped.lstrip("[").rstrip("]")
            currentSection = sectionMatch.split(".")
            result.append(line)
            continue

        if inArray:
            result.append(line)
            continue

        if "=" in stripped and not found:
            eqIndex = stripped.index("=")
            key = stripped[:eqIndex].strip().strip('"')
            expectedPath = currentSection + [key]

            if expectedPath == keys:
                indent = line[: len(line) - len(line.lstrip())]
                formatted = _formatTomlValue(newValue)
                result.append(f'{indent}{key} = {formatted}')
                found = True
                continue

        result.append(line)

    if not found:
        sectionPath = keys[:-1]
        key = keys[-1]
        formatted = _formatTomlValue(newValue)

        if sectionPath:
            sectionHeader = "[" + ".".join(sectionPath) + "]"
            sectionFound = False
            for i, line in enumerate(result):
                if line.strip() == sectionHeader:
                    sectionFound = True
                    break

            if sectionFound:
                insertIdx = i + 1
                while insertIdx < len(result) and result[insertIdx].strip() and not result[insertIdx].strip().startswith("["):
                    insertIdx += 1
                result.insert(insertIdx, f"{key} = {formatted}")
            else:
                result.append("")
                result.append(sectionHeader)
                result.append(f"{key} = {formatted}")
        else:
            result.append(f"{key} = {formatted}")

    return "\n".join(result)


def _formatTomlValue(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value == int(value):
            return f"{value:.1f}"
        return str(value)
    if isinstance(value, str):
        if any(c in value for c in "{}[],\"'#="):
            return "'" + value.replace("'", "\\'") + "'"
        return f'"{value}"'
    return str(value)


def _getCurrentValue(plugin: UtilityStone, dottedKey: str) -> Any:
    settings = plugin.settings
    keys = dottedKey.split(".")

    sectionName = keys[0] if keys else ""
    keyName = keys[1] if len(keys) > 1 else ""

    attrMap = {
        ("homes", "defaultLimit"): lambda: settings.homeDefaultLimit,
        ("warps", "requirePerWarpPermission"): lambda: settings.warpsNeedPermission,
        ("spawn", "teleportOnFirstJoin"): lambda: settings.spawnOnFirstJoin,
        ("teleport", "warmupSeconds"): lambda: settings.teleportWarmupSeconds,
        ("teleport", "cooldownSeconds"): lambda: settings.teleportCooldownSeconds,
        ("teleport", "requestTimeoutSeconds"): lambda: settings.teleportRequestSeconds,
        ("teleport", "cancelOnMove"): lambda: settings.teleportCancelOnMove,
        ("teleport", "moveTolerance"): lambda: settings.teleportMoveTolerance,
        ("teleport", "pollTicks"): lambda: settings.teleportPollTicks,
        ("teleport", "rememberDeathLocation"): lambda: settings.backOnDeath,
        ("teleport", "historySize"): lambda: settings.backHistorySize,
        ("chat", "manageFormat"): lambda: settings.chatManaged,
        ("chat", "format"): lambda: settings.chatFormat,
        ("chat", "afkTag"): lambda: settings.chatAfkTag,
        ("afk", "enabled"): lambda: settings.afkEnabled,
        ("afk", "timeoutSeconds"): lambda: settings.afkTimeoutSeconds,
        ("afk", "sampleSeconds"): lambda: settings.afkSampleSeconds,
        ("afk", "announce"): lambda: settings.afkAnnounce,
        ("connection", "joinMessage"): lambda: settings.joinMessage,
        ("connection", "quitMessage"): lambda: settings.quitMessage,
        ("connection", "welcomeMessage"): lambda: settings.welcomeMessage,
        ("storage", "saveIntervalSeconds"): lambda: settings.saveIntervalSeconds,
        ("storage", "playtimeSyncSeconds"): lambda: settings.playtimeSyncSeconds,
        ("messages", "usePrefix"): lambda: settings.usePrefix,
        ("messages", "prefix"): lambda: settings.prefix,
        ("discord", "enabled"): lambda: settings.discordEnabled,
        ("discord", "relayChat"): lambda: settings.discordRelayChat,
        ("discord", "relayDeaths"): lambda: settings.discordRelayDeaths,
        ("discord", "relayJoinLeave"): lambda: settings.discordRelayJoinLeave,
        ("discord", "relayServerState"): lambda: settings.discordRelayServerState,
        ("discord", "sendIntervalSeconds"): lambda: settings.discordSendIntervalSeconds,
        ("discord", "inboundPollTicks"): lambda: settings.discordPollTicks,
        ("discord", "maxInboundLength"): lambda: settings.discordInboundLimit,
        ("discord", "chatFormat"): lambda: settings.discordChatFormat,
        ("discord", "eventFormat"): lambda: settings.discordEventFormat,
        ("discord", "inboundFormat"): lambda: settings.discordInboundFormat,
    }

    getter = attrMap.get((sectionName, keyName))
    if getter:
        return getter()

    return None


def _applySetting(plugin: UtilityStone, dottedKey: str, value: Any) -> bool:
    # Validate the key against the whitelist before any file I/O
    if dottedKey not in ALLOWED_CONFIG_KEYS:
        plugin.logger.warning(f"Rejected config edit for unknown or restricted key: {dottedKey}")
        return False
    if dottedKey in SECRET_FIELDS:
        plugin.logger.warning(f"Rejected config edit for secret key: {dottedKey}")
        return False

    configPath = Path(plugin.data_folder) / "config.toml"
    if not configPath.exists():
        plugin.logger.error("config.toml not found")
        return False

    with _configLock:
        try:
            tomlText = configPath.read_text(encoding="utf-8")
        except OSError as exc:
            plugin.logger.error(f"Could not read config.toml: {exc}")
            return False

        newToml = _writeTomlValue(tomlText, dottedKey, value)

        try:
            tempPath = configPath.with_name("config.toml.tmp")
            tempPath.write_text(newToml, encoding="utf-8")
            import os
            os.replace(tempPath, configPath)
        except OSError as exc:
            plugin.logger.error(f"Could not write config.toml: {exc}")
            try:
                tempPath = configPath.with_name("config.toml.tmp")
                if tempPath.exists():
                    tempPath.unlink()
            except Exception:
                pass
            return False

    success = plugin.reloadSettings()
    if not success:
        plugin.logger.warning("Config was written but reload failed - changes will take effect on next restart")

    return True


def openConfigCategoryList(plugin: UtilityStone, player) -> bool:
    fm = plugin.gui

    form = buildActionMenu("Configuration", "Edit plugin settings in-game")

    for categoryName in CONFIG_CATEGORIES:
        fields = CONFIG_CATEGORIES[categoryName]
        visibleFields = [f for f in fields if not f.secret and f.key not in SECRET_FIELDS]
        if visibleFields:
            addButton(
                form,
                categoryName,
                on_click=fm.wrapClick(player, lambda p=player, cat=categoryName: _openCategory(plugin, p, cat), f"config:{categoryName}"),
            )

    addDivider(form)
    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: fm.navigator.openAdminPanel(player), "back"))

    return fm.sendForm(player, form, label="config_categories")


def _openCategory(plugin: UtilityStone, player, categoryName: str) -> None:
    fm = plugin.gui
    fields = CONFIG_CATEGORIES.get(categoryName, [])
    visibleFields = [f for f in fields if not f.secret and f.key not in SECRET_FIELDS]

    if not visibleFields:
        form = buildActionMenu(categoryName)
        addLabel(form, "No editable settings in this category.")
        addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openConfigCategoryList(plugin, player), "back"))
        fm.sendForm(player, form, label=f"config:{categoryName}")
        return

    form = buildActionMenu(categoryName)

    for field in visibleFields:
        currentValue = _getCurrentValue(plugin, field.key)
        if currentValue is None:
            currentValue = field.default

        displayValue = _displayValue(field, currentValue)
        addLabel(form, f"{field.label}: {displayValue}")

        if field.fieldType == "bool":
            addButton(
                form,
                f"Toggle {field.label}",
                on_click=fm.wrapClick(player, lambda p=player, f=field: _openBoolEditor(plugin, p, f), f"edit:{field.key}"),
            )
        elif field.fieldType in ("int", "float"):
            addButton(
                form,
                f"Edit {field.label}",
                on_click=fm.wrapClick(player, lambda p=player, f=field: _openNumericEditor(plugin, p, f), f"edit:{field.key}"),
            )
        elif field.fieldType == "string":
            addButton(
                form,
                f"Edit {field.label}",
                on_click=fm.wrapClick(player, lambda p=player, f=field: _openStringEditor(plugin, p, f), f"edit:{field.key}"),
            )
        elif field.fieldType == "enum":
            addButton(
                form,
                f"Edit {field.label}",
                on_click=fm.wrapClick(player, lambda p=player, f=field: _openEnumEditor(plugin, p, f), f"edit:{field.key}"),
            )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openConfigCategoryList(plugin, player), "back"))
    fm.sendForm(player, form, label=f"config:{categoryName}")


def _displayValue(field: ConfigField, value: Any) -> str:
    if field.fieldType == "bool":
        return "Enabled" if value else "Disabled"
    if field.fieldType == "float":
        return f"{value:g}"
    if field.fieldType == "int":
        return str(int(value))
    if field.fieldType == "string":
        if not value:
            return "(empty)"
        from endstone_utilitystone.util.text import shorten
        return shorten(value, 40)
    return str(value)


def _openBoolEditor(plugin: UtilityStone, player, field: ConfigField) -> None:
    fm = plugin.gui
    currentValue = _getCurrentValue(plugin, field.key)

    controls = [Toggle(label=field.label, default_value=bool(currentValue))]

    def _handleSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            newValue = bool(parsed[0])
            if _applySetting(plugin, field.key, newValue):
                plugin.messages.success(player, f"{field.label} set to {'enabled' if newValue else 'disabled'}.")
            else:
                plugin.messages.failure(player, f"Failed to save {field.label}.")
        fm.untrack(player)

    form = buildModal(
        title=f"Edit: {field.label}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _handleSubmit, f"config:{field.key}"),
        onClose=fm.wrapClose(player, f"config:{field.key}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"config_edit:{field.key}")


def _openNumericEditor(plugin: UtilityStone, player, field: ConfigField) -> None:
    fm = plugin.gui
    currentValue = _getCurrentValue(plugin, field.key)
    if currentValue is None:
        currentValue = field.default

    step = field.step
    minVal = field.minVal
    maxVal = field.maxVal

    if field.fieldType == "int":
        currentInt = int(currentValue)
        minInt = int(minVal)
        maxInt = int(maxVal)
        stepInt = max(1, int(step))

        controls = [Slider(
            label=field.label,
            min=float(minInt),
            max=float(maxInt),
            step=float(stepInt),
            default_value=float(currentInt),
        )]
    else:
        controls = [Slider(
            label=field.label,
            min=minVal,
            max=maxVal,
            step=step,
            default_value=float(currentValue),
        )]

    addLabelCtrl = Label(text=f"Range: {minVal:g} - {maxVal:g}")
    controls.append(addLabelCtrl)

    def _handleSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            raw = parsed[0]
            if field.fieldType == "int":
                newValue = int(float(raw))
                newValue = max(int(minVal), min(int(maxVal), newValue))
            else:
                newValue = float(raw)
                newValue = max(minVal, min(maxVal, newValue))

            if _applySetting(plugin, field.key, newValue):
                plugin.messages.success(player, f"{field.label} set to {newValue:g}.")
            else:
                plugin.messages.failure(player, f"Failed to save {field.label}.")
        fm.untrack(player)

    form = buildModal(
        title=f"Edit: {field.label}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _handleSubmit, f"config:{field.key}"),
        onClose=fm.wrapClose(player, f"config:{field.key}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"config_edit:{field.key}")


def _openStringEditor(plugin: UtilityStone, player, field: ConfigField) -> None:
    fm = plugin.gui
    currentValue = _getCurrentValue(plugin, field.key)
    if currentValue is None:
        currentValue = field.default

    controls = [TextInput(
        label=field.label,
        placeholder=field.description,
        default_value=str(currentValue),
    )]

    def _handleSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            newValue = str(parsed[0])
            if _applySetting(plugin, field.key, newValue):
                plugin.messages.success(player, f"{field.label} updated.")
            else:
                plugin.messages.failure(player, f"Failed to save {field.label}.")
        fm.untrack(player)

    form = buildModal(
        title=f"Edit: {field.label}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _handleSubmit, f"config:{field.key}"),
        onClose=fm.wrapClose(player, f"config:{field.key}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"config_edit:{field.key}")


def _openEnumEditor(plugin: UtilityStone, player, field: ConfigField) -> None:
    fm = plugin.gui
    currentValue = _getCurrentValue(plugin, field.key)
    if currentValue is None:
        currentValue = field.default

    controls = [Dropdown(
        label=field.label,
        options=field.options,
        default_index=field.options.index(currentValue) if currentValue in field.options else 0,
    )]

    def _handleSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            idx = int(parsed[0])
            if 0 <= idx < len(field.options):
                newValue = field.options[idx]
                if _applySetting(plugin, field.key, newValue):
                    plugin.messages.success(player, f"{field.label} set to {newValue}.")
                else:
                    plugin.messages.failure(player, f"Failed to save {field.label}.")
        fm.untrack(player)

    form = buildModal(
        title=f"Edit: {field.label}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _handleSubmit, f"config:{field.key}"),
        onClose=fm.wrapClose(player, f"config:{field.key}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"config_edit:{field.key}")
