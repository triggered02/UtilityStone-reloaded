from __future__ import annotations

ADMIN_GUI_PERMISSION = "utilitystone.admin.gui"
PLAYER_GUI_PERMISSION = "utilitystone.command.menu"


def hasAdminGui(player) -> bool:
    return player.has_permission(ADMIN_GUI_PERMISSION)


def hasPlayerGui(player) -> bool:
    return player.has_permission(PLAYER_GUI_PERMISSION)


def hasPermission(player, node: str) -> bool:
    return player.has_permission(node)
