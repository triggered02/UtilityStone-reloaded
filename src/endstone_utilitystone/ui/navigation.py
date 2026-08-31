from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from endstone_utilitystone.ui.manager import FormManager


class Navigator:
    def __init__(self, formManager: FormManager):
        self.fm = formManager

    def openPlayerMenu(self, player) -> bool:
        from endstone_utilitystone.ui.player_menu import openPlayerMenu
        return openPlayerMenu(self.fm.plugin, player)

    def openAdminPanel(self, player) -> bool:
        from endstone_utilitystone.ui.admin_menu import openAdminPanel
        return openAdminPanel(self.fm.plugin, player)

    def openConfigEditor(self, player) -> bool:
        from endstone_utilitystone.ui.config_menu import openConfigCategoryList
        return openConfigCategoryList(self.fm.plugin, player)
