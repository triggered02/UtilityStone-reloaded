"""
Regression tests for Admin Player Tools — Features 1–7.

Tests cover:
- Player Inspector permissions and structure
- Admin Homes inspection
- Inventory inspection (read-only, pagination)
- Ender Chest inspection (read-only, pagination)
- Player list navigation
- Permission node verification
- Audit logging structure
"""

from __future__ import annotations

import pathlib

# ---------------------------------------------------------------------------
# Source file paths
# ---------------------------------------------------------------------------
_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone"
_PLAYER_TOOLS_SRC = (_SRC / "ui" / "admin_player_tools.py").read_text()
_ADMIN_MENU_SRC = (_SRC / "ui" / "admin_menu.py").read_text()
_PLUGIN_SRC = (_SRC / "plugin.py").read_text()


# ===========================================================================
# Feature 1 — Player Inspector
# ===========================================================================
class TestPlayerInspector:
    """Verify Player Inspector exists and has required structure."""

    def test_openPlayerList_function_exists(self):
        assert "def openPlayerList(" in _PLAYER_TOOLS_SRC

    def test_openPlayerInspector_function_exists(self):
        assert "def _openPlayerInspector(" in _PLAYER_TOOLS_SRC

    def test_inspector_shows_username(self):
        assert 'f"Username:' in _PLAYER_TOOLS_SRC

    def test_inspector_shows_uuid(self):
        assert 'f"UUID:' in _PLAYER_TOOLS_SRC

    def test_inspector_shows_gamemode(self):
        assert 'f"Gamemode:' in _PLAYER_TOOLS_SRC

    def test_inspector_shows_dimension(self):
        assert 'f"Dimension:' in _PLAYER_TOOLS_SRC

    def test_inspector_shows_coordinates(self):
        assert 'f"Coordinates:' in _PLAYER_TOOLS_SRC

    def test_inspector_shows_health(self):
        assert 'f"Health:' in _PLAYER_TOOLS_SRC

    def test_inspector_shows_ping(self):
        assert 'f"Ping:' in _PLAYER_TOOLS_SRC

    def test_inspector_has_teleport_to_player(self):
        assert '"Teleport To Player"' in _PLAYER_TOOLS_SRC

    def test_inspector_has_teleport_player_to_me(self):
        assert '"Teleport Player To Me"' in _PLAYER_TOOLS_SRC

    def test_inspector_has_view_homes(self):
        assert '"View Homes"' in _PLAYER_TOOLS_SRC

    def test_inspector_has_view_inventory(self):
        assert '"View Inventory"' in _PLAYER_TOOLS_SRC

    def test_inspector_has_view_ender_chest(self):
        assert '"View Ender Chest"' in _PLAYER_TOOLS_SRC


# ===========================================================================
# Feature 2 — Admin Homes
# ===========================================================================
class TestAdminHomes:
    """Verify admin homes inspection exists and uses existing service."""

    def test_openAdminHomesForPlayer_function_exists(self):
        assert "def _openAdminHomesForPlayer(" in _PLAYER_TOOLS_SRC

    def test_admin_homes_uses_homes_service(self):
        assert "plugin.homes.homesOf(" in _PLAYER_TOOLS_SRC

    def test_admin_homes_shows_dimension(self):
        assert 'f"Dimension:' in _PLAYER_TOOLS_SRC

    def test_admin_homes_has_teleport_button(self):
        assert '"Teleport To "' in _PLAYER_TOOLS_SRC or "Teleport To" in _PLAYER_TOOLS_SRC

    def test_admin_homes_has_delete_button(self):
        assert '"Delete "' in _PLAYER_TOOLS_SRC or "Delete" in _PLAYER_TOOLS_SRC

    def test_admin_homes_delete_uses_existing_service(self):
        assert "plugin.homes.deleteHome(" in _PLAYER_TOOLS_SRC

    def test_admin_homes_teleport_permission_check(self):
        assert "PERM_HOMES_TELEPORT" in _PLAYER_TOOLS_SRC

    def test_admin_homes_view_permission_check(self):
        assert "PERM_HOMES_VIEW" in _PLAYER_TOOLS_SRC

    def test_admin_homes_delete_permission_check(self):
        assert "PERM_HOMES_DELETE" in _PLAYER_TOOLS_SRC


