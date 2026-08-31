"""Pure helper functions for Safe Area calculations.

These functions are separated from the service logic for easy testing
and to keep business logic testable without mocking Endstone APIs.
"""

import re

# Hostile mob type identifiers (Minecraft Bedrock Edition)
HOSTILE_MOBS = frozenset({
    # Zombie variants
    "minecraft:zombie",
    "minecraft:zombie_villager",
    "minecraft:husk",
    "minecraft:drowned",
    "minecraft:zombie_piglin",
    "minecraft:zombified_piglin",
    # Skeleton variants
    "minecraft:skeleton",
    "minecraft:stray",
    "minecraft:wither_skeleton",
    # Spider variants
    "minecraft:spider",
    "minecraft:cave_spider",
    # Creeper
    "minecraft:creeper",
    # Ender
    "minecraft:enderman",
    # Witch
    "minecraft:witch",
    # Slime variants
    "minecraft:slime",
    "minecraft:magma_cube",
    # Blaze
    "minecraft:blaze",
    # Ghast
    "minecraft:ghast",
    # Phantom
    "minecraft:phantom",
    # Guardian variants
    "minecraft:guardian",
    "minecraft:elder_guardian",
    # Pillager family
    "minecraft:pillager",
    "minecraft:vindicator",
    "minecraft:evoker",
    "minecraft:vex",
    "minecraft:ravager",
    # Hoglin variants
    "minecraft:hoglin",
    "minecraft:zoglin",
    # Piglin brute
    "minecraft:piglin_brute",
    # Shulker
    "minecraft:shulker",
    # Warden
    "minecraft:warden",
    # Breeze
    "minecraft:breeze",
    # Blaze (duplicate kept for clarity)
    "minecraft:blaze",
})

# Boss entities
DANGEROUS_BOSSES = frozenset({
    "minecraft:wither",
    "minecraft:ender_dragon",
})

# Explosive entities (TNT variants)
EXPLOSIVE_ENTITIES = frozenset({
    "minecraft:tnt",
    "minecraft:primed_tnt",
    "minecraft:bed",
    "minecraft:respawn_anchor",
})

# Combined set of all dangerous entities
ALL_DANGEROUS_ENTITIES = HOSTILE_MOBS | DANGEROUS_BOSSES | EXPLOSIVE_ENTITIES

# Valid area name pattern: alphanumeric, underscore, hyphen only
VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# Configuration constants
MAX_AREA_NAME_LENGTH = 32
MIN_RADIUS = 1
MAX_RADIUS = 10000


def isInsideCircle(x: float, z: float, centerX: float, centerZ: float, radius: float) -> bool:
    """Check if a point is inside a circle (inclusive of boundary).

    Uses squared distance to avoid expensive square root calculations.

    Args:
        x: Point X coordinate
        z: Point Z coordinate
        centerX: Circle center X
        centerZ: Circle center Z
        radius: Circle radius

    Returns:
        True if point is inside or on the boundary of the circle
    """
    dx = x - centerX
    dz = z - centerZ
    return (dx * dx + dz * dz) <= (radius * radius)


def isHostileMob(actorType: str) -> bool:
    """Check if an actor type is a hostile mob.

    Args:
        actorType: The actor's type string (e.g., "minecraft:zombie")

    Returns:
        True if the actor is a hostile mob
    """
    return actorType in HOSTILE_MOBS


def isDangerousBoss(actorType: str) -> bool:
    """Check if an actor type is a dangerous boss.

    Args:
        actorType: The actor's type string (e.g., "minecraft:wither")

    Returns:
        True if the actor is a dangerous boss
    """
    return actorType in DANGEROUS_BOSSES


def isExplosiveEntity(actorType: str) -> bool:
    """Check if an actor type is an explosive entity.

    Args:
        actorType: The actor's type string (e.g., "minecraft:tnt")

    Returns:
        True if the actor is an explosive entity
    """
    return actorType in EXPLOSIVE_ENTITIES


def isDangerousEntity(actorType: str) -> bool:
    """Check if an actor type is dangerous and should be removed from safe areas.

    Args:
        actorType: The actor's type string

    Returns:
        True if the actor is dangerous (hostile mob, boss, or explosive)
    """
    return actorType in ALL_DANGEROUS_ENTITIES


def shouldRemoveActor(actorType: str) -> bool:
    """Determine if an actor should be removed from a safe area.

    This is a convenience wrapper that checks if an entity is dangerous.
    Players are never removed (they're Player instances, not generic Actors).

    Args:
        actorType: The actor's type string

    Returns:
        True if the actor should be removed
    """
    return isDangerousEntity(actorType)


def isAcceptableAreaName(name: str) -> bool:
    """Validate a safe area name.

    Rules:
    - Must not be empty
    - Must not exceed MAX_AREA_NAME_LENGTH
    - Must only contain alphanumeric characters, underscores, or hyphens
    - Must not contain path traversal sequences

    Args:
        name: The area name to validate

    Returns:
        True if the name is valid
    """
    if not name or len(name) > MAX_AREA_NAME_LENGTH:
        return False

    # Reject path traversal
    if ".." in name or "/" in name or "\\" in name:
        return False

    return bool(VALID_NAME_PATTERN.match(name))


def normalizeAreaName(name: str) -> str:
    """Normalize an area name to lowercase and strip whitespace.

    Args:
        name: The area name to normalize

    Returns:
        Normalized lowercase name
    """
    return name.strip().lower()


def validateRadius(radius: float) -> tuple[bool, str]:
    """Validate a radius value.

    Args:
        radius: The radius to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    try:
        radius = float(radius)
    except (TypeError, ValueError):
        return False, "Radius must be a number."

    if radius < MIN_RADIUS:
        return False, f"Radius must be at least {MIN_RADIUS}."

    if radius > MAX_RADIUS:
        return False, f"Radius must be at most {MAX_RADIUS}."

    return True, ""
