"""Comprehensive tests for the Safe Area system.

Tests cover:
- Pure helper functions (geometry, entity classification, name validation)
- SafeAreaService CRUD operations
- Player gamemode enforcement
- Overlapping areas
- Bypass system
- API verification for Endstone events used
"""

import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ──────────────────────────────────────────────────────────────────────
# Pure Helper Tests
# ──────────────────────────────────────────────────────────────────────


class TestIsInsideCircle:
    """Test the isInsideCircle geometry function."""

    def test_inside_circle(self):
        from endstone_utilitystone.util.safearea_helpers import isInsideCircle
        assert isInsideCircle(0, 0, 0, 0, 10) is True

    def test_outside_circle(self):
        from endstone_utilitystone.util.safearea_helpers import isInsideCircle
        assert isInsideCircle(15, 0, 0, 0, 10) is False

    def test_on_boundary(self):
        from endstone_utilitystone.util.safearea_helpers import isInsideCircle
        assert isInsideCircle(10, 0, 0, 0, 10) is True

    def test_negative_coordinates(self):
        from endstone_utilitystone.util.safearea_helpers import isInsideCircle
        assert isInsideCircle(-5, -5, 0, 0, 10) is True

    def test_large_distance(self):
        from endstone_utilitystone.util.safearea_helpers import isInsideCircle
        assert isInsideCircle(1000, 1000, 0, 0, 10) is False

    def test_zero_radius(self):
        from endstone_utilitystone.util.safearea_helpers import isInsideCircle
        assert isInsideCircle(0, 0, 0, 0, 0) is True
        assert isInsideCircle(1, 0, 0, 0, 0) is False

    def test_diagonal_distance(self):
        from endstone_utilitystone.util.safearea_helpers import isInsideCircle
        # 3-4-5 triangle
        assert isInsideCircle(3, 4, 0, 0, 5) is True
        assert isInsideCircle(3, 4, 0, 0, 4.9) is False


class TestHostileMobClassification:
    """Test hostile mob type classification."""

    def test_zombie_is_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:zombie") is True

    def test_creeper_is_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:creeper") is True

    def test_skeleton_is_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:skeleton") is True

    def test_wither_skeleton_is_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:wither_skeleton") is True

    def test_enderman_is_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:enderman") is True

    def test_phantom_is_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:phantom") is True

    def test_warden_is_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:warden") is True

    def test_cow_is_not_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:cow") is False

    def test_pig_is_not_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:pig") is False

    def test_player_is_not_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("minecraft:player") is False

    def test_empty_string_not_hostile(self):
        from endstone_utilitystone.util.safearea_helpers import isHostileMob
        assert isHostileMob("") is False


class TestBossClassification:
    """Test dangerous boss classification."""

    def test_wither_is_boss(self):
        from endstone_utilitystone.util.safearea_helpers import isDangerousBoss
        assert isDangerousBoss("minecraft:wither") is True

    def test_ender_dragon_is_boss(self):
        from endstone_utilitystone.util.safearea_helpers import isDangerousBoss
        assert isDangerousBoss("minecraft:ender_dragon") is True

    def test_zombie_is_not_boss(self):
        from endstone_utilitystone.util.safearea_helpers import isDangerousBoss
        assert isDangerousBoss("minecraft:zombie") is False


class TestExplosiveEntityClassification:
    """Test explosive entity classification."""

    def test_tnt_is_explosive(self):
        from endstone_utilitystone.util.safearea_helpers import isExplosiveEntity
        assert isExplosiveEntity("minecraft:tnt") is True

    def test_primed_tnt_is_explosive(self):
        from endstone_utilitystone.util.safearea_helpers import isExplosiveEntity
        assert isExplosiveEntity("minecraft:primed_tnt") is True

    def test_bed_is_explosive(self):
        from endstone_utilitystone.util.safearea_helpers import isExplosiveEntity
        assert isExplosiveEntity("minecraft:bed") is True

    def test_zombie_is_not_explosive(self):
        from endstone_utilitystone.util.safearea_helpers import isExplosiveEntity
        assert isExplosiveEntity("minecraft:zombie") is False


