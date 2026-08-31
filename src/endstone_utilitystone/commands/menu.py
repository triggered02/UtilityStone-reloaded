from __future__ import annotations

from endstone import Player

from endstone_utilitystone.commands.base import CommandGroup
from endstone_utilitystone.ui.permissions import hasAdminGui, hasPlayerGui


class MenuCommands(CommandGroup):
    def bindings(self) -> dict:
        return {
            "menu": self.openMenu,
        }

    def openMenu(self, sender, args: list) -> bool:
        if not isinstance(sender, Player):
            self.messages.failure(sender, "Only a player in game can use that command.")
            return True

        if self.plugin.gui is None:
            self.messages.failure(sender, "The GUI system is not ready.")
            return True

        action = args[0].lower() if args else ""

        if action == "admin":
            if not hasAdminGui(sender):
                self.messages.failure(sender, "You do not have permission to access the admin panel.")
                return True
            self.plugin.gui.navigator.openAdminPanel(sender)
            return True

        self.plugin.gui.navigator.openPlayerMenu(sender)
        return True
