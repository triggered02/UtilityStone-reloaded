"""Safe Area service for managing protected regions.

This service handles:
- CRUD operations on safe areas
- Spatial queries (which areas contain a point)
- Player gamemode enforcement
- Dangerous entity tracking
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from endstone.actor import Actor
from endstone import GameMode, Player

from endstone_utilitystone.util.safearea_helpers import (
    ALL_DANGEROUS_ENTITIES,
    isAcceptableAreaName,
    isDangerousEntity,
    isInsideCircle,
    normalizeAreaName,
    shouldRemoveActor,
    validateRadius,
)

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


class PlayerState:
    """Tracks a player's gamemode state while inside safe areas."""

    __slots__ = ("previousGamemode", "insideAreas", "isEnforcing")

    def __init__(self, previousGamemode: GameMode) -> None:
        self.previousGamemode: GameMode = previousGamemode
        self.insideAreas: set[str] = set()
        self.isEnforcing: bool = False


class SafeAreaService:
    """Manages safe areas, player enforcement, and dangerous entity cleanup."""

    def __init__(self, plugin: UtilityStone) -> None:
        self.plugin = plugin
        self.store = plugin.storage.open("safeareas", {"areas": {}})

        # In-memory player state tracking
        # Key: str(player.unique_id), Value: PlayerState
        self._playerStates: dict[str, PlayerState] = {}

        # Set of player IDs currently being enforced (to prevent recursion)
        self._enforcing: set[str] = set()

    # ──────────────────────────────────────────────────────────────────
    # CRUD Operations
    # ──────────────────────────────────────────────────────────────────

    def create(
        self,
        name: str,
        dimension: str,
        centerX: float,
        centerZ: float,
        radius: float,
        createdBy: str,
    ) -> tuple[bool, str]:
        """Create a new safe area.

        Returns:
            Tuple of (success, message). If success is False, message contains error.
        """
        normalizedName = normalizeAreaName(name)

        if not isAcceptableAreaName(normalizedName):
            return False, "Invalid area name. Use only letters, numbers, underscores, and hyphens."

        valid, errorMsg = validateRadius(radius)
        if not valid:
            return False, errorMsg

        areas = self.store.data.get("areas", {})
        if normalizedName in areas:
            return False, f"An area named '{normalizedName}' already exists."

        areas[normalizedName] = {
            "dimension": dimension,
            "centerX": float(centerX),
            "centerZ": float(centerZ),
            "radius": float(radius),
            "enabled": True,
            "createdBy": createdBy,
            "createdAt": time.time(),
        }

        self.store.data["areas"] = areas
        self.store.markDirty()
        return True, f"Safe area '{normalizedName}' created."

    def delete(self, name: str) -> tuple[bool, str]:
        """Delete a safe area.

        Returns:
            Tuple of (success, message).
        """
        normalizedName = normalizeAreaName(name)
        areas = self.store.data.get("areas", {})

        if normalizedName not in areas:
            return False, f"No area named '{normalizedName}' exists."

        del areas[normalizedName]
        self.store.data["areas"] = areas
        self.store.markDirty()
        return True, f"Safe area '{normalizedName}' deleted."

    def get(self, name: str) -> dict | None:
        """Get a safe area by name.

        Returns:
            Area dict if found, None otherwise.
        """
        normalizedName = normalizeAreaName(name)
        return self.store.data.get("areas", {}).get(normalizedName)

    def listAll(self) -> list[dict]:
        """List all safe areas.

        Returns:
            List of dicts with name and area data.
        """
        areas = self.store.data.get("areas", {})
        result = []
        for name, data in areas.items():
            result.append({"name": name, **data})
        return sorted(result, key=lambda a: a["name"])

    def setEnabled(self, name: str, enabled: bool) -> tuple[bool, str]:
        """Enable or disable a safe area.

        Returns:
            Tuple of (success, message).
        """
        normalizedName = normalizeAreaName(name)
        areas = self.store.data.get("areas", {})
        area = areas.get(normalizedName)

        if area is None:
            return False, f"No area named '{normalizedName}' exists."

        area["enabled"] = enabled
        self.store.markDirty()

        status = "enabled" if enabled else "disabled"
        return True, f"Safe area '{normalizedName}' {status}."

    # ──────────────────────────────────────────────────────────────────
    # Spatial Queries
    # ──────────────────────────────────────────────────────────────────

    def areasContaining(self, dimension: str, x: float, z: float) -> list[dict]:
        """Find all enabled safe areas that contain the given point.

        Args:
            dimension: Dimension name (e.g., "OVERWORLD")
            x: X coordinate
            z: Z coordinate

        Returns:
            List of area dicts that contain the point.
        """
        areas = self.store.data.get("areas", {})
        result = []

        for name, area in areas.items():
            if not area.get("enabled", False):
                continue

            if area.get("dimension") != dimension:
                continue

            if isInsideCircle(
                x, z,
                area["centerX"], area["centerZ"],
                area["radius"]
            ):
                result.append({"name": name, **area})

        return result

    def isInside(self, dimension: str, x: float, z: float) -> bool:
        """Check if a point is inside any enabled safe area.

        Args:
            dimension: Dimension name
            x: X coordinate
            z: Z coordinate

        Returns:
            True if the point is inside at least one enabled safe area
        """
        return len(self.areasContaining(dimension, x, z)) > 0

    def isInsideLocation(self, location) -> bool:
        """Check if a location is inside any enabled safe area.

        Args:
            location: Endstone Location object

        Returns:
            True if the location is inside at least one enabled safe area
        """
        try:
            return self.isInside(
                location.dimension.name,
                location.x,
                location.z,
            )
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────────
    # Player Enforcement
    # ──────────────────────────────────────────────────────────────────

    def shouldBypass(self, player: Player) -> bool:
        """Check if a player should bypass safe area gamemode enforcement.

        Bypass conditions:
        - Player has utilitystone.safearea.bypass permission
        - Player has utilitystone.admin permission
        - Player is OP

        Args:
            player: The player to check

        Returns:
            True if the player should bypass enforcement
        """
        if player.is_op:
            return True

        if player.has_permission("utilitystone.safearea.bypass"):
            return True

        if player.has_permission("utilitystone.admin"):
            return True

        # Check scoreboard tags
        bypassTag = self.plugin.settings.safeareasBypassTag
        if bypassTag and bypassTag in player.scoreboard_tags:
            return True

        return False

    def updatePlayerLocation(self, player: Player) -> None:
        """Update player's safe area state based on their current location.

        This is the central method for handling player movement, teleportation,
        and joining. All location changes should flow through here.

        Args:
            player: The player whose location changed
        """
        if self.shouldBypass(player):
            return

        location = player.location
        dimensionName = location.dimension.name
        x = location.x
        z = location.z

        playerKey = str(player.unique_id)
        state = self._playerStates.get(playerKey)

        currentAreas = self.areasContaining(dimensionName, x, z)
        currentAreaNames = {area["name"] for area in currentAreas}

        if state is None:
            # Player was not in any safe area
            if currentAreaNames:
                # Entering safe area(s) for the first time
                self._enterAreas(player, playerKey, currentAreaNames)
        else:
            # Player was in at least one safe area
            previousAreas = state.insideAreas

            newlyEntered = currentAreaNames - previousAreas
            leftAll = previousAreas - currentAreaNames

            if leftAll:
                if currentAreaNames:
                    # Left some areas but still in others
                    state.insideAreas = currentAreaNames
                else:
                    # Left all areas
                    self._leaveAllAreas(player, playerKey, state)
            elif newlyEntered:
                # Entered new areas while already in some
                state.insideAreas = currentAreaNames

    def _enterAreas(self, player: Player, playerKey: str, areaNames: set[str]) -> None:
        """Handle player entering safe area(s).

        Args:
            player: The player
            playerKey: The player's unique ID as string
            areaNames: Set of area names the player is entering
        """
        # Save current gamemode before forcing adventure
        previousGamemode = player.game_mode

        # Don't save if already in adventure (avoid overwrite)
        if previousGamemode == GameMode.ADVENTURE:
            # Check if we already have state (shouldn't happen, but safety)
            existingState = self._playerStates.get(playerKey)
            if existingState is not None:
                previousGamemode = existingState.previousGamemode

        state = PlayerState(previousGamemode)
        state.insideAreas = areaNames
        self._playerStates[playerKey] = state

        # Force adventure mode
        self._enforceAdventureMode(player, playerKey)

    def _leaveAllAreas(self, player: Player, playerKey: str, state: PlayerState) -> None:
        """Handle player leaving all safe areas.

        Args:
            player: The player
            playerKey: The player's unique ID as string
            state: The player's current state
        """
        # Restore previous gamemode
        self._restoreGamemode(player, playerKey, state)

    def _enforceAdventureMode(self, player: Player, playerKey: str) -> None:
        """Set player to adventure mode.

        Args:
            player: The player
            playerKey: The player's unique ID as string
        """
        if playerKey in self._enforcing:
            return  # Prevent recursion

        self._enforcing.add(playerKey)
        try:
            player.game_mode = GameMode.ADVENTURE
        finally:
            self._enforcing.discard(playerKey)

    def _restoreGamemode(self, player: Player, playerKey: str, state: PlayerState) -> None:
        """Restore player's original gamemode.

        Args:
            player: The player
            playerKey: The player's unique ID as string
            state: The player's state with saved gamemode
        """
        if playerKey in self._enforcing:
            return  # Prevent recursion

        self._enforcing.add(playerKey)
        try:
            player.game_mode = state.previousGamemode
        finally:
            self._enforcing.discard(playerKey)
            self._playerStates.pop(playerKey, None)

    def isEnforcing(self, playerKey: str) -> bool:
        """Check if we're currently enforcing gamemode for a player.

        Used to prevent recursion when PlayerGameModeChangeEvent fires
        from our own enforcement.

        Args:
            playerKey: The player's unique ID as string

        Returns:
            True if we're currently enforcing for this player
        """
        return playerKey in self._enforcing

    def isInsideAnyArea(self, player: Player) -> bool:
        """Check if a player is currently tracked as being inside safe areas.

        Args:
            player: The player to check

        Returns:
            True if the player is inside at least one safe area
        """
        playerKey = str(player.unique_id)
        state = self._playerStates.get(playerKey)
        return state is not None and len(state.insideAreas) > 0

    def getState(self, player: Player) -> PlayerState | None:
        """Get a player's safe area state.

        Args:
            player: The player

        Returns:
            PlayerState if the player is tracked, None otherwise
        """
        playerKey = str(player.unique_id)
        return self._playerStates.get(playerKey)

    # ──────────────────────────────────────────────────────────────────
    # Dangerous Entity Cleanup
    # ──────────────────────────────────────────────────────────────────

    def scanDangerousActors(self) -> int:
        """Scan for and remove dangerous actors inside safe areas.

        This is called periodically by the scheduled task.

        Returns:
            Number of actors removed
        """
        if not self.plugin.settings.safeareasEnabled:
            return 0

        removed = 0

        for dimensionType in self.plugin.server.level.dimensions:
            try:
                dimension = self.plugin.server.level.get_dimension(dimensionType.name)
                if dimension is None:
                    continue

                for actor in dimension.actors:
                    if not actor.is_valid:
                        continue

                    # Skip players
                    if isinstance(actor, Player):
                        continue

                    actorType = actor.type
                    if not isDangerousEntity(actorType):
                        continue

                    location = actor.location
                    if self.isInside(location.dimension.name, location.x, location.z):
                        try:
                            actor.remove()
                            removed += 1
                        except Exception:
                            pass  # Actor may have been removed by another thread
            except Exception:
                continue

        return removed

    # ──────────────────────────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────────────────────────

    def clearPlayerState(self, player: Player) -> None:
        """Clear a player's state (called on disconnect).

        Args:
            player: The player
        """
        playerKey = str(player.unique_id)
        self._playerStates.pop(playerKey, None)
        self._enforcing.discard(playerKey)

    def clearAll(self) -> None:
        """Clear all in-memory state.

        Called during plugin disable.
        """
        self._playerStates.clear()
        self._enforcing.clear()