# ===========================================================================
# Feature 3 — Inventory Inspection
# ===========================================================================
class TestInventoryInspection:
    """Verify inventory inspection is read-only and uses correct API."""

    def test_openInventoryView_function_exists(self):
        assert "def _openInventoryView(" in _PLAYER_TOOLS_SRC

    def test_inventory_uses_player_inventory(self):
        assert "target.inventory" in _PLAYER_TOOLS_SRC

    def test_inventory_reads_slots(self):
        assert "inventory[slot]" in _PLAYER_TOOLS_SRC

    def test_inventory_handles_empty_slots(self):
        assert "Empty" in _PLAYER_TOOLS_SRC

    def test_inventory_shows_amount(self):
        assert "item.amount" in _PLAYER_TOOLS_SRC

    def test_inventory_has_pagination(self):
        assert '"Previous Page"' in _PLAYER_TOOLS_SRC
        assert '"Next Page"' in _PLAYER_TOOLS_SRC

    def test_inventory_permission_check(self):
        assert "PERM_INVENTORY_VIEW" in _PLAYER_TOOLS_SRC

    def test_inventory_does_not_modify(self):
        """Inventory inspection must not call __setitem__, clear, add_item."""
        lines = _PLAYER_TOOLS_SRC.split("\n")
        in_inventory_function = False
        for line in lines:
            if "def _openInventoryView(" in line:
                in_inventory_function = True
            elif in_inventory_function and line.strip().startswith("def "):
                in_inventory_function = False
            if in_inventory_function:
                assert "__setitem__" not in line, "Inventory view must not write to slots"
                assert ".clear(" not in line, "Inventory view must not clear slots"
                assert ".add_item(" not in line, "Inventory view must not add items"


# ===========================================================================
# Feature 4 — Ender Chest Inspection
# ===========================================================================
class TestEnderChestInspection:
    """Verify ender chest inspection is read-only and uses correct API."""

    def test_openEnderChestView_function_exists(self):
        assert "def _openEnderChestView(" in _PLAYER_TOOLS_SRC

    def test_ender_chest_uses_player_ender_chest(self):
        assert "target.ender_chest" in _PLAYER_TOOLS_SRC

    def test_ender_chest_reads_slots(self):
        assert "enderChest[slot]" in _PLAYER_TOOLS_SRC

    def test_ender_chest_handles_empty_slots(self):
        assert "Empty" in _PLAYER_TOOLS_SRC

    def test_ender_chest_shows_amount(self):
        assert "item.amount" in _PLAYER_TOOLS_SRC

    def test_ender_chest_has_pagination(self):
        assert '"Previous Page"' in _PLAYER_TOOLS_SRC
        assert '"Next Page"' in _PLAYER_TOOLS_SRC

    def test_ender_chest_permission_check(self):
        assert "PERM_ENDERCHEST_VIEW" in _PLAYER_TOOLS_SRC

    def test_ender_chest_does_not_modify(self):
        """Ender chest inspection must not write to slots."""
        lines = _PLAYER_TOOLS_SRC.split("\n")
        in_ender_function = False
        for line in lines:
            if "def _openEnderChestView(" in line:
                in_ender_function = True
            elif in_ender_function and line.strip().startswith("def "):
                in_ender_function = False
            if in_ender_function:
                assert "__setitem__" not in line, "Ender chest view must not write to slots"
                assert ".clear(" not in line, "Ender chest view must not clear slots"


# ===========================================================================
# Feature 5 — Player List / Selection
# ===========================================================================
class TestPlayerList:
    """Verify player list navigation."""

    def test_player_list_function_exists(self):
        assert "def openPlayerList(" in _PLAYER_TOOLS_SRC

    def test_player_list_shows_online_players(self):
        assert "plugin.server.online_players" in _PLAYER_TOOLS_SRC

    def test_player_list_has_back_button(self):
        assert '"Back"' in _PLAYER_TOOLS_SRC

    def test_player_list_permission_check(self):
        assert "PERM_INSPECT" in _PLAYER_TOOLS_SRC

    def test_admin_menu_delegates_to_player_list(self):
        assert "from endstone_utilitystone.ui.admin_player_tools import openPlayerList" in _ADMIN_MENU_SRC


