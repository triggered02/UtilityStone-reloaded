from endstone.event import EventPriority, PlayerJoinEvent, PlayerQuitEvent, event_handler

from endstone_utilitystone.util.text import colorize

SUPPRESS_TOKENS = frozenset({"none", "off", "hidden", "silent"})


class ConnectionListener:
    def __init__(self, plugin):
        self.plugin = plugin

    @event_handler(priority=EventPriority.LOW)
    def onPlayerJoin(self, event: PlayerJoinEvent) -> None:
        player = event.player
        plugin = self.plugin

        session = plugin.sessions.open(player)
        plugin.profiles.recordJoin(player)

        # Apply rank permissions
        if plugin.ranks is not None:
            plugin.ranks.applyRank(player)

        template = plugin.settings.joinMessage
        if template:
            event.join_message = None if template.lower() in SUPPRESS_TOKENS else self.render(template, player)

        welcome = plugin.settings.welcomeMessage
        if welcome:
            player.send_message(colorize(welcome.replace("{name}", player.name)))

        if plugin.settings.spawnOnFirstJoin and plugin.spawns.markSeen(player):
            plugin.server.scheduler.run_task(plugin, lambda: self.sendToSpawn(player), delay=20)

        if plugin.settings.menuItemEnabled:
            giveMenuItem(self.plugin, player)

        plugin.discord.relayPresence(f"{player.name} joined the server.")
        session.touch()

    @event_handler(priority=EventPriority.LOW)
    def onPlayerQuit(self, event: PlayerQuitEvent) -> None:
        player = event.player
        plugin = self.plugin

        session = plugin.sessions.close(player)
        plugin.profiles.recordQuit(player, session)
        plugin.teleports.forget(player)
        plugin.godPlayers.discard(player.unique_id)

        if plugin.gui is not None:
            plugin.gui.onPlayerQuit(player)

        plugin.discord.relayPresence(f"{player.name} left the server.")

        template = plugin.settings.quitMessage
        if template:
            event.quit_message = None if template.lower() in SUPPRESS_TOKENS else self.render(template, player)

    def sendToSpawn(self, player) -> None:
        try:
            if not player.is_valid:
                return
        except Exception:
            return

        destination = self.plugin.spawns.resolve()
        if destination is not None:
            player.teleport(destination)

    def giveMenuItem(self, player) -> None:
        giveMenuItem(self.plugin, player)

    def render(self, template: str, player) -> str:
        return colorize(template.replace("{name}", player.name))


def giveMenuItem(plugin, player, force: bool = False) -> bool:
    try:
        if not player.is_valid:
            return False
    except Exception:
        return False

    settings = plugin.settings
    itemType = settings.menuItemType
    displayName = settings.menuItemName
    lore = settings.menuItemLore

    if not itemType or not displayName:
        return False

    inventory = player.inventory
    valid_names = {displayName, "Server Menu", "UtilityStone Menu"}

    # If not forced, check if player already has the exact menu item
    if not force:
        for slot in range(len(inventory)):
            try:
                item = inventory.get_item(slot)
                if item is None:
                    continue
                if item.type != itemType:
                    item_type_str = item.type.id if hasattr(item.type, "id") else str(item.type)
                    if item_type_str != itemType and item_type_str != f"minecraft:{itemType}":
                        continue
                meta = item.item_meta
                if meta is not None and meta.has_display_name and meta.display_name in valid_names:
                    return True
            except Exception:
                continue

    # Remove any old written_book menu items so player is upgraded from book to compass
    for slot in range(len(inventory)):
        try:
            item = inventory.get_item(slot)
            if item is None:
                continue
            item_type_str = item.type.id if hasattr(item.type, "id") else str(item.type)
            if "written_book" in item_type_str:
                meta = item.item_meta
                if meta is not None and meta.has_display_name and meta.display_name in valid_names:
                    inventory.clear(slot)
        except Exception:
            continue

    from endstone.inventory import ItemStack

    try:
        stack = ItemStack(itemType, 1)
        meta = stack.item_meta
        if meta is not None:
            meta.display_name = displayName
            if lore:
                meta.lore = [lore]
            stack.set_item_meta(meta)

        slot = min(max(0, settings.menuItemSlot), 35)
        existing = inventory.get_item(slot)
        if existing is not None:
            overflow = inventory.add_item(stack)
            if overflow:
                for s in overflow.values():
                    dimension = player.location.dimension
                    dimension.drop_item(player.location, s)
        else:
            inventory.set_item(slot, stack)
        return True
    except Exception as exc:
        plugin.logger.warning(f"Could not give menu item to {player.name}: {exc}")
        return False
