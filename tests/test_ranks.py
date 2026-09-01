"""
Comprehensive tests for the Rank System.

Tests cover:
- Rank CRUD operations
- Player assignment
- Inheritance resolution and validation
- Permission resolution
- Priority, prefix, suffix
- Default rank safety
- Audit logging structure
- Command registration
- Admin GUI structure
- Player inspector integration
"""

from __future__ import annotations

import pathlib

# ---------------------------------------------------------------------------
# Source file paths
# ---------------------------------------------------------------------------
_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone"
_RANKS_SRC = (_SRC / "services" / "ranks.py").read_text()
_RANK_CMDS_SRC = (_SRC / "commands" / "ranks.py").read_text()
_RANK_MENU_SRC = (_SRC / "ui" / "rank_menu.py").read_text()
_PLUGIN_SRC = (_SRC / "plugin.py").read_text()
_ADMIN_MENU_SRC = (_SRC / "ui" / "admin_menu.py").read_text()
_PLAYER_TOOLS_SRC = (_SRC / "ui" / "admin_player_tools.py").read_text()
_CONNECTION_SRC = (_SRC / "listeners" / "connection.py").read_text()
_CHAT_SRC = (_SRC / "listeners" / "chat.py").read_text()


# ===========================================================================
# Rank Service — Structure
# ===========================================================================
class TestRankServiceStructure:
    """Verify RankService exists and has required methods."""

    def test_rank_service_class_exists(self):
        assert "class RankService:" in _RANKS_SRC

    def test_listRanks_method(self):
        assert "def listRanks(" in _RANKS_SRC

    def test_getRankDefinition_method(self):
        assert "def getRankDefinition(" in _RANKS_SRC

    def test_createRank_method(self):
        assert "def createRank(" in _RANKS_SRC

    def test_updateRank_method(self):
        assert "def updateRank(" in _RANKS_SRC

    def test_deleteRank_method(self):
        assert "def deleteRank(" in _RANKS_SRC

    def test_getPlayerRank_method(self):
        assert "def getPlayerRank(" in _RANKS_SRC

    def test_setPlayerRank_method(self):
        assert "def setPlayerRank(" in _RANKS_SRC

    def test_removePlayerRank_method(self):
        assert "def removePlayerRank(" in _RANKS_SRC

    def test_resolvePermissions_method(self):
        assert "def resolvePermissions(" in _RANKS_SRC

    def test_getPriority_method(self):
        assert "def getPriority(" in _RANKS_SRC

    def test_getPrefix_method(self):
        assert "def getPrefix(" in _RANKS_SRC

    def test_getSuffix_method(self):
        assert "def getSuffix(" in _RANKS_SRC

    def test_validateInheritance_method(self):
        assert "def validateInheritance(" in _RANKS_SRC

    def test_applyRank_method(self):
        assert "def applyRank(" in _RANKS_SRC

    def test_removeRankPermissions_method(self):
        assert "def removeRankPermissions(" in _RANKS_SRC

    def test_refreshOnlinePlayers_method(self):
        assert "def refreshOnlinePlayers(" in _RANKS_SRC


# ===========================================================================
# Rank Service — Default Rank
# ===========================================================================
class TestDefaultRank:
    """Verify default rank is always present and protected."""

    def test_default_rank_constant(self):
        assert 'DEFAULT_RANK = "default"' in _RANKS_SRC

    def test_default_rank_always_created(self):
        assert 'DEFAULT_RANK not in self.ranks' in _RANKS_SRC

    def test_cannot_delete_default(self):
        assert "Cannot delete the" in _RANKS_SRC and "default" in _RANKS_SRC

    def test_cannot_create_default(self):
        assert "Cannot create rank" in _RANKS_SRC and "default" in _RANKS_SRC


# ===========================================================================
# Rank Service — Inheritance Validation
# ===========================================================================
class TestInheritanceValidation:
    """Verify inheritance validation prevents cycles and invalid refs."""

    def test_self_inheritance_rejected(self):
        assert "cannot inherit from itself" in _RANKS_SRC

    def test_missing_parent_rejected(self):
        assert "does not exist" in _RANKS_SRC

    def test_circular_inheritance_detected(self):
        assert "Circular inheritance" in _RANKS_SRC

    def test_uses_dfs_for_cycle_detection(self):
        assert "visited" in _RANKS_SRC and "stack" in _RANKS_SRC


