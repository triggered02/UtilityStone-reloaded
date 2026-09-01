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
            self.giveMenuItem(player)

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
        try:
            if not player.is_valid:
                return
        except Exception:
            return

        settings = self.plugin.settings
        itemType = settings.menuItemType
        displayName = settings.menuItemName
        lore = settings.menuItemLore

        if not itemType or not displayName:
            return

        inventory = player.inventory
        for slot in list(range(36)) + [36, 37, 38, 39, 40]:
            try:
                item = inventory.get_item(slot)
                if item is None:
                    continue
                if item.type != itemType:
                    continue
                meta = item.item_meta
                if meta is not None and meta.display_name == displayName:
                    return
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
        except Exception as exc:
            self.plugin.logger.warning(f"Could not give menu item to {player.name}: {exc}")

    def render(self, template: str, player) -> str:
        return colorize(template.replace("{name}", player.name))
