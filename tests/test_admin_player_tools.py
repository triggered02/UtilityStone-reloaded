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
import sys

_WORKTREE_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(_WORKTREE_SRC) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_SRC))
for _name in list(sys.modules):
    if _name == "endstone_utilitystone" or _name.startswith("endstone_utilitystone."):
        del sys.modules[_name]

# ---------------------------------------------------------------------------
# Source file paths
# ---------------------------------------------------------------------------
_SRC = _WORKTREE_SRC / "endstone_utilitystone"
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

    def test_perm_inventory_edit_exists(self):
        assert "utilitystone.admin.inventory.edit" in _PLUGIN_SRC
        assert "utilitystone.admin.players.inventory.edit" in _PLUGIN_SRC

    def test_perm_enderchest_edit_exists(self):
        assert "utilitystone.admin.enderchest.edit" in _PLUGIN_SRC
        assert "utilitystone.admin.players.enderchest.edit" in _PLUGIN_SRC

    def test_permissions_default_to_op(self):
        """All admin permissions should default to op."""
        for perm in [
            "utilitystone.admin.players.inspect",
            "utilitystone.admin.homes.view",
            "utilitystone.admin.homes.teleport",
            "utilitystone.admin.homes.delete",
            "utilitystone.admin.inventory.view",
            "utilitystone.admin.inventory.edit",
            "utilitystone.admin.players.inventory.view",
            "utilitystone.admin.players.inventory.edit",
            "utilitystone.admin.enderchest.view",
            "utilitystone.admin.enderchest.edit",
            "utilitystone.admin.players.enderchest.view",
            "utilitystone.admin.players.enderchest.edit",
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
        assert 'PERM_INVENTORY_EDIT = "utilitystone.admin.inventory.edit"' in _PLAYER_TOOLS_SRC
        assert 'PERM_ENDERCHEST_VIEW = "utilitystone.admin.enderchest.view"' in _PLAYER_TOOLS_SRC
        assert 'PERM_ENDERCHEST_EDIT = "utilitystone.admin.enderchest.edit"' in _PLAYER_TOOLS_SRC


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


# ===========================================================================
# Unit / Logic Tests for Inventory & Ender Chest Editing
# ===========================================================================
import types
from unittest import mock
import unittest

class FakeContainer:
    def __init__(self, size=27):
        self._slots = [None] * size

    def __len__(self):
        return len(self._slots)

    def __getitem__(self, index):
        return self._slots[index]

    def __setitem__(self, index, item):
        self._slots[index] = item


class TestInventoryEditingExecution(unittest.TestCase):
    def setUp(self):
        from endstone_utilitystone.ui import admin_player_tools
        self.apt = admin_player_tools

        self.messages = []
        self.failures = []
        self.successes = []

        self.admin = types.SimpleNamespace(
            name="AdminPlayer",
            unique_id="admin-1",
            is_valid=True,
            has_permission=lambda p: True,
        )

        self.target = types.SimpleNamespace(
            name="TargetPlayer",
            unique_id="target-1",
            is_valid=True,
            allow_flight=False,
            game_mode=types.SimpleNamespace(name="survival"),
            location=types.SimpleNamespace(
                dimension=types.SimpleNamespace(name="overworld"),
                block_x=10, block_y=64, block_z=20,
            ),
            health=20.0,
            max_health=20.0,
            ping=15,
            inventory=FakeContainer(36),
            ender_chest=FakeContainer(27),
        )

        self.plugin = types.SimpleNamespace(
            logger=types.SimpleNamespace(info=lambda m: None),
            messages=types.SimpleNamespace(
                failure=lambda p, m: self.failures.append(m),
                success=lambda p, m: self.successes.append(m),
                info=lambda p, m: self.messages.append(m),
            ),
            sessions=types.SimpleNamespace(of=lambda p: None),
            profiles=types.SimpleNamespace(profileFor=lambda p: None),
            punishments=types.SimpleNamespace(muteFor=lambda id: None),
            ranks=None,
            godPlayers=set(),
            gui=types.SimpleNamespace(
                safePlayer=lambda p: p if getattr(p, "is_valid", False) else None,
                sendForm=lambda p, f, label="": True,
                wrapClick=lambda p, cb, l="": (lambda: cb()),
                wrapSubmit=lambda p, cb, l="": (lambda player, data: cb(player, data)),
                wrapClose=lambda p, l="": (lambda player: None),
            ),
        )

    def test_save_valid_inventory_edits(self):
        local_edits = {0: ("minecraft:diamond", 64, 0), 1: ("minecraft:apple", 10, 0)}
        self.apt._saveContainerEdits(self.plugin, self.admin, self.target, is_ender_chest=False, local_edits=local_edits)

        self.assertEqual(len(self.failures), 0)
        self.assertEqual(len(self.successes), 1)
        self.assertIsNotNone(self.target.inventory[0])
        self.assertEqual(self.target.inventory[0].amount, 64)
        self.assertIsNotNone(self.target.inventory[1])
        self.assertEqual(self.target.inventory[1].amount, 10)

    def test_save_valid_enderchest_edits(self):
        local_edits = {5: ("minecraft:emerald", 32, 0)}
        self.apt._saveContainerEdits(self.plugin, self.admin, self.target, is_ender_chest=True, local_edits=local_edits)

        self.assertEqual(len(self.failures), 0)
        self.assertEqual(len(self.successes), 1)
        self.assertIsNotNone(self.target.ender_chest[5])
        self.assertEqual(self.target.ender_chest[5].amount, 32)

    def test_unauthorized_save_blocked(self):
        unauth_admin = types.SimpleNamespace(
            name="UnauthAdmin",
            unique_id="admin-2",
            is_valid=True,
            has_permission=lambda p: False,
        )
        local_edits = {0: ("minecraft:diamond", 64, 0)}
        self.apt._saveContainerEdits(self.plugin, unauth_admin, self.target, is_ender_chest=False, local_edits=local_edits)

        self.assertEqual(len(self.failures), 1)
        self.assertIn("permission", self.failures[0].lower())
        self.assertIsNone(self.target.inventory[0])

    def test_invalid_item_identifier_rejected_atomically(self):
        local_edits = {
            0: ("minecraft:diamond", 64, 0),
            1: ("invalid_nonexistent_item_type_xyz", 10, 0),
        }
        with mock.patch("endstone.inventory.ItemStack", side_effect=lambda t, a, d: None if "invalid" in t else types.SimpleNamespace(type=t, amount=a, data=d)):
            self.apt._saveContainerEdits(self.plugin, self.admin, self.target, is_ender_chest=False, local_edits=local_edits)

        self.assertEqual(len(self.failures), 1)
        self.assertIn("Could not create item", self.failures[0])
        # Verify atomic failure: slot 0 must NOT be updated
        self.assertIsNone(self.target.inventory[0])

    def test_cancel_causes_no_mutation(self):
        # Opening inspector or editor does not mutate container
        initial_slot0 = self.target.inventory[0]
        self.apt._openContainerEditor(self.plugin, self.admin, self.target, is_ender_chest=False, page=0)
        self.assertEqual(self.target.inventory[0], initial_slot0)

    def test_disappearing_target_handled_cleanly(self):
        self.target.is_valid = False
        local_edits = {0: ("minecraft:diamond", 64, 0)}
        self.apt._saveContainerEdits(self.plugin, self.admin, self.target, is_ender_chest=False, local_edits=local_edits)

        self.assertEqual(len(self.failures), 1)
        self.assertIn("no longer online", self.failures[0])