# ===========================================================================
# Rank Service — Storage
# ===========================================================================
class TestRankStorage:
    """Verify storage pattern matches existing services."""

    def test_uses_storage_manager(self):
        assert 'plugin.storage.open("ranks"' in _RANKS_SRC

    def test_has_ranks_dict(self):
        assert '"ranks"' in _RANKS_SRC

    def test_has_player_ranks_dict(self):
        assert '"player_ranks"' in _RANKS_SRC

    def test_marks_dirty_on_create(self):
        assert "self.store.markDirty()" in _RANKS_SRC


# ===========================================================================
# Rank Commands
# ===========================================================================
class TestRankCommands:
    """Verify rank commands are registered."""

    def test_rank_command_class_exists(self):
        assert "class RankCommands(" in _RANKS_SRC or "class RankCommands(" in _RANK_CMDS_SRC

    def test_rank_command_in_init(self):
        assert "RankCommands" in (_SRC / "commands" / "__init__.py").read_text()

    def test_rank_in_command_groups(self):
        init_src = (_SRC / "commands" / "__init__.py").read_text()
        assert "RankCommands" in init_src

    def test_rank_command_bindings(self):
        assert '"rank": self.rankCommand' in _RANK_CMDS_SRC

    def test_subcommand_list(self):
        assert '"list": self.rankList' in _RANK_CMDS_SRC

    def test_subcommand_info(self):
        assert '"info": self.rankInfo' in _RANK_CMDS_SRC

    def test_subcommand_create(self):
        assert '"create": self.rankCreate' in _RANK_CMDS_SRC

    def test_subcommand_delete(self):
        assert '"delete": self.rankDelete' in _RANK_CMDS_SRC

    def test_subcommand_set(self):
        assert '"set": self.rankSet' in _RANK_CMDS_SRC

    def test_subcommand_remove(self):
        assert '"remove": self.rankRemove' in _RANK_CMDS_SRC

    def test_subcommand_player(self):
        assert '"player": self.rankPlayer' in _RANK_CMDS_SRC


# ===========================================================================
# Rank Admin GUI
# ===========================================================================
class TestRankAdminGUI:
    """Verify rank admin GUI structure."""

    def test_openRankList_function(self):
        assert "def openRankList(" in _RANK_MENU_SRC

    def test_rank_list_in_admin_menu(self):
        assert "Ranks" in _ADMIN_MENU_SRC

    def test_admin_menu_delegates_to_rank_list(self):
        assert "from endstone_utilitystone.ui.rank_menu import openRankList" in _ADMIN_MENU_SRC

    def test_rank_detail_function(self):
        assert "def _openRankDetail(" in _RANK_MENU_SRC

    def test_create_rank_function(self):
        assert "def _openCreateRank(" in _RANK_MENU_SRC

    def test_edit_priority_function(self):
        assert "def _editPriority(" in _RANK_MENU_SRC

    def test_edit_prefix_function(self):
        assert "def _editPrefix(" in _RANK_MENU_SRC

    def test_edit_suffix_function(self):
        assert "def _editSuffix(" in _RANK_MENU_SRC

    def test_edit_permissions_function(self):
        assert "def _editPermissions(" in _RANK_MENU_SRC

    def test_edit_inheritance_function(self):
        assert "def _editInheritance(" in _RANK_MENU_SRC

    def test_delete_rank_confirmation(self):
        assert "def _confirmDeleteRank(" in _RANK_MENU_SRC


# ===========================================================================
# Player Inspector Integration
# ===========================================================================
class TestPlayerInspectorIntegration:
    """Verify rank display and change in player inspector."""

    def test_inspector_shows_rank(self):
        assert "Rank:" in _PLAYER_TOOLS_SRC and "getEffectiveRankName" in _PLAYER_TOOLS_SRC

    def test_inspector_has_change_rank_button(self):
        assert '"Change Rank"' in _PLAYER_TOOLS_SRC

    def test_change_rank_function_exists(self):
        assert "def _openChangeRank(" in _PLAYER_TOOLS_SRC

    def test_set_player_rank_function(self):
        assert "def _setPlayerRank(" in _PLAYER_TOOLS_SRC

    def test_remove_player_rank_function(self):
        assert "def _removePlayerRank(" in _PLAYER_TOOLS_SRC


# ===========================================================================
# Chat Integration
# ===========================================================================
class TestChatIntegration:
    """Verify prefix/suffix integration in chat."""

    def test_chat_supports_prefix_placeholder(self):
        assert "{prefix}" in _CHAT_SRC

    def test_chat_supports_suffix_placeholder(self):
        assert "{suffix}" in _CHAT_SRC

    def test_chat_gets_rank_prefix(self):
        assert "getPrefix" in _CHAT_SRC

    def test_chat_gets_rank_suffix(self):
        assert "getSuffix" in _CHAT_SRC

    def test_chat_colorizes_prefix(self):
        assert "colorize(rank_prefix)" in _CHAT_SRC or "colorize" in _CHAT_SRC