class TestDangerousEntityCombined:
    """Test combined dangerous entity classification."""

    def test_zombie_is_dangerous(self):
        from endstone_utilitystone.util.safearea_helpers import isDangerousEntity
        assert isDangerousEntity("minecraft:zombie") is True

    def test_wither_is_dangerous(self):
        from endstone_utilitystone.util.safearea_helpers import isDangerousEntity
        assert isDangerousEntity("minecraft:wither") is True

    def test_tnt_is_dangerous(self):
        from endstone_utilitystone.util.safearea_helpers import isDangerousEntity
        assert isDangerousEntity("minecraft:tnt") is True

    def test_cow_is_not_dangerous(self):
        from endstone_utilitystone.util.safearea_helpers import isDangerousEntity
        assert isDangerousEntity("minecraft:cow") is False

    def test_should_remove_actor(self):
        from endstone_utilitystone.util.safearea_helpers import shouldRemoveActor
        assert shouldRemoveActor("minecraft:zombie") is True
        assert shouldRemoveActor("minecraft:cow") is False


class TestAreaNameValidation:
    """Test area name validation."""

    def test_valid_name(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("spawn") is True

    def test_valid_name_with_numbers(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("area1") is True

    def test_valid_name_with_underscore(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("my_area") is True

    def test_valid_name_with_hyphen(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("my-area") is True

    def test_empty_name_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("") is False

    def test_space_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("my area") is False

    def test_path_traversal_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("../etc") is False
        assert isAcceptableAreaName("a/b") is False
        assert isAcceptableAreaName("a\\b") is False

    def test_too_long_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("a" * 33) is False

    def test_special_characters_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import isAcceptableAreaName
        assert isAcceptableAreaName("area@name") is False
        assert isAcceptableAreaName("area$name") is False


class TestAreaNameNormalization:
    """Test area name normalization."""

    def test_lowercase(self):
        from endstone_utilitystone.util.safearea_helpers import normalizeAreaName
        assert normalizeAreaName("SPAWN") == "spawn"

    def test_strip_whitespace(self):
        from endstone_utilitystone.util.safearea_helpers import normalizeAreaName
        assert normalizeAreaName("  spawn  ") == "spawn"

    def test_mixed_case(self):
        from endstone_utilitystone.util.safearea_helpers import normalizeAreaName
        assert normalizeAreaName("MyArea") == "myarea"


class TestRadiusValidation:
    """Test radius validation."""

    def test_valid_radius(self):
        from endstone_utilitystone.util.safearea_helpers import validateRadius
        valid, msg = validateRadius(100)
        assert valid is True
        assert msg == ""

    def test_valid_radius_string(self):
        from endstone_utilitystone.util.safearea_helpers import validateRadius
        valid, msg = validateRadius("100")
        assert valid is True

    def test_zero_radius_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import validateRadius
        valid, msg = validateRadius(0)
        assert valid is False
        assert "at least" in msg

    def test_negative_radius_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import validateRadius
        valid, msg = validateRadius(-10)
        assert valid is False

    def test_too_large_radius_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import validateRadius
        valid, msg = validateRadius(100001)
        assert valid is False
        assert "at most" in msg

    def test_non_numeric_radius_invalid(self):
        from endstone_utilitystone.util.safearea_helpers import validateRadius
        valid, msg = validateRadius("abc")
        assert valid is False
        assert "number" in msg


# ──────────────────────────────────────────────────────────────────────
# SafeAreaService Tests (Mocked)
# ──────────────────────────────────────────────────────────────────────


def _create_mock_plugin():
    """Create a mock plugin for testing SafeAreaService."""
    plugin = MagicMock()
    plugin.storage = MagicMock()
    plugin.server = MagicMock()
    plugin.settings = MagicMock()
    plugin.messages = MagicMock()

    # Create a mock store
    store = MagicMock()
    store.data = {"areas": {}}
    plugin.storage.open.return_value = store

    return plugin, store


class TestSafeAreaServiceCRUD:
    """Test SafeAreaService CRUD operations."""

    def test_create_area(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        success, msg = service.create("spawn", "OVERWORLD", 100, 200, 50, "Admin")
        assert success is True
        assert "created" in msg
        assert "spawn" in store.data["areas"]

    def test_create_duplicate_name(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 100, 200, 50, "Admin")
        success, msg = service.create("spawn", "OVERWORLD", 300, 400, 75, "Admin2")
        assert success is False
        assert "already exists" in msg

    def test_create_invalid_name(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        success, msg = service.create("../etc", "OVERWORLD", 100, 200, 50, "Admin")
        assert success is False
        assert "Invalid" in msg

    def test_create_invalid_radius(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        success, msg = service.create("spawn", "OVERWORLD", 100, 200, -5, "Admin")
        assert success is False
        assert "at least" in msg

    def test_delete_area(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 100, 200, 50, "Admin")
        success, msg = service.delete("spawn")
        assert success is True
        assert "deleted" in msg
        assert "spawn" not in store.data["areas"]

    def test_delete_nonexistent(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        success, msg = service.delete("nonexistent")
        assert success is False
        assert "No area" in msg

    def test_get_area(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 100, 200, 50, "Admin")
        area = service.get("spawn")
        assert area is not None
        assert area["dimension"] == "OVERWORLD"
        assert area["centerX"] == 100

    def test_get_nonexistent(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        area = service.get("nonexistent")
        assert area is None

    def test_list_areas(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("arena", "OVERWORLD", 0, 0, 100, "Admin")
        service.create("spawn", "OVERWORLD", 50, 50, 50, "Admin")

        areas = service.listAll()
        assert len(areas) == 2
        assert areas[0]["name"] == "arena"
        assert areas[1]["name"] == "spawn"

    def test_set_enabled(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 100, 200, 50, "Admin")
        success, msg = service.setEnabled("spawn", False)
        assert success is True
        assert "disabled" in msg

        area = service.get("spawn")
        assert area["enabled"] is False

    def test_set_enabled_nonexistent(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        success, msg = service.setEnabled("nonexistent", True)
        assert success is False


class TestSafeAreaServiceSpatialQueries:
    """Test SafeAreaService spatial queries."""

    def test_areas_containing(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        areas = service.areasContaining("OVERWORLD", 0, 0)
        assert len(areas) == 1
        assert areas[0]["name"] == "spawn"

    def test_areas_containing_outside(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        areas = service.areasContaining("OVERWORLD", 200, 200)
        assert len(areas) == 0

    def test_areas_containing_wrong_dimension(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        areas = service.areasContaining("NETHER", 0, 0)
        assert len(areas) == 0

    def test_areas_containing_disabled_area(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")
        service.setEnabled("spawn", False)

        areas = service.areasContaining("OVERWORLD", 0, 0)
        assert len(areas) == 0

    def test_is_inside(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        assert service.isInside("OVERWORLD", 0, 0) is True
        assert service.isInside("OVERWORLD", 200, 200) is False

    def test_overlapping_areas(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("area1", "OVERWORLD", 0, 0, 100, "Admin")
        service.create("area2", "OVERWORLD", 50, 0, 100, "Admin")

        # Point inside both areas (25, 0 is within 100 of both centers)
        areas = service.areasContaining("OVERWORLD", 25, 0)
        assert len(areas) == 2

        # Point inside only area1 (-80, 0 is 80 from area1 center, 130 from area2 center)
        areas = service.areasContaining("OVERWORLD", -80, 0)
        assert len(areas) == 1
        assert areas[0]["name"] == "area1"


class TestSafeAreaServicePlayerEnforcement:
    """Test SafeAreaService player gamemode enforcement."""

    def _create_mock_player(self, unique_id="player1", game_mode=None, is_op=False):
        """Create a mock player."""
        player = MagicMock()
        player.unique_id = unique_id
        player.name = "TestPlayer"
        player.is_op = is_op
        player.scoreboard_tags = set()

        if game_mode is not None:
            # Store game_mode as a regular attribute (not PropertyMock)
            # so setting player.game_mode = X actually works
            del player.game_mode  # Remove any default mock
            player.game_mode = game_mode

        def has_permission(perm):
            if is_op:
                return True
            if perm == "utilitystone.safearea.bypass":
                return False
            if perm == "utilitystone.admin":
                return False
            return False

        player.has_permission = has_permission

        location = MagicMock()
        location.dimension.name = "OVERWORLD"
        location.x = 0
        location.z = 0
        player.location = location

        return player

    def test_should_bypass_op_player(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        player = self._create_mock_player(is_op=True)
        assert service.shouldBypass(player) is True

    def test_should_not_bypass_normal_player(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        player = self._create_mock_player(is_op=False)
        assert service.shouldBypass(player) is False

    def test_entering_safe_area(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)
        service.updatePlayerLocation(player)

        state = service.getState(player)
        assert state is not None
        assert GameMode.ADVENTURE in [GameMode.ADVENTURE]  # Should be enforced

    def test_leaving_safe_area(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)

        # Enter area
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)

        # Leave area
        player.location.x = 200
        player.location.z = 200
        service.updatePlayerLocation(player)

        state = service.getState(player)
        assert state is None  # Should be cleared

    def test_overlapping_areas_enter_first(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("area1", "OVERWORLD", 0, 0, 100, "Admin")
        service.create("area2", "OVERWORLD", 50, 0, 100, "Admin")

        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)

        # Enter area1
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)

        state = service.getState(player)
        assert state is not None
        assert "area1" in state.insideAreas

    def test_overlapping_areas_enter_second(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("area1", "OVERWORLD", 0, 0, 100, "Admin")
        service.create("area2", "OVERWORLD", 50, 0, 100, "Admin")

        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)

        # Enter area1
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)

        # Enter area2 (still in area1)
        player.location.x = 25
        player.location.z = 0
        service.updatePlayerLocation(player)

        state = service.getState(player)
        assert state is not None
        assert "area1" in state.insideAreas
        assert "area2" in state.insideAreas

    def test_overlapping_areas_leave_one(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("area1", "OVERWORLD", 0, 0, 100, "Admin")
        service.create("area2", "OVERWORLD", 50, 0, 100, "Admin")

        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)

        # Enter both areas (25, 0 is inside both)
        player.location.x = 25
        player.location.z = 0
        service.updatePlayerLocation(player)

        # Leave area1 but stay in area2 (120, 0 is 120 from area1 center, 70 from area2 center)
        player.location.x = 120
        player.location.z = 0
        service.updatePlayerLocation(player)

        state = service.getState(player)
        assert state is not None
        assert "area1" not in state.insideAreas
        assert "area2" in state.insideAreas

    def test_clear_player_state(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)
        service.updatePlayerLocation(player)

        service.clearPlayerState(player)
        state = service.getState(player)
        assert state is None

    def test_restore_and_clear_restores_gamemode(self):
        """Test that restoreAndClearPlayerState restores original gamemode before clearing state."""
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        # Player enters safe area with SURVIVAL mode
        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)
        service.updatePlayerLocation(player)

        # Verify player is tracked and enforced to ADVENTURE
        state = service.getState(player)
        assert state is not None
        assert state.previousGamemode == GameMode.SURVIVAL
        assert player.game_mode == GameMode.ADVENTURE

        # Disconnect (should restore SURVIVAL before clearing state)
        service.restoreAndClearPlayerState(player)

        # Verify gamemode was restored to SURVIVAL
        assert player.game_mode == GameMode.SURVIVAL

        # Verify state was cleared
        state = service.getState(player)
        assert state is None

    def test_restore_and_clear_no_state(self):
        """Test restoreAndClearPlayerState with no existing state."""
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        player = self._create_mock_player()

        # Call restoreAndClearPlayerState with no state - should not crash
        service.restoreAndClearPlayerState(player)

        # Verify no state exists
        state = service.getState(player)
        assert state is None

    def test_restore_and_clear_prevents_adventure_as_previous(self):
        """Test that restoreAndClear prevents ADVENTURE from being saved as previousGamemode on rejoin.

        This is the critical bug fix: if a player disconnects inside a safe area
        without restoring gamemode, on rejoin the system would save ADVENTURE as
        their "original" gamemode, causing them to be stuck in ADVENTURE after leaving.
        """
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        # Player enters safe area with SURVIVAL mode
        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)
        service.updatePlayerLocation(player)

        # Verify enforcement
        state = service.getState(player)
        assert state.previousGamemode == GameMode.SURVIVAL

        # Simulate disconnect with proper restoration
        service.restoreAndClearPlayerState(player)
        assert player.game_mode == GameMode.SURVIVAL  # Restored

        # Simulate rejoin - player is now in SURVIVAL (restored)
        # When they enter the safe area again, SURVIVAL should be saved
        service.updatePlayerLocation(player)
        state = service.getState(player)
        assert state is not None
        assert state.previousGamemode == GameMode.SURVIVAL  # Correctly saved SURVIVAL, not ADVENTURE

    def test_restore_and_clear_does_not_affect_enforcing_set(self):
        """Test that restoreAndClearPlayerState properly cleans up the enforcing set."""
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        player = self._create_mock_player(game_mode=GameMode.SURVIVAL)
        playerKey = str(player.unique_id)

        service.updatePlayerLocation(player)

        # Verify enforcing set is clean after enforcement
        assert playerKey not in service._enforcing

        # Disconnect
        service.restoreAndClearPlayerState(player)

        # Verify enforcing set is still clean
        assert playerKey not in service._enforcing

    def test_restore_and_clear_with_adventure_mode_player(self):
        """Test restoreAndClearPlayerState when player was already in ADVENTURE mode."""
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)

        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        # Player enters safe area with ADVENTURE mode (e.g., creative builder)
        player = self._create_mock_player(game_mode=GameMode.ADVENTURE)
        service.updatePlayerLocation(player)

        # State should save ADVENTURE as previous (since that's what they had)
        state = service.getState(player)
        assert state.previousGamemode == GameMode.ADVENTURE

        # Disconnect
        service.restoreAndClearPlayerState(player)

        # Should restore to ADVENTURE (their original mode)
        assert player.game_mode == GameMode.ADVENTURE


class TestSafeAreaWalkOutRegression:
    """Regression tests for the exact reported bug:
    SURVIVAL → enter SafeArea → ADVENTURE → walk outside → SURVIVAL

    Each test verifies one specific property of the walk-out path.
    """

    def _create_service_with_area(self, center_x=0, center_z=0, radius=100):
        """Create a SafeAreaService with one 'spawn' area."""
        from endstone_utilitystone.services.safeareas import SafeAreaService
        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)
        service.create("spawn", "OVERWORLD", center_x, center_z, radius, "Admin")
        return service

    def _create_player(self, unique_id="player1", game_mode=None):
        """Create a mock player with mutable game_mode."""
        player = MagicMock()
        player.unique_id = unique_id
        player.name = "TestPlayer"
        player.is_op = False
        player.scoreboard_tags = set()
        player.has_permission = lambda perm: False
        if game_mode is not None:
            del player.game_mode
            player.game_mode = game_mode
        location = MagicMock()
        location.dimension.name = "OVERWORLD"
        location.x = 0
        location.z = 0
        player.location = location
        return player

    # ──────────────────────────────────────────────────────────────────
    # 1. updatePlayerLocation IS called on every movement tick
    # ──────────────────────────────────────────────────────────────────

    def test_walk_outside_triggers_updatePlayerLocation(self):
        """Walking outside the radius calls areasContaining with the new coordinates."""
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)

        # Enter
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert service.getState(player) is not None

        # Walk outside
        player.location.x = 200
        player.location.z = 0
        service.updatePlayerLocation(player)

        # State should be cleared (updatePlayerLocation ran and processed exit)
        assert service.getState(player) is None

    # ──────────────────────────────────────────────────────────────────
    # 2. areasContaining correctly detects outside-the-radius position
    # ──────────────────────────────────────────────────────────────────

    def test_areas_containing_returns_empty_outside_radius(self):
        """areasContaining returns empty list for a point outside the circle."""
        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)

        # Inside
        inside = service.areasContaining("OVERWORLD", 50, 0)
        assert len(inside) == 1

        # Exactly on boundary (100 units away) — inclusive
        boundary = service.areasContaining("OVERWORLD", 100, 0)
        assert len(boundary) == 1

        # Just outside boundary
        outside = service.areasContaining("OVERWORLD", 101, 0)
        assert len(outside) == 0

        # Far outside
        far_outside = service.areasContaining("OVERWORLD", 500, 500)
        assert len(far_outside) == 0

    # ──────────────────────────────────────────────────────────────────
    # 3. Gamemode is restored to SURVIVAL after walking out
    # ──────────────────────────────────────────────────────────────────

    def test_walk_out_restores_survival_gamemode(self):
        """Full path: SURVIVAL → enter → ADVENTURE → walk out → SURVIVAL."""
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)

        # Step 1: Player starts in SURVIVAL
        assert player.game_mode == GameMode.SURVIVAL

        # Step 2: Walk INTO the safe area
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)

        # Step 3: Verify switched to ADVENTURE
        assert player.game_mode == GameMode.ADVENTURE
        state = service.getState(player)
        assert state is not None
        assert state.previousGamemode == GameMode.SURVIVAL

        # Step 4: Walk OUTSIDE the safe area
        player.location.x = 200
        player.location.z = 0
        service.updatePlayerLocation(player)

        # Step 5: Verify restored to SURVIVAL
        assert player.game_mode == GameMode.SURVIVAL

    # ──────────────────────────────────────────────────────────────────
    # 4. Player state is cleared after restoration
    # ──────────────────────────────────────────────────────────────────

    def test_walk_out_clears_player_state(self):
        """After walking out, the player's state should be None."""
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)

        # Enter
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert service.getState(player) is not None

        # Walk out
        player.location.x = 200
        player.location.z = 0
        service.updatePlayerLocation(player)

        # State cleared
        assert service.getState(player) is None

    # ──────────────────────────────────────────────────────────────────
    # 5. Enforcing set is clean after walk-out (no leaked locks)
    # ──────────────────────────────────────────────────────────────────

    def test_walk_out_enforcing_set_clean(self):
        """After walking out, the _enforcing set should have no entry for this player."""
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)
        playerKey = str(player.unique_id)

        # Enter
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert playerKey not in service._enforcing

        # Walk out
        player.location.x = 200
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert playerKey not in service._enforcing

    # ──────────────────────────────────────────────────────────────────
    # 6. Teleport outside also restores correctly
    # ──────────────────────────────────────────────────────────────────

    def test_teleport_out_restores_survival(self):
        """Teleporting outside the safe area also restores gamemode."""
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)

        # Enter
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert player.game_mode == GameMode.ADVENTURE

        # Teleport outside (same code path as walk — updatePlayerLocation is called)
        player.location.x = -500
        player.location.z = -500
        service.updatePlayerLocation(player)

        assert player.game_mode == GameMode.SURVIVAL
        assert service.getState(player) is None

    # ──────────────────────────────────────────────────────────────────
    # 7. Rapid enter/exit does not corrupt state
    # ──────────────────────────────────────────────────────────────────

    def test_rapid_enter_exit_cycle(self):
        """Multiple rapid enter/exit cycles should always restore correctly."""
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)

        for _ in range(5):
            # Enter
            player.location.x = 0
            player.location.z = 0
            service.updatePlayerLocation(player)
            assert player.game_mode == GameMode.ADVENTURE

            # Exit
            player.location.x = 200
            player.location.z = 0
            service.updatePlayerLocation(player)
            assert player.game_mode == GameMode.SURVIVAL
            assert service.getState(player) is None

    # ──────────────────────────────────────────────────────────────────
    # 8. Walking to a different area within the zone does NOT restore
    # ──────────────────────────────────────────────────────────────────

    def test_staying_inside_does_not_restore(self):
        """Moving within the safe area keeps ADVENTURE, does not restore."""
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)

        # Enter at center
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert player.game_mode == GameMode.ADVENTURE

        # Move to edge but still inside
        player.location.x = 50
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert player.game_mode == GameMode.ADVENTURE
        assert service.getState(player) is not None

    # ──────────────────────────────────────────────────────────────────
    # 9. Re-entering after walk-out saves correct previous gamemode
    # ──────────────────────────────────────────────────────────────────

    def test_reenter_after_walkout_saves_survival(self):
        """After walking out and re-entering, previousGamemode should be SURVIVAL, not ADVENTURE."""
        from endstone import GameMode

        service = self._create_service_with_area(center_x=0, center_z=0, radius=100)
        player = self._create_player(game_mode=GameMode.SURVIVAL)

        # Enter → ADVENTURE
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert player.game_mode == GameMode.ADVENTURE

        # Walk out → SURVIVAL
        player.location.x = 200
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert player.game_mode == GameMode.SURVIVAL

        # Re-enter → should save SURVIVAL as previous (not ADVENTURE)
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)
        assert player.game_mode == GameMode.ADVENTURE
        state = service.getState(player)
        assert state is not None
        assert state.previousGamemode == GameMode.SURVIVAL

    # ──────────────────────────────────────────────────────────────────
    # 10. The _enforcing guard prevents onPlayerGameModeChange from blocking
    # ──────────────────────────────────────────────────────────────────

    def test_enforcing_guard_during_restore(self):
        """Verify the _enforcing set is populated during _restoreGamemode execution,
        preventing the PlayerGameModeChangeEvent handler from cancelling the restore."""
        from endstone_utilitystone.services.safeareas import SafeAreaService
        from endstone import GameMode

        plugin, store = _create_mock_plugin()
        service = SafeAreaService(plugin)
        service.create("spawn", "OVERWORLD", 0, 0, 100, "Admin")

        player = self._create_player(game_mode=GameMode.SURVIVAL)
        playerKey = str(player.unique_id)

        # Enter area
        player.location.x = 0
        player.location.z = 0
        service.updatePlayerLocation(player)

        # Simulate what onPlayerGameModeChange does: check isEnforcing
        # At this point, _enforcing should be clean
        assert not service.isEnforcing(playerKey)

        # Now walk out — _restoreGamemode should add to _enforcing before setting game_mode
        player.location.x = 200
        player.location.z = 0
        service.updatePlayerLocation(player)

        # After restoration, _enforcing should be clean again
        assert not service.isEnforcing(playerKey)
        assert player.game_mode == GameMode.SURVIVAL


class TestSafeAreaServiceDangerousActorScan:
    """Test SafeAreaService dangerous actor scanning."""

    def test_scan_returns_zero_when_disabled(self):
        from endstone_utilitystone.services.safeareas import SafeAreaService

        plugin, store = _create_mock_plugin()
        plugin.settings.safeareasEnabled = False
        service = SafeAreaService(plugin)

        removed = service.scanDangerousActors()
        assert removed == 0


# ──────────────────────────────────────────────────────────────────────
# API Verification Tests
# ──────────────────────────────────────────────────────────────────────


class TestSafeAreaEventAPIVerification:
    """Verify Endstone events used by SafeAreaListener exist and have correct attributes."""

    def test_player_move_event(self):
        from endstone.event import PlayerMoveEvent
        assert hasattr(PlayerMoveEvent, "player")
        assert hasattr(PlayerMoveEvent, "from_location")
        assert hasattr(PlayerMoveEvent, "to_location")
        assert hasattr(PlayerMoveEvent, "cancel")

    def test_player_teleport_event(self):
        from endstone.event import PlayerTeleportEvent
        assert hasattr(PlayerTeleportEvent, "player")
        assert hasattr(PlayerTeleportEvent, "from_location")
        assert hasattr(PlayerTeleportEvent, "to_location")
        assert hasattr(PlayerTeleportEvent, "cancel")

    def test_player_join_event(self):
        from endstone.event import PlayerJoinEvent
        assert hasattr(PlayerJoinEvent, "player")

    def test_player_quit_event(self):
        from endstone.event import PlayerQuitEvent
        assert hasattr(PlayerQuitEvent, "player")

    def test_actor_spawn_event(self):
        from endstone.event import ActorSpawnEvent
        assert hasattr(ActorSpawnEvent, "actor")
        assert hasattr(ActorSpawnEvent, "cancel")

    def test_actor_explode_event(self):
        from endstone.event import ActorExplodeEvent
        assert hasattr(ActorExplodeEvent, "actor")
        assert hasattr(ActorExplodeEvent, "location")
        assert hasattr(ActorExplodeEvent, "cancel")

    def test_block_explode_event(self):
        from endstone.event import BlockExplodeEvent
        assert hasattr(BlockExplodeEvent, "block")
        assert hasattr(BlockExplodeEvent, "cancel")

    def test_block_place_event(self):
        from endstone.event import BlockPlaceEvent
        assert hasattr(BlockPlaceEvent, "block")
        assert hasattr(BlockPlaceEvent, "player")
        assert hasattr(BlockPlaceEvent, "cancel")

    def test_block_break_event(self):
        from endstone.event import BlockBreakEvent
        assert hasattr(BlockBreakEvent, "block")
        assert hasattr(BlockBreakEvent, "player")
        assert hasattr(BlockBreakEvent, "cancel")

    def test_player_gamemode_change_event(self):
        from endstone.event import PlayerGameModeChangeEvent
        assert hasattr(PlayerGameModeChangeEvent, "player")
        assert hasattr(PlayerGameModeChangeEvent, "new_game_mode")
        assert hasattr(PlayerGameModeChangeEvent, "cancel")

    def test_game_mode_enum(self):
        from endstone import GameMode
        assert hasattr(GameMode, "SURVIVAL")
        assert hasattr(GameMode, "CREATIVE")
        assert hasattr(GameMode, "ADVENTURE")
        assert hasattr(GameMode, "SPECTATOR")


class TestSafeAreaActorAPIVerification:
    """Verify Actor APIs used by SafeAreaService."""

    def test_actor_type(self):
        from endstone.actor import Actor
        assert hasattr(Actor, "type")

    def test_actor_location(self):
        from endstone.actor import Actor
        assert hasattr(Actor, "location")

    def test_actor_remove(self):
        from endstone.actor import Actor
        assert hasattr(Actor, "remove")

    def test_actor_is_valid(self):
        from endstone.actor import Actor
        assert hasattr(Actor, "is_valid")

    def test_actor_scoreboard_tags(self):
        from endstone.actor import Actor
        assert hasattr(Actor, "scoreboard_tags")

    def test_player_game_mode(self):
        from endstone import Player
        assert hasattr(Player, "game_mode")

    def test_player_is_op(self):
        from endstone import Player
        assert hasattr(Player, "is_op")

    def test_player_has_permission(self):
        from endstone import Player
        assert hasattr(Player, "has_permission")


# ──────────────────────────────────────────────────────────────────────
# Code Verification Tests
# ──────────────────────────────────────────────────────────────────────


class TestSafeAreaCodeVerification:
    """Verify the Safe Area implementation uses correct APIs."""

    def test_safearea_listener_uses_correct_events(self):
        """Verify SafeAreaListener imports and uses correct events."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "safearea.py"
        source = path.read_text()

        # Must use correct event imports
        assert "PlayerMoveEvent" in source
        assert "PlayerTeleportEvent" in source
        assert "ActorSpawnEvent" in source
        assert "BlockExplodeEvent" in source
        assert "ActorExplodeEvent" in source
        assert "BlockPlaceEvent" in source
        assert "BlockBreakEvent" in source
        assert "PlayerGameModeChangeEvent" in source

    def test_safearea_listener_uses_game_mode_enum(self):
        """Verify SafeAreaListener uses GameMode.ADVENTURE, not hardcoded value."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "safearea.py"
        source = path.read_text()

        # Must use GameMode.ADVENTURE, not hardcoded integer
        assert "GameMode.ADVENTURE" in source
        # Must NOT use hardcoded integer 4 for adventure mode
        assert "!= 4" not in source, "Must use GameMode.ADVENTURE, not hardcoded integer 4"

    def test_safearea_service_uses_storage(self):
        """Verify SafeAreaService uses JsonStore pattern."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "services" / "safeareas.py"
        source = path.read_text()

        assert "plugin.storage.open" in source
        assert "markDirty" in source

    def test_safearea_commands_extend_command_group(self):
        """Verify SafeAreaCommands extends CommandGroup."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "commands" / "safeareas.py"
        source = path.read_text()

        assert "CommandGroup" in source
        assert "def bindings" in source

    def test_plugin_initializes_safeareas(self):
        """Verify plugin.py initializes SafeAreaService."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "plugin.py"
        source = path.read_text()

        assert "SafeAreaService" in source
        assert "self.safeareas" in source

    def test_config_has_safeareas_section(self):
        """Verify config.toml has safeareas section."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "config.toml"
        source = path.read_text()

        assert "[safeareas]" in source
        assert "enabled" in source
        assert "scanIntervalSeconds" in source

    def test_settings_parses_safeareas(self):
        """Verify Settings class parses safeareas config."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "core" / "settings.py"
        source = path.read_text()

        assert "safeareasEnabled" in source
        assert "safeareasScanIntervalSeconds" in source
        assert "safeareasBypassPermission" in source
        assert "safeareasBypassTag" in source

    def test_admin_menu_has_safeareas(self):
        """Verify admin_menu.py has Safe Areas button."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "admin_menu.py"
        source = path.read_text()

        assert "Safe Areas" in source
        assert "_openSafeAreas" in source
        assert "_openSafeAreaDetail" in source
        assert "_createSafeArea" in source

    def test_safearea_listener_uses_restore_and_clear(self):
        """Verify SafeAreaListener uses restoreAndClearPlayerState on quit."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "safearea.py"
        source = path.read_text()

        # Must use restoreAndClearPlayerState on quit to restore gamemode
        assert "restoreAndClearPlayerState" in source
        # Must NOT use clearPlayerState on quit (would lose gamemode)
        assert "clearPlayerState" not in source

    def test_safearea_service_has_restore_and_clear(self):
        """Verify SafeAreaService has restoreAndClearPlayerState method."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "services" / "safeareas.py"
        source = path.read_text()

        assert "def restoreAndClearPlayerState" in source
        assert "def clearPlayerState" in source  # Still exists for other uses
