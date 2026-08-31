from endstone_utilitystone.util.player_actions import healPlayer, feedPlayer, toggleFlight, toggleGod


class FakePlayer:
    def __init__(self, name="TestPlayer", health=10, max_health=20, uid="uid-1"):
        self.name = name
        self.health = health
        self.max_health = max_health
        self.unique_id = uid
        self.allow_flight = False
        self.is_flying = False
        self._messages = []

    def send_message(self, msg):
        self._messages.append(msg)


class FakeMessages:
    def success(self, target, msg):
        target._messages.append(f"[SUCCESS] {msg}")

    def failure(self, target, msg):
        target._messages.append(f"[FAILURE] {msg}")


class FakeServer:
    def __init__(self):
        self.command_sender = FakePlayer("Console")
        self._commands = []

    def dispatch_command(self, sender, cmd):
        self._commands.append(cmd)


class FakePlugin:
    def __init__(self):
        self.messages = FakeMessages()
        self.server = FakeServer()
        self.godPlayers = set()
        self.logger = type("Logger", (), {"warning": lambda s, m: None})()
        self.gui = type("GUI", (), {"untrack": lambda s, p: None})()


class TestHealPlayer:
    def test_heals_self(self):
        plugin = FakePlugin()
        player = FakePlayer(health=5, max_health=20)
        healPlayer(plugin, player, None)
        assert player.health == 20
        assert "healed" in player._messages[0].lower()

    def test_heals_other(self):
        plugin = FakePlugin()
        sender = FakePlayer("Admin", uid="uid-admin")
        target = FakePlayer("Victim", health=5, max_health=20, uid="uid-victim")
        healPlayer(plugin, target, sender)
        assert target.health == 20
        assert any("Victim" in m for m in sender._messages)

    def test_heals_same_no_double_message(self):
        plugin = FakePlugin()
        player = FakePlayer("Solo", health=5, max_health=20, uid="uid-1")
        healPlayer(plugin, player, player)
        assert player.health == 20
        assert len(player._messages) == 1


class TestFeedPlayer:
    def test_dispatches_effect(self):
        plugin = FakePlugin()
        player = FakePlayer()
        feedPlayer(plugin, player, None)
        assert len(plugin.server._commands) == 1
        assert "saturation" in plugin.server._commands[0]

    def test_messages_target(self):
        plugin = FakePlugin()
        player = FakePlayer()
        feedPlayer(plugin, player, None)
        assert any("hunger" in m.lower() for m in player._messages)


class TestToggleFlight:
    def test_enable(self):
        plugin = FakePlugin()
        player = FakePlayer()
        result = toggleFlight(plugin, player, None)
        assert result is True
        assert player.allow_flight is True

    def test_disable(self):
        plugin = FakePlugin()
        player = FakePlayer()
        player.allow_flight = True
        result = toggleFlight(plugin, player, None)
        assert result is False
        assert player.allow_flight is False
        assert player.is_flying is False

    def test_disable_stops_flying(self):
        plugin = FakePlugin()
        player = FakePlayer()
        player.allow_flight = True
        player.is_flying = True
        toggleFlight(plugin, player, None)
        assert player.is_flying is False

    def test_other_message(self):
        plugin = FakePlugin()
        sender = FakePlayer("Admin", uid="uid-admin")
        target = FakePlayer("Victim", uid="uid-victim")
        toggleFlight(plugin, target, sender)
        assert any("flight" in m.lower() for m in sender._messages)


class TestToggleGod:
    def test_enable(self):
        plugin = FakePlugin()
        player = FakePlayer(uid="uid-1")
        result = toggleGod(plugin, player, None)
        assert result is True
        assert "uid-1" in plugin.godPlayers

    def test_disable(self):
        plugin = FakePlugin()
        player = FakePlayer(uid="uid-1")
        plugin.godPlayers.add("uid-1")
        result = toggleGod(plugin, player, None)
        assert result is False
        assert "uid-1" not in plugin.godPlayers

    def test_other_message(self):
        plugin = FakePlugin()
        sender = FakePlayer("Admin", uid="uid-admin")
        target = FakePlayer("Victim", uid="uid-victim")
        toggleGod(plugin, target, sender)
        assert any("god" in m.lower() for m in sender._messages)
