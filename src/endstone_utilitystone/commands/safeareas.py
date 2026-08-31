"""Safe area management commands.

Provides /safearea command with subcommands:
- set <name> <radius> - Create/update safe area at current location
- remove <name> - Delete a safe area
- list - List all safe areas
- info <name> - Show details of a safe area
- enable <name> - Enable a safe area
- disable <name> - Disable a safe area
"""

from __future__ import annotations

from endstone_utilitystone.commands.base import CommandGroup
from endstone_utilitystone.util.locations import describeLocation
from endstone_utilitystone.util.safearea_helpers import (
    isAcceptableAreaName,
    normalizeAreaName,
    validateRadius,
)


class SafeAreaCommands(CommandGroup):
    def bindings(self) -> dict:
        return {
            "safearea": self.route,
            "sa": self.route,
        }

    def route(self, sender, args: list) -> bool:
        player = self.asPlayer(sender)
        if player is None:
            return True

        if not args:
            self._showUsage(sender)
            return True

        sub = args[0].lower()
        subArgs = args[1:]

        if sub == "set":
            return self._setArea(sender, player, subArgs)
        elif sub == "remove" or sub == "delete":
            return self._removeArea(sender, subArgs)
        elif sub == "list" or sub == "ls":
            return self._listAreas(sender)
        elif sub == "info":
            return self._infoArea(sender, subArgs)
        elif sub == "enable":
            return self._enableArea(sender, subArgs, True)
        elif sub == "disable":
            return self._enableArea(sender, subArgs, False)
        else:
            self._showUsage(sender)
            return True

    def _showUsage(self, sender) -> None:
        self.messages.info(sender, "Safe Area Commands:")
        self.messages.info(sender, "/safearea set <name> <radius> - Create at your location")
        self.messages.info(sender, "/safearea remove <name> - Delete a safe area")
        self.messages.info(sender, "/safearea list - List all safe areas")
        self.messages.info(sender, "/safearea info <name> - View area details")
        self.messages.info(sender, "/safearea enable <name> - Enable an area")
        self.messages.info(sender, "/safearea disable <name> - Disable an area")

    def _setArea(self, sender, player, args: list) -> bool:
        if len(args) < 2:
            self.messages.failure(sender, "Usage: /safearea set <name> <radius>")
            return True

        name = args[0]
        radiusStr = args[1]

        # Validate name
        normalizedName = normalizeAreaName(name)
        if not isAcceptableAreaName(normalizedName):
            self.messages.failure(sender, "Invalid area name. Use only letters, numbers, underscores, and hyphens.")
            return True

        # Validate radius
        valid, errorMsg = validateRadius(radiusStr)
        if not valid:
            self.messages.failure(sender, errorMsg)
            return True

        radius = float(radiusStr)

        # Get player's current location
        location = player.location
        dimensionName = location.dimension.name
        centerX = location.x
        centerZ = location.z

        # Create the area
        success, message = self.plugin.safeareas.create(
            name=normalizedName,
            dimension=dimensionName,
            centerX=centerX,
            centerZ=centerZ,
            radius=radius,
            createdBy=player.name,
        )

        if success:
            self.messages.success(sender, message)
        else:
            self.messages.failure(sender, message)

        return True

    def _removeArea(self, sender, args: list) -> bool:
        if not args:
            self.messages.failure(sender, "Usage: /safearea remove <name>")
            return True

        name = args[0]
        success, message = self.plugin.safeareas.delete(name)

        if success:
            self.messages.success(sender, message)
        else:
            self.messages.failure(sender, message)

        return True

    def _listAreas(self, sender) -> bool:
        areas = self.plugin.safeareas.listAll()

        if not areas:
            self.messages.info(sender, "No safe areas have been created.")
            return True

        self.messages.info(sender, f"Safe Areas ({len(areas)}):")
        for area in areas:
            status = "ENABLED" if area.get("enabled", False) else "DISABLED"
            radius = area.get("radius", 0)
            self.messages.info(
                sender,
                f"  {area['name']} - {status} - Radius: {radius} - Dimension: {area.get('dimension', '?')}"
            )

        return True

    def _infoArea(self, sender, args: list) -> bool:
        if not args:
            self.messages.failure(sender, "Usage: /safearea info <name>")
            return True

        name = args[0]
        area = self.plugin.safeareas.get(name)

        if area is None:
            self.messages.failure(sender, f"No area named '{normalizeAreaName(name)}' exists.")
            return True

        status = "ENABLED" if area.get("enabled", False) else "DISABLED"
        self.messages.info(sender, f"Safe Area: {normalizeAreaName(name)}")
        self.messages.info(sender, f"  Status: {status}")
        self.messages.info(sender, f"  Dimension: {area.get('dimension', '?')}")
        self.messages.info(sender, f"  Center: X={area.get('centerX', 0):.1f}, Z={area.get('centerZ', 0):.1f}")
        self.messages.info(sender, f"  Radius: {area.get('radius', 0)}")
        self.messages.info(sender, f"  Created by: {area.get('createdBy', '?')}")

        return True

    def _enableArea(self, sender, args: list, enabled: bool) -> bool:
        if not args:
            action = "enable" if enabled else "disable"
            self.messages.failure(sender, f"Usage: /safearea {action} <name>")
            return True

        name = args[0]
        success, message = self.plugin.safeareas.setEnabled(name, enabled)

        if success:
            self.messages.success(sender, message)
        else:
            self.messages.failure(sender, message)

        return True