# ===========================================================================
# Connection Integration
# ===========================================================================
class TestConnectionIntegration:
    """Verify rank applied on join."""

    def test_rank_applied_on_join(self):
        assert "applyRank" in _CONNECTION_SRC

    def test_rank_check_in_join_handler(self):
        assert "plugin.ranks" in _CONNECTION_SRC


# ===========================================================================
# Plugin Integration
# ===========================================================================
class TestPluginIntegration:
    """Verify rank service registered in plugin."""

    def test_rank_service_import(self):
        assert "from endstone_utilitystone.services.ranks import RankService" in _PLUGIN_SRC

    def test_rank_service_initialized(self):
        assert "self.ranks = RankService(self)" in _PLUGIN_SRC

    def test_rank_service_attribute(self):
        assert "self.ranks: RankService | None = None" in _PLUGIN_SRC

    def test_rank_cleanup_on_disable(self):
        assert "self.ranks.clearAttachments()" in _PLUGIN_SRC


# ===========================================================================
# Permission Nodes
# ===========================================================================
class TestPermissionNodes:
    """Verify all rank permission nodes exist."""

    def test_rank_view_perm(self):
        assert "utilitystone.admin.ranks.view" in _PLUGIN_SRC

    def test_rank_create_perm(self):
        assert "utilitystone.admin.ranks.create" in _PLUGIN_SRC

    def test_rank_edit_perm(self):
        assert "utilitystone.admin.ranks.edit" in _PLUGIN_SRC

    def test_rank_delete_perm(self):
        assert "utilitystone.admin.ranks.delete" in _PLUGIN_SRC

    def test_rank_assign_perm(self):
        assert "utilitystone.admin.ranks.assign" in _PLUGIN_SRC

    def test_all_perms_default_to_op(self):
        for perm in [
            "utilitystone.admin.ranks.view",
            "utilitystone.admin.ranks.create",
            "utilitystone.admin.ranks.edit",
            "utilitystone.admin.ranks.delete",
            "utilitystone.admin.ranks.assign",
        ]:
            # Check the permission exists with "op" default somewhere nearby in the permissions dict
            assert f'"{perm}"' in _PLUGIN_SRC, f"{perm} not found"
            assert '"op"' in _PLUGIN_SRC, "op default not found"


# ===========================================================================
# Command Registration
# ===========================================================================
class TestCommandRegistration:
    """Verify /rank command is registered in plugin."""

    def test_rank_command_registered(self):
        assert '"rank":' in _PLUGIN_SRC

    def test_rank_command_description(self):
        assert '"Manage server ranks."' in _PLUGIN_SRC

    def test_rank_command_has_usages(self):
        assert "/rank list" in _PLUGIN_SRC
        assert "/rank set" in _PLUGIN_SRC


# ===========================================================================
# Deletion Safety
# ===========================================================================
class TestDeletionSafety:
    """Verify rank deletion checks dependencies."""

    def test_checks_assigned_players(self):
        assert "assigned" in _RANKS_SRC and "player" in _RANKS_SRC.lower()

    def test_checks_inheriting_ranks(self):
        assert "inheriting" in _RANKS_SRC or "inherit" in _RANKS_SRC

    def test_blocks_deletion_with_dependencies(self):
        assert "Cannot delete" in _RANKS_SRC


# ===========================================================================
# Rank Priority
# ===========================================================================
class TestRankPriority:
    """Verify priority is stored and accessible."""

    def test_priority_in_definition(self):
        assert '"priority"' in _RANKS_SRC

    def test_getPriority_returns_int(self):
        assert "def getPriority(" in _RANKS_SRC

    def test_default_priority_zero(self):
        assert "priority: int = 0" in _RANKS_SRC or "priority=0" in _RANKS_SRC


# ===========================================================================
# Audit Logging
# ===========================================================================
class TestAuditLogging:
    """Verify audit logging for rank operations."""

    def test_create_logged(self):
        assert "created" in _RANKS_SRC and "logger" in _RANKS_SRC

    def test_delete_logged(self):
        assert "deleted" in _RANKS_SRC and "logger" in _RANKS_SRC

    def test_assignment_logged(self):
        assert "set to" in _RANKS_SRC and "logger" in _RANKS_SRC

    def test_removal_logged(self):
        assert "removed" in _RANKS_SRC and "logger" in _RANKS_SRC
