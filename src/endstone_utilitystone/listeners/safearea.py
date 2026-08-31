"""Safe Area event listener.

Handles:
- Player movement/teleportation for gamemode enforcement
- Actor spawn prevention for hostile mobs
- Block placement prevention for TNT
- Explosion cancellation
- Block break prevention
- Gamemode change prevention
"""

from __future__ import annotations

from endstone.actor import Actor
from endstone import GameMode, Player
from endstone.event import (
    ActorDamageEvent,
    ActorExplodeEvent,
    ActorSpawnEvent,
    BlockBreakEvent,
    BlockExplodeEvent,
    BlockPlaceEvent,
    EventPriority,
    PlayerGameModeChangeEvent,
    PlayerJoinEvent,
    PlayerMoveEvent,
    PlayerQuitEvent,
    PlayerTeleportEvent,
    event_handler,
)

from endstone_utilitystone.util.safearea_helpers import (
    EXPLOSIVE_ENTITIES,
    isDangerousEntity,
    isExplosiveEntity,
)


class SafeAreaListener:
    """Listens for events related to safe area enforcement."""

    def __init__(self, plugin) -> None:
        self.plugin = plugin

    @property
    def safeareas(self):
        return self.plugin.safeareas

    # ──────────────────────────────────────────────────────────────────
    # Player Movement / Teleportation
    # ──────────────────────────────────────────────────────────────────

    @event_handler(priority=EventPriority.LOW)
    def onPlayerMove(self, event: PlayerMoveEvent) -> None:
        """Handle player movement for safe area detection."""
        if not self.plugin.settings.safeareasEnabled:
            return

        self.safeareas.updatePlayerLocation(event.player)

    @event_handler(priority=EventPriority.LOW)
    def onPlayerTeleport(self, event: PlayerTeleportEvent) -> None:
        """Handle player teleportation for safe area detection."""
        if not self.plugin.settings.safeareasEnabled:
            return

        self.safeareas.updatePlayerLocation(event.player)

    # ──────────────────────────────────────────────────────────────────
    # Player Join / Quit
    # ──────────────────────────────────────────────────────────────────

    @event_handler(priority=EventPriority.NORMAL)
    def onPlayerJoin(self, event: PlayerJoinEvent) -> None:
        """Handle player joining to check if they're inside a safe area."""
        if not self.plugin.settings.safeareasEnabled:
            return

        # Small delay to ensure player location is set
        self.plugin.server.scheduler.run_task(
            self.plugin,
            lambda: self.safeareas.updatePlayerLocation(event.player),
            delay=5,
        )

    @event_handler(priority=EventPriority.NORMAL)
    def onPlayerQuit(self, event: PlayerQuitEvent) -> None:
        """Handle player quitting to clean up state."""
        if not self.plugin.settings.safeareasEnabled:
            return

        self.safeareas.clearPlayerState(event.player)

    # ──────────────────────────────────────────────────────────────────
    # Actor Spawn Prevention
    # ──────────────────────────────────────────────────────────────────

    @event_handler(priority=EventPriority.HIGHEST)
    def onActorSpawn(self, event: ActorSpawnEvent) -> None:
        """Prevent hostile mobs from spawning inside safe areas."""
        if not self.plugin.settings.safeareasEnabled:
            return

        actor = event.actor

        # Skip players
        if isinstance(actor, Player):
            return

        actorType = actor.type
        if not isDangerousEntity(actorType):
            return

        location = actor.location
        if self.safeareas.isInside(location.dimension.name, location.x, location.z):
            event.cancel()

    # ──────────────────────────────────────────────────────────────────
    # Block Place Prevention (TNT)
    # ──────────────────────────────────────────────────────────────────

    @event_handler(priority=EventPriority.HIGHEST)
    def onBlockPlace(self, event: BlockPlaceEvent) -> None:
        """Prevent TNT placement inside safe areas."""
        if not self.plugin.settings.safeareasEnabled:
            return

        block = event.block
        blockType = block.type

        # Block type is a string like "minecraft:tnt"
        if blockType != "minecraft:tnt":
            return

        location = block.location
        if self.safeareas.isInside(location.dimension.name, location.x, location.z):
            event.cancel()
            if isinstance(event.player, Player):
                self.plugin.messages.failure(
                    event.player,
                    "You cannot place TNT in a safe area."
                )

    # ──────────────────────────────────────────────────────────────────
    # Explosion Prevention
    # ──────────────────────────────────────────────────────────────────

    @event_handler(priority=EventPriority.HIGHEST)
    def onBlockExplode(self, event: BlockExplodeEvent) -> None:
        """Cancel explosions inside safe areas."""
        if not self.plugin.settings.safeareasEnabled:
            return

        location = event.block.location
        if self.safeareas.isInside(location.dimension.name, location.x, location.z):
            event.cancel()

    @event_handler(priority=EventPriority.HIGHEST)
    def onActorExplode(self, event: ActorExplodeEvent) -> None:
        """Cancel actor-caused explosions inside safe areas."""
        if not self.plugin.settings.safeareasEnabled:
            return

        location = event.location
        if self.safeareas.isInside(location.dimension.name, location.x, location.z):
            event.cancel()

    # ──────────────────────────────────────────────────────────────────
    # Block Break Prevention
    # ──────────────────────────────────────────────────────────────────

    @event_handler(priority=EventPriority.HIGHEST)
    def onBlockBreak(self, event: BlockBreakEvent) -> None:
        """Prevent block breaking inside safe areas for non-bypass players."""
        if not self.plugin.settings.safeareasEnabled:
            return

        player = event.player
        if not isinstance(player, Player):
            return

        # Bypass players can break blocks
        if self.safeareas.shouldBypass(player):
            return

        location = event.block.location
        if self.safeareas.isInside(location.dimension.name, location.x, location.z):
            event.cancel()

    # ──────────────────────────────────────────────────────────────────
    # Gamemode Change Prevention
    # ──────────────────────────────────────────────────────────────────

    @event_handler(priority=EventPriority.HIGHEST)
    def onPlayerGameModeChange(self, event: PlayerGameModeChangeEvent) -> None:
        """Prevent non-bypass players from changing gamemode inside safe areas."""
        if not self.plugin.settings.safeareasEnabled:
            return

        player = event.player
        if not isinstance(player, Player):
            return

        playerKey = str(player.unique_id)

        # If we're enforcing gamemode, don't block our own changes
        if self.safeareas.isEnforcing(playerKey):
            return

        # Bypass players can change gamemode freely
        if self.safeareas.shouldBypass(player):
            return

        # Check if player is inside any safe area
        if self.safeareas.isInsideAnyArea(player):
            # Allow changing TO adventure mode (our enforcement)
            if event.new_game_mode != GameMode.ADVENTURE:
                event.cancel()