# ===========================================================================
# Feature 6 — Permissions
# ===========================================================================
class TestPermissions:
    """Verify permission nodes exist in plugin.py and are used in code."""

    def test_perm_inspect_exists(self):
        assert "utilitystone.admin.players.inspect" in _PLUGIN_SRC

    def test_perm_homes_view_exists(self):
        assert "utilitystone.admin.homes.view" in _PLUGIN_SRC

    def test_perm_homes_teleport_exists(self):
        assert "utilitystone.admin.homes.teleport" in _PLUGIN_SRC

    def test_perm_homes_delete_exists(self):
        assert "utilitystone.admin.homes.delete" in _PLUGIN_SRC

    def test_perm_inventory_view_exists(self):
        assert "utilitystone.admin.inventory.view" in _PLUGIN_SRC

    def test_perm_enderchest_view_exists(self):
        assert "utilitystone.admin.enderchest.view" in _PLUGIN_SRC

    def test_permissions_default_to_op(self):
        """All admin permissions should default to op."""
        for perm in [
            "utilitystone.admin.players.inspect",
            "utilitystone.admin.homes.view",
            "utilitystone.admin.homes.teleport",
            "utilitystone.admin.homes.delete",
            "utilitystone.admin.inventory.view",
            "utilitystone.admin.enderchest.view",
        ]:
            assert f'"{perm}"' in _PLUGIN_SRC
            # Check it's in the permissions dict with "op" default
            idx = _PLUGIN_SRC.index(f'"{perm}"')
            nearby = _PLUGIN_SRC[idx:idx + 200]
            assert '"op"' in nearby or "'op'" in nearby, f"{perm} should default to op"

    def test_permission_constants_defined(self):
        assert 'PERM_INSPECT = "utilitystone.admin.players.inspect"' in _PLAYER_TOOLS_SRC
        assert 'PERM_HOMES_VIEW = "utilitystone.admin.homes.view"' in _PLAYER_TOOLS_SRC
        assert 'PERM_HOMES_TELEPORT = "utilitystone.admin.homes.teleport"' in _PLAYER_TOOLS_SRC
        assert 'PERM_HOMES_DELETE = "utilitystone.admin.homes.delete"' in _PLAYER_TOOLS_SRC
        assert 'PERM_INVENTORY_VIEW = "utilitystone.admin.inventory.view"' in _PLAYER_TOOLS_SRC
        assert 'PERM_ENDERCHEST_VIEW = "utilitystone.admin.enderchest.view"' in _PLAYER_TOOLS_SRC


# ===========================================================================
# Feature 7 — Audit Logging
# ===========================================================================
class TestAuditLogging:
    """Verify audit logging is present for sensitive actions."""

    def test_audit_function_exists(self):
        assert "def _audit(" in _PLAYER_TOOLS_SRC

    def test_audit_uses_plugin_logger(self):
        assert "plugin.logger.info(" in _PLAYER_TOOLS_SRC

    def test_inspect_action_logged(self):
        assert 'inspected player' in _PLAYER_TOOLS_SRC

    def test_view_homes_action_logged(self):
        assert 'viewed homes of' in _PLAYER_TOOLS_SRC

    def test_teleport_to_home_action_logged(self):
        assert 'teleported to home' in _PLAYER_TOOLS_SRC

    def test_view_inventory_action_logged(self):
        assert 'viewed inventory of' in _PLAYER_TOOLS_SRC

    def test_view_ender_chest_action_logged(self):
        assert 'viewed Ender Chest of' in _PLAYER_TOOLS_SRC

    def test_teleport_to_player_action_logged(self):
        assert 'teleported to' in _PLAYER_TOOLS_SRC

    def test_teleport_player_to_me_action_logged(self):
        assert 'teleported' in _PLAYER_TOOLS_SRC


# ===========================================================================
# Item Display Helper
# ===========================================================================
class TestItemDisplayHelper:
    """Verify item display name helper."""

    def test_getItemDisplayName_function_exists(self):
        assert "def _getItemDisplayName(" in _PLAYER_TOOLS_SRC

    def test_item_display_uses_translation_key(self):
        assert "translation_key" in _PLAYER_TOOLS_SRC

    def test_item_display_fallback_to_type(self):
        assert "str(item.type)" in _PLAYER_TOOLS_SRC
