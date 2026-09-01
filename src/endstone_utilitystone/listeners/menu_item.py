from endstone.event import EventPriority, PlayerInteractEvent, event_handler


class MenuItemListener:
    def __init__(self, plugin):
        self.plugin = plugin

    @event_handler(priority=EventPriority.LOW)
    def onPlayerInteract(self, event: PlayerInteractEvent) -> None:
        settings = self.plugin.settings
        if not settings.menuItemEnabled:
            return

        if not event.has_item:
            return

        action = event.action
        if action != PlayerInteractEvent.Action.RIGHT_CLICK_AIR and action != PlayerInteractEvent.Action.RIGHT_CLICK_BLOCK:
            return

        player = event.player
        item = event.item

        if item is None:
            return

        # Must match BOTH item type AND display name
        if item.type != settings.menuItemType:
            return

        meta = item.item_meta
        if meta is None:
            return

        if meta.display_name != settings.menuItemName:
            return

        event.cancel()

        if self.plugin.gui is None:
            self.plugin.messages.failure(player, "The menu system is not ready.")
            return

        self.plugin.gui.navigator.openPlayerMenu(player)
