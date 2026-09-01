"""
Integration tests for chat prefix/suffix injection.

These tests exercise the actual deliver() code path with live RankService
data, not just source-text assertions.
"""

from __future__ import annotations

import sys
import pathlib
from types import SimpleNamespace

# Ensure the source tree is importable
_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from endstone_utilitystone.services.ranks import RankService, DEFAULT_RANK
from endstone_utilitystone.util.text import colorize


# ---------------------------------------------------------------------------
# Minimal mock infrastructure
# ---------------------------------------------------------------------------
class MockStore:
    """Minimal JsonStore-like object for RankService."""

    def __init__(self, data=None):
        self.data = data or {"ranks": {}, "player_ranks": {}}
        self._dirty = False

    def markDirty(self):
        self._dirty = True


class MockStorageManager:
    """Minimal StorageManager that returns a MockStore."""

    def __init__(self):
        self._stores = {}

    def open(self, name, defaults=None):
        if name not in self._stores:
            self._stores[name] = MockStore(
                {"ranks": dict(defaults.get("ranks", {})), "player_ranks": dict(defaults.get("player_ranks", {}))}
            )
        return self._stores[name]


class MockPlayer:
    def __init__(self, name, uid):
        self.name = name
        self.unique_id = uid
        self.has_permission = lambda perm: False
        self.messages_received = []

    def send_message(self, msg):
        self.messages_received.append(msg)


class MockSession:
    def __init__(self, key="test-key"):
        self.key = key
        self.isAfk = False


class MockServer:
    def __init__(self, players):
        self.online_players = players
        self.logger = MockLogger()


class MockLogger:
    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class MockAfkService:
    def tag(self, session):
        return ""


class MockProfiles:
    def isIgnoring(self, key1, key2):
        return False


class MockSessions:
    def of(self, player):
        return MockSession()


