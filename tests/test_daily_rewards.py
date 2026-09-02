"""
Comprehensive tests for the Daily Rewards system.

Covers the service, reward execution, milestone selection, admin controls,
player GUI wiring, permissions, settings parsing, commands, and plugin
integration.  Uses a mix of source-code structural assertions (matching the
project's other test modules) and runtime behavior tests with mock plugins.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

# Ensure the source tree is importable (mirrors test_chat_integration.py)
_SRC_PATH = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

_SRC = _SRC_PATH / "endstone_utilitystone"
_SERVICE_SRC = (_SRC / "services" / "daily_rewards.py").read_text()
_CMD_SRC = (_SRC / "commands" / "daily_rewards.py").read_text()
_UI_SRC = (_SRC / "ui" / "daily_rewards.py").read_text()
_PLUGIN_SRC = (_SRC / "plugin.py").read_text()
_PLAYER_MENU_SRC = (_SRC / "ui" / "player_menu.py").read_text()
_ADMIN_MENU_SRC = (_SRC / "ui" / "admin_menu.py").read_text()
_PLAYER_TOOLS_SRC = (_SRC / "ui" / "admin_player_tools.py").read_text()
_CONFIG_TOML = (_SRC / "config.toml").read_text()
_SETTINGS_SRC = (_SRC / "core" / "settings.py").read_text()
_CONFIG_MENU_SRC = (_SRC / "ui" / "config_menu.py").read_text()

from endstone_utilitystone.services.daily_rewards import DailyRewardsService  # noqa: E402


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------
class MockStore:
    def __init__(self, data=None):
        self.data = data or {"players": {}}
        self._dirty = False

    def markDirty(self):
        self._dirty = True


class MockStorageManager:
    def __init__(self, store=None):
        self._store = store or MockStore()

    def open(self, name, defaults=None):
        return self._store


class MockLogger:
    def __init__(self):
        self.warnings = []

    def info(self, msg):
        pass

    def warning(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        pass


class MockSettings:
    def __init__(self, enabled=True, rewards=None):
        self.dailyRewardsEnabled = enabled
        self.dailyRewardsRewards = rewards if rewards is not None else {
            1: ["give {player} iron_ingot 5"],
            3: ["give {player} diamond 1"],
            7: ["give {player} emerald 5"],
            30: ["give {player} diamond_block 1"],
        }


class MockPlayer:
    def __init__(self, name="Steve", uid="abc-123"):
        self.name = name
        self.unique_id = uid


class MockServer:
    def __init__(self, fail_commands=False):
        self.command_sender = "console"
        self.dispatched = []
        self.online_players = []
        self._fail = fail_commands

    def dispatch_command(self, sender, cmd):
        self.dispatched.append((sender, cmd))
        if self._fail:
            raise RuntimeError("command failed")


class MockMessages:
    def __init__(self):
        self.out = []

    def success(self, player, text):
        self.out.append(("success", getattr(player, "name", "?"), text))

    def failure(self, player, text):
        self.out.append(("failure", getattr(player, "name", "?"), text))

    def notice(self, player, text):
        self.out.append(("notice", getattr(player, "name", "?"), text))

    def info(self, player, text):
        self.out.append(("info", getattr(player, "name", "?"), text))


class MockPlugin:
    def __init__(self, enabled=True, rewards=None, fail_commands=False):
        self.store = MockStore({"players": {}})
        self.storage = MockStorageManager(self.store)
        self.server = MockServer(fail_commands=fail_commands)
        self.logger = MockLogger()
        self.messages = MockMessages()
        self.settings = MockSettings(enabled=enabled, rewards=rewards)
        self.dailyRewards = DailyRewardsService(self)

    def set_today(self, date):
        self.dailyRewards._today = staticmethod(lambda: date)


# ---------------------------------------------------------------------------
# Service structure
# ---------------------------------------------------------------------------
class TestDailyRewardsServiceStructure:
    def test_service_class_exists(self):
        assert "class DailyRewardsService:" in _SERVICE_SRC

    def test_uses_storage_manager(self):
        assert 'plugin.storage.open("daily_rewards"' in _SERVICE_SRC

    def test_has_players_dict(self):
        assert '"players"' in _SERVICE_SRC

    def test_marks_dirty(self):
        assert "self.store.markDirty()" in _SERVICE_SRC

    def test_camel_case_methods(self):
        for method in (
            "def canClaim(",
            "def getPlayerState(",
            "def getMilestoneReward(",
            "def describeReward(",
            "def nextClaimDate(",
            "def resetStreak(",
            "def clearHistory(",
            "def timeUntilNextClaim(",
            "def isEnabled(",
        ):
            assert method in _SERVICE_SRC, f"Missing method {method}"


# ---------------------------------------------------------------------------
# First claim / basic behavior
# ---------------------------------------------------------------------------
class TestBasicClaim:
    def test_first_claim(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        ok, _ = plugin.dailyRewards.claim(player)
        assert ok is True
        state = plugin.dailyRewards.getPlayerState(str(player.unique_id))
        assert state["streak"] == 1
        assert state["total_claims"] == 1
        assert state["last_claim"] == "2026-09-01"

    def test_duplicate_same_day_denied(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        assert plugin.dailyRewards.claim(player)[0] is True
        ok, msg = plugin.dailyRewards.claim(player)
        assert ok is False
        assert "already claimed" in msg.lower()

    def test_next_day_increments_streak(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        plugin.set_today(datetime.date(2026, 9, 2))
        ok, _ = plugin.dailyRewards.claim(player)
        assert ok is True
        assert plugin.dailyRewards.getPlayerState(str(player.unique_id))["streak"] == 2

    def test_missed_day_resets_streak(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        plugin.set_today(datetime.date(2026, 9, 3))  # skipped Sep 2
        plugin.dailyRewards.claim(player)
        assert plugin.dailyRewards.getPlayerState(str(player.unique_id))["streak"] == 1

    def test_multiple_missed_days_reset_streak(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        plugin.set_today(datetime.date(2026, 9, 10))
        plugin.dailyRewards.claim(player)
        assert plugin.dailyRewards.getPlayerState(str(player.unique_id))["streak"] == 1

    def test_total_claims_increment(self):
        plugin = MockPlugin()
        player = MockPlayer()
        for day in (1, 2, 3):
            plugin.set_today(datetime.date(2026, 9, day))
            plugin.dailyRewards.claim(player)
        assert plugin.dailyRewards.getPlayerState(str(player.unique_id))["total_claims"] == 3

    def test_disabled_system_denies(self):
        plugin = MockPlugin(enabled=False)
        player = MockPlayer()
        ok, msg = plugin.dailyRewards.claim(player)
        assert ok is False
        assert "disabled" in msg.lower()

    def test_can_claim_false_when_disabled(self):
        plugin = MockPlugin(enabled=False)
        assert plugin.dailyRewards.canClaim("abc-123") is False


# ---------------------------------------------------------------------------
# Eligibility / next claim date
# ---------------------------------------------------------------------------
class TestEligibility:
    def test_can_claim_true_fresh(self):
        plugin = MockPlugin()
        assert plugin.dailyRewards.canClaim("abc-123") is True

    def test_can_claim_false_same_day(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        assert plugin.dailyRewards.canClaim(str(player.unique_id)) is False

    def test_can_claim_true_next_day(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        plugin.set_today(datetime.date(2026, 9, 2))
        assert plugin.dailyRewards.canClaim(str(player.unique_id)) is True

    def test_next_claim_date_after_claim(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        assert plugin.dailyRewards.nextClaimDate(str(player.unique_id)) == "2026-09-02"

    def test_time_until_next_claim_zero_when_claimable(self):
        plugin = MockPlugin()
        assert plugin.dailyRewards.timeUntilNextClaim("abc-123") == 0.0


# ---------------------------------------------------------------------------
# Milestone / reward selection
# ---------------------------------------------------------------------------
class TestMilestoneSelection:
    REWARDS = {
        1: ["give {player} iron_ingot 5"],
        3: ["give {player} diamond 1"],
        7: ["give {player} emerald 5"],
        30: ["give {player} diamond_block 1"],
    }

    def test_exact_milestone(self):
        plugin = MockPlugin(rewards=self.REWARDS)
        assert plugin.dailyRewards.getMilestoneReward(3) == ["give {player} diamond 1"]

    def test_between_milestones(self):
        plugin = MockPlugin(rewards=self.REWARDS)
        # Streak 2 -> highest milestone <= 2 is day 1
        assert plugin.dailyRewards.getMilestoneReward(2) == ["give {player} iron_ingot 5"]

    def test_above_highest_milestone(self):
        plugin = MockPlugin(rewards=self.REWARDS)
        # Streak 31 -> day 30
        assert plugin.dailyRewards.getMilestoneReward(31) == ["give {player} diamond_block 1"]

    def test_below_lowest_milestone(self):
        plugin = MockPlugin(rewards={3: ["give {player} diamond 1"]})
        assert plugin.dailyRewards.getMilestoneReward(1) == []

    def test_no_rewards_configured(self):
        plugin = MockPlugin(rewards={})
        assert plugin.dailyRewards.getMilestoneReward(1) == []

    def test_claim_with_no_milestone_still_succeeds(self):
        plugin = MockPlugin(rewards={})
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        ok, msg = plugin.dailyRewards.claim(player)
        assert ok is True
        assert "reward" in msg.lower()


# ---------------------------------------------------------------------------
# Reward execution
# ---------------------------------------------------------------------------
class TestRewardExecution:
    def test_placeholder_replaced(self):
        plugin = MockPlugin()
        player = MockPlayer(name="AntiCreeper")
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        assert plugin.server.dispatched[0][1] == "give AntiCreeper iron_ingot 5"

    def test_called_from_console(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        assert plugin.server.dispatched[0][0] == "console"

    def test_multiple_commands(self):
        plugin = MockPlugin(rewards={
            1: ["give {player} iron_ingot 5", "money add {player} 100"],
        })
        player = MockPlayer(name="Steve")
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        cmds = [c for _, c in plugin.server.dispatched]
        assert cmds == ["give Steve iron_ingot 5", "money add Steve 100"]

    def test_command_failure_logged_but_claim_consumed(self):
        plugin = MockPlugin(fail_commands=True)
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        ok, msg = plugin.dailyRewards.claim(player)
        assert ok is True
        state = plugin.dailyRewards.getPlayerState(str(player.unique_id))
        assert state["last_claim"] == "2026-09-01"
        assert len(plugin.logger.warnings) >= 1

    def test_no_duplicate_execution(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        first_count = len(plugin.server.dispatched)
        plugin.dailyRewards.claim(player)  # denied
        assert len(plugin.server.dispatched) == first_count


# ---------------------------------------------------------------------------
# Admin operations
# ---------------------------------------------------------------------------
class TestAdminOperations:
    def test_reset_streak(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        ok, _ = plugin.dailyRewards.resetStreak(str(player.unique_id))
        assert ok is True
        state = plugin.dailyRewards.getPlayerState(str(player.unique_id))
        assert state["streak"] == 0
        assert state["total_claims"] == 1  # history preserved

    def test_reset_streak_no_data(self):
        plugin = MockPlugin()
        ok, _ = plugin.dailyRewards.resetStreak("unknown-uid")
        assert ok is False

    def test_clear_history(self):
        plugin = MockPlugin()
        player = MockPlayer()
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.claim(player)
        ok, _ = plugin.dailyRewards.clearHistory(str(player.unique_id))
        assert ok is True
        assert plugin.dailyRewards.getPlayerState(str(player.unique_id)) == {
            "last_claim": None, "streak": 0, "total_claims": 0,
        }

    def test_clear_history_no_data(self):
        plugin = MockPlugin()
        ok, _ = plugin.dailyRewards.clearHistory("nope")
        assert ok is False

    def test_invalid_player_state_recovery(self):
        plugin = MockPlugin()
        player = MockPlayer(uid="bad-state")
        plugin.store.data["players"]["bad-state"] = {
            "last_claim": "not-a-date",
            "streak": "garbage",
            "total_claims": [],
        }
        plugin.set_today(datetime.date(2026, 9, 1))
        ok, _ = plugin.dailyRewards.claim(player)
        assert ok is True
        state = plugin.dailyRewards.getPlayerState("bad-state")
        assert state["streak"] == 1
        assert state["total_claims"] == 1
        assert state["last_claim"] == "2026-09-01"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class TestSettingsParsing:
    def test_settings_has_daily_rewards_attrs(self):
        assert "dailyRewardsEnabled" in _SETTINGS_SRC
        assert "dailyRewardsRewards" in _SETTINGS_SRC

    def test_default_enabled(self):
        from endstone_utilitystone.core.settings import Settings
        s = Settings()
        assert s.dailyRewardsEnabled is True

    def test_parses_rewards_from_config(self):
        from endstone_utilitystone.core.settings import Settings
        config = {
            "dailyRewards": {
                "enabled": True,
                "rewards": {
                    "1": ["give {player} iron_ingot 5"],
                    "3": ["give {player} diamond 1"],
                },
            }
        }
        s = Settings(config)
        assert s.dailyRewardsRewards == {
            1: ["give {player} iron_ingot 5"],
            3: ["give {player} diamond 1"],
        }

    def test_ignores_non_numeric_keys(self):
        from endstone_utilitystone.core.settings import Settings
        config = {
            "dailyRewards": {
                "rewards": {"1": "give {player} x", "abc": ["give {player} y"]},
            }
        }
        s = Settings(config)
        assert 1 in s.dailyRewardsRewards
        assert "abc" not in s.dailyRewardsRewards

    def test_config_toml_has_daily_rewards(self):
        assert "[dailyRewards]" in _CONFIG_TOML
        assert "enabled" in _CONFIG_TOML


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
class TestCommands:
    def test_command_class_exists(self):
        assert "class DailyRewardsCommands(" in _CMD_SRC

    def test_command_registered_in_commands_init(self):
        from endstone_utilitystone.commands import COMMAND_GROUPS
        names = [cls.__name__ for cls in COMMAND_GROUPS]
        assert "DailyRewardsCommands" in names

    def test_command_registered_in_plugin(self):
        assert '"dailyreward"' in _PLUGIN_SRC

    def test_claim_binding(self):
        assert '"dailyreward": self.route' in _CMD_SRC

    def test_route_claim_subcommand(self):
        assert 'if action in ("", "claim")' in _CMD_SRC

    def test_route_status_subcommand(self):
        assert 'if action == "status"' in _CMD_SRC


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
class TestPermissions:
    def test_player_permission_node_default_true(self):
        assert "utilitystone.command.dailyreward" in _PLUGIN_SRC
        idx = _PLUGIN_SRC.index("utilitystone.command.dailyreward")
        nearby = _PLUGIN_SRC[idx:idx + 200]
        assert '"op"' not in nearby  # player command defaults to True

    def test_admin_view_permission(self):
        from endstone_utilitystone.ui.daily_rewards import PERM_VIEW
        assert PERM_VIEW == "utilitystone.admin.dailyrewards.view"
        idx = _PLUGIN_SRC.index("utilitystone.admin.dailyrewards.view")
        assert '"op"' in _PLUGIN_SRC[idx:idx + 200]

    def test_admin_reset_permission(self):
        from endstone_utilitystone.ui.daily_rewards import PERM_RESET
        assert PERM_RESET == "utilitystone.admin.dailyrewards.reset"
        idx = _PLUGIN_SRC.index("utilitystone.admin.dailyrewards.reset")
        assert '"op"' in _PLUGIN_SRC[idx:idx + 200]


# ---------------------------------------------------------------------------
# Plugin integration
# ---------------------------------------------------------------------------
class TestPluginIntegration:
    def test_service_import(self):
        assert "from endstone_utilitystone.services.daily_rewards import DailyRewardsService" in _PLUGIN_SRC

    def test_service_attribute_declared(self):
        assert "self.dailyRewards: DailyRewardsService | None = None" in _PLUGIN_SRC

    def test_service_initialized(self):
        assert "self.dailyRewards = DailyRewardsService(self)" in _PLUGIN_SRC

    def test_safeareas_not_broken(self):
        assert "SafeAreaService" in _PLUGIN_SRC
        assert "self.safeareas" in _PLUGIN_SRC


# ---------------------------------------------------------------------------
# GUI structure
# ---------------------------------------------------------------------------
class TestGUIStructure:
    def test_player_menu_has_daily_reward_button(self):
        assert '"Daily Reward"' in _PLAYER_MENU_SRC
        assert "utilitystone.command.dailyreward" in _PLAYER_MENU_SRC

    def test_admin_menu_has_daily_rewards(self):
        assert 'addButton(form, "Daily Rewards"' in _ADMIN_MENU_SRC
        assert "openDailyRewardsAdmin" in _ADMIN_MENU_SRC

    def test_player_inspector_has_daily_rewards(self):
        assert '"Daily Rewards"' in _PLAYER_TOOLS_SRC
        assert "utilitystone.admin.dailyrewards.view" in _PLAYER_TOOLS_SRC

    def test_ui_module_functions_exist(self):
        for func in (
            "def openDailyReward(",
            "def openDailyRewardsAdmin(",
            "def openPlayerDailyRewardDetail(",
            "def _openPlayerDetail(",
            "def _resetStreak(",
            "def _clearHistory(",
        ):
            assert func in _UI_SRC, f"Missing {func}"

    def test_config_menu_has_daily_rewards_category(self):
        assert '"Daily Rewards"' in _CONFIG_MENU_SRC

    def test_gui_uses_wrap_click(self):
        assert "fm.wrapClick" in _UI_SRC