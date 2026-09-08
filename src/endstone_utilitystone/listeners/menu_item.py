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

        from endstone_utilitystone.ui.permissions import hasPermission
        if not hasPermission(player, "utilitystone.command.menu"):
            return

        # Must match BOTH item type AND display name
        item_type_str = item.type.id if hasattr(item.type, "id") else str(item.type)
        target_type = settings.menuItemType
        target_type_full = target_type if ":" in target_type else f"minecraft:{target_type}"
        target_type_short = target_type.replace("minecraft:", "")

        if item_type_str not in (target_type, target_type_full, target_type_short) and str(item.type) != target_type:
            return

        meta = item.item_meta
        if meta is None or not meta.has_display_name or meta.display_name != settings.menuItemName:
            return

        event.cancel()

        if self.plugin.gui is None:
            self.plugin.messages.failure(player, "The menu system is not ready.")
            return

        self.plugin.gui.navigator.openPlayerMenu(player)