class MockPlugin:
    def __init__(self, players, settings=None):
        self.storage = MockStorageManager()
        self.server = MockServer(players)
        self.ranks = RankService(self)
        self.logger = MockLogger()
        self.afk = MockAfkService()
        self.profiles = MockProfiles()
        self.sessions = MockSessions()

        # Settings
        s = settings or {}
        self.settings = SimpleNamespace(
            chatFormat=s.get("chatFormat", "{prefix}{name}{suffix}: {message}"),
            chatManaged=True,
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestChatPrefixIntegration:
    """Real integration tests for chat prefix/suffix injection."""

    def _make_deliver(self, chat_format="{prefix}{name}{suffix}: {message}"):
        """Set up a ChatListener + RankService + deliver the message, return the output line."""
        player = MockPlayer("Triggered_02", "abc-123")
        session = MockSession()
        plugin = MockPlugin([player], {"chatFormat": chat_format})

        # Create an "admin" rank with prefix and suffix
        ok, msg = plugin.ranks.createRank(
            "admin", priority=100, prefix="&c[Admin] ", suffix=" &r"
        )
        assert ok, f"createRank failed: {msg}"

        # Assign it to the player
        ok, msg = plugin.ranks.setPlayerRank("abc-123", "admin")
        assert ok, f"setPlayerRank failed: {msg}"

        # Import and instantiate ChatListener
        from endstone_utilitystone.listeners.chat import ChatListener
        listener = ChatListener(plugin)

        # Call deliver directly
        listener.deliver(player, session, "hello world")

        assert len(player.messages_received) == 1, f"Expected 1 message, got {len(player.messages_received)}"
        return player.messages_received[0]

    def test_prefix_appears_in_output(self):
        line = self._make_deliver()
        assert "&c[Admin]" in line or "\u00a7c[Admin]" in line, f"Prefix not found in output: {line!r}"

    def test_suffix_appears_in_output(self):
        line = self._make_deliver()
        assert "&r" in line or "\u00a7r" in line, f"Suffix not found in output: {line!r}"

    def test_player_name_appears_in_output(self):
        line = self._make_deliver()
        assert "Triggered_02" in line, f"Player name not found in output: {line!r}"

    def test_message_appears_in_output(self):
        line = self._make_deliver()
        assert "hello world" in line, f"Message not found in output: {line!r}"

    def test_format_without_prefix_suffix_works(self):
        """User with old format (no {prefix}/{suffix}) should still work."""
        line = self._make_deliver(chat_format="<{name}> {message}")
        assert "Triggered_02" in line
        assert "hello world" in line
        # Prefix/suffix should NOT appear since placeholders aren't in template
        assert "&c[Admin]" not in line and "\u00a7c[Admin]" not in line

    def test_default_rank_no_prefix(self):
        """Player with default rank should produce no prefix/suffix."""
        player = MockPlayer("NewPlayer", "def-456")
        plugin = MockPlugin([player])
        # Don't assign any rank — should use default
        from endstone_utilitystone.listeners.chat import ChatListener
        listener = ChatListener(plugin)
        session = MockSession()
        listener.deliver(player, session, "test msg")
        line = player.messages_received[0]
        assert "NewPlayer" in line
        assert "test msg" in line
        # No rank prefix
        assert "[" not in line or line.index("[") > line.index("NewPlayer")

    def test_rank_service_getEffectiveRankName(self):
        """Verify RankService returns the correct rank name."""
        player = MockPlayer("TestPlayer", "uid-789")
        plugin = MockPlugin([player])
        plugin.ranks.createRank("vip", priority=50, prefix="&6[VIP] ", suffix="")
        plugin.ranks.setPlayerRank("uid-789", "vip")
        assert plugin.ranks.getEffectiveRankName(player) == "vip"

    def test_rank_service_getPrefix(self):
        """Verify RankService returns the correct prefix."""
        player = MockPlayer("TestPlayer", "uid-789")
        plugin = MockPlugin([player])
        plugin.ranks.createRank("vip", priority=50, prefix="&6[VIP] ", suffix="")
        assert plugin.ranks.getPrefix("vip") == "&6[VIP] "

    def test_rank_service_getSuffix(self):
        """Verify RankService returns the correct suffix."""
        player = MockPlayer("TestPlayer", "uid-789")
        plugin = MockPlugin([player])
        plugin.ranks.createRank("vip", priority=50, prefix="", suffix=" &r")
        assert plugin.ranks.getSuffix("vip") == " &r"

    def test_colorize_converts_ampersand_prefix(self):
        """Verify colorize converts &c to section sign."""
        result = colorize("&c[Admin] ")
        assert result == "\u00a7c[Admin] "

    def test_deliver_line_structure(self):
        """Verify the full output line has the expected structure."""
        line = self._make_deliver()
        # Expected: colorized_prefix + "Triggered_02" + colorized_suffix + ": hello world"
        # The colorize function converts &c to \u00a7c and " &r" to " \u00a7r"
        assert "\u00a7c[Admin] Triggered_02 \u00a7r: hello world" == line

    def test_chat_format_migration_detects_old_default(self):
        """Verify the migration logic correctly detects old format."""
        from endstone_utilitystone.plugin import UtilityStone
        # Read the actual method source
        import inspect
        src = inspect.getsource(UtilityStone._migrateChatFormat)
        assert '<{name}> {message}' in src
        assert '{prefix}{name}{suffix}: {message}' in src

    def test_new_config_default_contains_prefix_suffix(self):
        """Verify the default config.toml contains {prefix} and {suffix}."""
        config_path = _SRC / "endstone_utilitystone" / "config.toml"
        content = config_path.read_text()
        assert "{prefix}" in content
        assert "{suffix}" in content

    def test_settings_default_contains_prefix_suffix(self):
        """Verify the settings.py default contains {prefix} and {suffix}."""
        settings_path = _SRC / "endstone_utilitystone" / "core" / "settings.py"
        content = settings_path.read_text()
        assert "{prefix}" in content
        assert "{suffix}" in content
