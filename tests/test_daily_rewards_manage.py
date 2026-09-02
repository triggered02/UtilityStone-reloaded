"""
Tests for the Daily Rewards milestone management feature (admin).

Covers the service milestone CRUD API, config.toml persistence, empty
command validation, milestone validation, permission protection, and the
Manage Rewards GUI wiring.
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
_UI_SRC = (_SRC / "ui" / "daily_rewards.py").read_text()
_PLUGIN_SRC = (_SRC / "plugin.py").read_text()

from endstone_utilitystone.services.daily_rewards import (  # noqa: E402
    DailyRewardsService,
    _rewriteRewardsSection,
)

# ---------------------------------------------------------------------------
# Mock infrastructure (self-contained, mirrors test_daily_rewards.py)
# ---------------------------------------------------------------------------
DEFAULT_REWARDS = {
    1: ["give {player} iron_ingot 5"],
    3: ["give {player} diamond 1"],
    7: ["give {player} emerald 5"],
    30: ["give {player} diamond_block 1"],
}


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
        self.errors = []

    def info(self, msg):
        pass

    def warning(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        self.errors.append(msg)


class MockSettings:
    def __init__(self, enabled=True, rewards=None):
        self.dailyRewardsEnabled = enabled
        self.dailyRewardsRewards = rewards if rewards is not None else dict(DEFAULT_REWARDS)


class MockPlayer:
    def __init__(self, name="Steve", uid="abc-123"):
        self.name = name
        self.unique_id = uid

    def has_permission(self, perm):
        return True


class MockServer:
    def __init__(self):
        self.command_sender = "console"
        self.dispatched = []
        self.online_players = []

    def dispatch_command(self, sender, cmd):
        self.dispatched.append((sender, cmd))


class MockMessages:
    def __init__(self):
        self.success_msgs = []
        self.failure_msgs = []

    def success(self, player, text):
        self.success_msgs.append(text)

    def failure(self, player, text):
        self.failure_msgs.append(text)


class MockPlugin:
    def __init__(self, enabled=True, rewards=None, data_folder=None):
        self.store = MockStore({"players": {}})
        self.storage = MockStorageManager(self.store)
        self.server = MockServer()
        self.logger = MockLogger()
        self.messages = MockMessages()
        self.settings = MockSettings(enabled=enabled, rewards=rewards)
        self.data_folder = data_folder or ""
        self.dailyRewards = DailyRewardsService(self)

    def set_today(self, date):
        self.dailyRewards._today = staticmethod(lambda: date)


# ---------------------------------------------------------------------------
# Service structure
# ---------------------------------------------------------------------------
class TestManageServiceStructure:
    def test_manage_methods_exist(self):
        for method in (
            "def getRewards(",
            "def getReward(",
            "def createReward(",
            "def setReward(",
            "def deleteReward(",
            "def addRewardCommand(",
            "def updateRewardCommand(",
            "def removeRewardCommand(",
        ):
            assert method in _SERVICE_SRC, f"Missing {method}"

    def test_service_has_persist_method(self):
        assert "def _persistMilestones(" in _SERVICE_SRC


# ---------------------------------------------------------------------------
# Reading milestones
# ---------------------------------------------------------------------------
class TestReadMilestones:
    def test_get_rewards_returns_config(self):
        plugin = MockPlugin()
        rewards = plugin.dailyRewards.getRewards()
        assert rewards == DEFAULT_REWARDS

    def test_get_reward_existing(self):
        plugin = MockPlugin()
        assert plugin.dailyRewards.getReward(3) == ["give {player} diamond 1"]

    def test_get_reward_missing(self):
        plugin = MockPlugin()
        assert plugin.dailyRewards.getReward(99) is None

    def test_get_reward_invalid_input(self):
        plugin = MockPlugin()
        assert plugin.dailyRewards.getReward("not-a-number") is None


# ---------------------------------------------------------------------------
# Adding milestones
# ---------------------------------------------------------------------------
class TestAddMilestone:
    def test_create_reward(self):
        plugin = MockPlugin(rewards={})
        ok, msg = plugin.dailyRewards.createReward(7, ["give {player} diamond 3", "xp add {player} 250"])
        assert ok is True
        assert plugin.dailyRewards.getReward(7) == ["give {player} diamond 3", "xp add {player} 250"]
        assert "created" in msg

    def test_create_reward_duplicate_denied(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.createReward(3, ["give {player} diamond 5"])
        assert ok is False
        assert "already exists" in msg

    def test_reject_zero(self):
        plugin = MockPlugin(rewards={})
        ok, msg = plugin.dailyRewards.createReward(0, ["give {player} iron_ingot 1"])
        assert ok is False
        assert "positive" in msg

    def test_reject_negative(self):
        plugin = MockPlugin(rewards={})
        ok, msg = plugin.dailyRewards.createReward(-5, ["give {player} iron_ingot 1"])
        assert ok is False
        assert "positive" in msg

    def test_reject_non_numeric(self):
        plugin = MockPlugin(rewards={})
        ok, msg = plugin.dailyRewards.createReward("abc", ["give {player} iron_ingot 1"])
        assert ok is False

    def test_normalizes_whitespace(self):
        plugin = MockPlugin(rewards={})
        ok, _ = plugin.dailyRewards.createReward(4, ["  give {player} iron_ingot 5  ", "  "])
        assert ok is True
        assert plugin.dailyRewards.getReward(4) == ["give {player} iron_ingot 5"]


# ---------------------------------------------------------------------------
# Editing milestones
# ---------------------------------------------------------------------------
class TestEditMilestone:
    def test_set_reward_updates_commands(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.setReward(3, ["give {player} gold_ingot 2"])
        assert ok is True
        assert plugin.dailyRewards.getReward(3) == ["give {player} gold_ingot 2"]
        assert "updated" in msg

    def test_add_command(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.addRewardCommand(7, "xp add {player} 250")
        assert ok is True
        assert plugin.dailyRewards.getReward(7) == ["give {player} emerald 5", "xp add {player} 250"]

    def test_add_command_empty_denied(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.addRewardCommand(7, "   ")
        assert ok is False
        assert "empty" in msg

    def test_update_command(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.updateRewardCommand(7, 0, "give {player} emerald 10")
        assert ok is True
        assert plugin.dailyRewards.getReward(7) == ["give {player} emerald 10"]

    def test_update_command_bad_index(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.updateRewardCommand(7, 99, "give {player} x 1")
        assert ok is False

    def test_update_command_empty_denied(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.updateRewardCommand(7, 0, "  ")
        assert ok is False
        assert "empty" in msg

    def test_remove_command(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.removeRewardCommand(7, 0)
        assert ok is True
        assert plugin.dailyRewards.getReward(7) == []

    def test_remove_command_bad_index(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.removeRewardCommand(7, 99)
        assert ok is False


# ---------------------------------------------------------------------------
# Deleting milestones
# ---------------------------------------------------------------------------
class TestDeleteMilestone:
    def test_delete_reward(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.deleteReward(7)
        assert ok is True
        assert plugin.dailyRewards.getReward(7) is None

    def test_delete_missing_reward(self):
        plugin = MockPlugin()
        ok, msg = plugin.dailyRewards.deleteReward(99)
        assert ok is False


# ---------------------------------------------------------------------------
# config.toml persistence
# ---------------------------------------------------------------------------
class TestConfigPersistence:
    def test_rewrite_rewards_section(self):
        old = (
            "[dailyRewards]\n"
            "enabled = true\n\n"
            '[dailyRewards.rewards]\n'
            '"3" = [\n    "give {player} diamond 1",\n]\n\n'
            "[kits.starter]\n"
            "cooldown = \"24h\"\n"
        )
        new = _rewriteRewardsSection(old, {
            1: ["give {player} bread 16"],
            3: ["give {player} iron_ingot 5"],
        })
        assert "enabled = true" in new
        assert "1 = [" in new
        assert '"give {player} bread 16"' in new
        assert '"3" = [' not in new
        assert "[kits.starter]" in new
        assert "cooldown" in new

    def test_persist_writes_file(self, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text(
            "[dailyRewards]\n"
            "enabled = true\n\n"
            '[dailyRewards.rewards]\n'
            '"1" = [\n    "give {player} iron_ingot 5",\n]\n\n'
            "[other]\n"
            "someValue = 42\n",
            encoding="utf-8",
        )
        plugin = MockPlugin(data_folder=str(tmp_path))
        plugin.dailyRewards.setReward(1, ["give {player} diamond 3", "xp add {player} 250"])

        content = config.read_text(encoding="utf-8")
        assert "give {player} diamond 3" in content
        assert "xp add {player} 250" in content
        assert "someValue = 42" in content  # unrelated section preserved

    def test_in_memory_updates_even_when_file_missing(self):
        # When there is no config folder, changes should still apply in-session.
        plugin = MockPlugin()
        ok, _ = plugin.dailyRewards.setReward(3, ["give {player} gold_ingot 1"])
        assert ok is True
        assert plugin.dailyRewards.getReward(3) == ["give {player} gold_ingot 1"]


# ---------------------------------------------------------------------------
# Reward execution after milestone edits
# ---------------------------------------------------------------------------
class TestEditThenClaim:
    def test_claim_uses_updated_reward(self):
        plugin = MockPlugin()
        player = MockPlayer(name="Steve")
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.setReward(1, ["give {player} diamond 3"])
        plugin.dailyRewards.claim(player)
        assert plugin.server.dispatched[-1][1] == "give Steve diamond 3"

    def test_claim_after_delete_uses_next_lower(self):
        plugin = MockPlugin()
        player = MockPlayer(name="Steve")
        plugin.set_today(datetime.date(2026, 9, 1))
        plugin.dailyRewards.deleteReward(1)
        # With day-1 removed, the new day-1 claim falls through to the next
        # lower milestone... which is none, so no command runs but claim succeeds.
        ok, _ = plugin.dailyRewards.claim(player)
        assert ok is True
        assert len(plugin.server.dispatched) == 0


# ---------------------------------------------------------------------------
# GUI structure & permissions
# ---------------------------------------------------------------------------
class TestManageGUIPermissions:
    def test_perm_manage_constant(self):
        assert 'PERM_MANAGE = "utilitystone.admin.dailyrewards.manage"' in _UI_SRC

    def test_permission_registered_in_plugin(self):
        assert "utilitystone.admin.dailyrewards.manage" in _PLUGIN_SRC
        idx = _PLUGIN_SRC.index("utilitystone.admin.dailyrewards.manage")
        assert '"op"' in _PLUGIN_SRC[idx:idx + 200]

    def test_manage_button_in_admin_screen(self):
        assert '"Manage Rewards"' in _UI_SRC
        assert "PERM_MANAGE" in _UI_SRC

    def test_manage_screen_function_exists(self):
        assert "def _openManageRewards(" in _UI_SRC

    def test_add_reward_function_exists(self):
        assert "def _openAddReward(" in _UI_SRC

    def test_reward_detail_function_exists(self):
        assert "def _openRewardDetail(" in _UI_SRC

    def test_command_add_function_exists(self):
        assert "def _addCommandInput(" in _UI_SRC

    def test_command_edit_function_exists(self):
        assert "def _editCommandInput(" in _UI_SRC

    def test_command_remove_function_exists(self):
        assert "def _doRemoveCommand(" in _UI_SRC

    def test_delete_uses_confirmation(self):
        assert "def _confirmDeleteReward(" in _UI_SRC
        assert "askConfirmation" in _UI_SRC

    def test_milestone_parse_helper(self):
        from endstone_utilitystone.ui.daily_rewards import _parseMilestoneText
        assert _parseMilestoneText("7") == (7, "")
        day, err = _parseMilestoneText("0")
        assert day == 0 and err
        day, err = _parseMilestoneText("-3")
        assert day == 0 and err
        day, err = _parseMilestoneText("abc")
        assert day == 0 and err

    def test_manage_gated_by_permission(self):
        # _requireManagePermission enforces the manage node before showing UI.
        assert "PERM_MANAGE" in _UI_SRC
        assert "do not have permission to manage daily rewards" in _UI_SRC


# ---------------------------------------------------------------------------
# Rewrite helper edge cases
# ---------------------------------------------------------------------------
class TestRewriteEdgeCases:
    def test_missing_section_gets_appended(self):
        text = "[other]\nvalue = 1\n"
        new = _rewriteRewardsSection(text, {1: ["give {player} x 1"]})
        assert "[dailyRewards.rewards]" in new
        assert "[other]" in new
        assert "1 = [" in new

    def test_empty_milestones_keeps_header(self):
        text = '[dailyRewards.rewards]\n"1" = [\n    "give {player} x",\n]\n'
        new = _rewriteRewardsSection(text, {})
        assert "[dailyRewards.rewards]" in new
        assert "1 = [" not in new

    def test_escapes_quotes(self):
        old = "[dailyRewards.rewards]\n1 = [\n]\n"
        new = _rewriteRewardsSection(old, {1: ['say "hi" {player}']})
        assert 'say \\"hi\\" {player}' in new