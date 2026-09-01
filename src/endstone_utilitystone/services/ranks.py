"""
Rank Service — Rank management, permissions, inheritance, and assignment.

Storage structure:
{
  "ranks": {
    "default": { "priority": 0, "prefix": "", "suffix": "", "permissions": [], "inheritance": [] }
  },
  "player_ranks": {
    "player_uuid": "rank_name"
  }
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone

DEFAULT_RANK = "default"


class RankService:
    def __init__(self, plugin: UtilityStone):
        self.plugin = plugin
        self.store = plugin.storage.open("ranks", {"ranks": {}, "player_ranks": {}})
        self.store.data.setdefault("ranks", {})
        self.store.data.setdefault("player_ranks", {})
        self._attachments: dict[int, list] = {}

        # Ensure default rank always exists
        if DEFAULT_RANK not in self.ranks:
            self.ranks[DEFAULT_RANK] = {
                "priority": 0,
                "prefix": "",
                "suffix": "",
                "permissions": [],
                "inheritance": [],
            }
            self.store.markDirty()

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------
    @property
    def ranks(self) -> dict:
        return self.store.data["ranks"]

    @property
    def playerRanks(self) -> dict:
        return self.store.data["player_ranks"]

    # ------------------------------------------------------------------
    # Rank CRUD
    # ------------------------------------------------------------------
    def listRanks(self) -> list[str]:
        return sorted(self.ranks.keys())

    def getRankDefinition(self, name: str) -> dict | None:
        return self.ranks.get(name)

    def createRank(
        self,
        name: str,
        priority: int = 0,
        prefix: str = "",
        suffix: str = "",
        permissions: list[str] | None = None,
        inheritance: list[str] | None = None,
    ) -> tuple[bool, str]:
        name = name.strip().lower()
        if not name:
            return False, "Rank name cannot be empty."
        if name == DEFAULT_RANK:
            return False, f"Cannot create rank '{DEFAULT_RANK}' — it already exists."
        if name in self.ranks:
            return False, f"Rank '{name}' already exists."

        inheritance = inheritance or []
        permissions = permissions or []

        # Validate inheritance
        valid, err = self.validateInheritance(name, inheritance)
        if not valid:
            return False, err

        self.ranks[name] = {
            "priority": priority,
            "prefix": prefix,
            "suffix": suffix,
            "permissions": permissions,
            "inheritance": inheritance,
        }
        self.store.markDirty()
        self.plugin.logger.info(f"Rank '{name}' created (priority={priority})")
        return True, f"Rank '{name}' created."

    def updateRank(self, name: str, **kwargs) -> tuple[bool, str]:
        definition = self.ranks.get(name)
        if definition is None:
            return False, f"Rank '{name}' does not exist."

        if "inheritance" in kwargs:
            valid, err = self.validateInheritance(name, kwargs["inheritance"])
            if not valid:
                return False, err

        for key in ("priority", "prefix", "suffix", "permissions", "inheritance"):
            if key in kwargs:
                definition[key] = kwargs[key]

        self.store.markDirty()

        # Refresh all online players with this rank
        self._refreshPlayersWithRank(name)

        return True, f"Rank '{name}' updated."

    def deleteRank(self, name: str) -> tuple[bool, str]:
        if name == DEFAULT_RANK:
            return False, f"Cannot delete the '{DEFAULT_RANK}' rank."
        if name not in self.ranks:
            return False, f"Rank '{name}' does not exist."

        # Check for players assigned to this rank
        assigned = [pid for pid, rn in self.playerRanks.items() if rn == name]
        if assigned:
            return False, f"Cannot delete '{name}' — {len(assigned)} player(s) are assigned to it. Reassign them first."

        # Check for ranks inheriting from this rank
        inheriting = []
        for rankName, rankDef in self.ranks.items():
            if name in rankDef.get("inheritance", []):
                inheriting.append(rankName)
        if inheriting:
            return False, f"Cannot delete '{name}' — rank(s) {', '.join(inheriting)} inherit from it."

        del self.ranks[name]
        self.store.markDirty()
        self.plugin.logger.info(f"Rank '{name}' deleted")
        return True, f"Rank '{name}' deleted."

    # ------------------------------------------------------------------
    # Player assignment
    # ------------------------------------------------------------------
    def getPlayerRank(self, player_uuid: str) -> str | None:
        return self.playerRanks.get(str(player_uuid))

    def setPlayerRank(self, player_uuid: str, rank_name: str) -> tuple[bool, str]:
        rank_name = rank_name.strip().lower()
        if rank_name not in self.ranks:
            return False, f"Rank '{rank_name}' does not exist."

        self.playerRanks[str(player_uuid)] = rank_name
        self.store.markDirty()

        # Apply to online player if present
        player = self._findOnlinePlayer(player_uuid)
        if player is not None:
            self.applyRank(player)

        self.plugin.logger.info(f"Rank of {player_uuid} set to '{rank_name}'")
        return True, f"Rank set to '{rank_name}'."

    def removePlayerRank(self, player_uuid: str) -> tuple[bool, str]:
        key = str(player_uuid)
        if key not in self.playerRanks:
            return False, "Player has no assigned rank."

        old = self.playerRanks.pop(key)
        self.store.markDirty()

        # Apply default rank to online player
        player = self._findOnlinePlayer(player_uuid)
        if player is not None:
            self.applyRank(player)

        self.plugin.logger.info(f"Rank removed from {player_uuid} (was '{old}')")
        return True, f"Rank removed (reverted to default)."

    # ------------------------------------------------------------------
    # Inheritance resolution
    # ------------------------------------------------------------------
    def validateInheritance(self, rank_name: str, parents: list[str]) -> tuple[bool, str]:
        """Check that inheritance is valid (no cycles, no missing parents, no self-reference)."""
        if rank_name in parents:
            return False, f"Rank '{rank_name}' cannot inherit from itself."

        for parent in parents:
            if parent not in self.ranks and parent != rank_name:
                return False, f"Parent rank '{parent}' does not exist."

        # Check for cycles using DFS
        visited = set()
        stack = list(parents)
        while stack:
            current = stack.pop()
            if current == rank_name:
                return False, f"Circular inheritance detected involving '{current}'."
            if current in visited:
                continue
            visited.add(current)
            parent_def = self.ranks.get(current)
            if parent_def:
                stack.extend(parent_def.get("inheritance", []))

        return True, ""

    def resolvePermissions(self, rank_name: str) -> set[str]:
        """Collect all permissions from a rank and its ancestors."""
        visited = set()
        permissions: set[str] = set()

        def walk(name: str):
            if name in visited:
                return
            visited.add(name)
            rank_def = self.ranks.get(name)
            if rank_def is None:
                return
            permissions.update(rank_def.get("permissions", []))
            for parent in rank_def.get("inheritance", []):
                walk(parent)

        walk(rank_name)
        return permissions

    # ------------------------------------------------------------------
    # Priority / prefix / suffix
    # ------------------------------------------------------------------
    def getPriority(self, rank_name: str) -> int:
        rank_def = self.ranks.get(rank_name)
        if rank_def is None:
            return 0
        return rank_def.get("priority", 0)

    def getPrefix(self, rank_name: str | None) -> str:
        if rank_name is None:
            return ""
        rank_def = self.ranks.get(rank_name)
        if rank_def is None:
            return ""
        return rank_def.get("prefix", "")

    def getSuffix(self, rank_name: str | None) -> str:
        if rank_name is None:
            return ""
        rank_def = self.ranks.get(rank_name)
        if rank_def is None:
            return ""
        return rank_def.get("suffix", "")

    # ------------------------------------------------------------------
    # Permission attachment (Endstone API)
    # ------------------------------------------------------------------
    def applyRank(self, player) -> None:
        """Apply rank permissions to an online player."""
        from endstone_utilitystone.util.text import colorize

        uid = player.unique_id

        # Remove old attachments
        old = self._attachments.pop(uid, [])
        for att in old:
            try:
                player.remove_attachment(att)
            except Exception:
                pass

        # Determine effective rank
        rank_name = self.getPlayerRank(str(uid))
        if rank_name is None:
            rank_name = DEFAULT_RANK

        # Collect permissions from rank hierarchy
        perms = self.resolvePermissions(rank_name)

        # Add new attachments
        new_attachments = []
        for perm in perms:
            try:
                att = player.add_attachment(self.plugin, perm, True)
                if att is not None:
                    new_attachments.append(att)
            except Exception:
                pass

        if new_attachments:
            self._attachments[uid] = new_attachments

    def removeRankPermissions(self, player) -> None:
        """Remove all rank-based permission attachments from a player."""
        uid = player.unique_id
        old = self._attachments.pop(uid, [])
        for att in old:
            try:
                player.remove_attachment(att)
            except Exception:
                pass

    def refreshOnlinePlayers(self) -> None:
        """Reapply ranks to all online players."""
        for player in self.plugin.server.online_players:
            try:
                self.applyRank(player)
            except Exception:
                pass

    def _refreshPlayersWithRank(self, rank_name: str) -> None:
        """Refresh all online players who have the specified rank."""
        for player in self.plugin.server.online_players:
            if self.getPlayerRank(str(player.unique_id)) == rank_name:
                try:
                    self.applyRank(player)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def clearAttachments(self) -> None:
        """Remove all stored attachments (called on disable)."""
        self._attachments.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _findOnlinePlayer(self, player_uuid):
        uid_str = str(player_uuid)
        for player in self.plugin.server.online_players:
            if str(player.unique_id) == uid_str:
                return player
        return None

    def getEffectiveRankName(self, player) -> str:
        """Return the rank name for a player (assigned or default)."""
        rank = self.getPlayerRank(str(player.unique_id))
        return rank if rank is not None else DEFAULT_RANK

    def formatPlayerName(self, player) -> str:
        """Return 'prefix + name + suffix' with color codes resolved."""
        from endstone_utilitystone.util.text import colorize

        rank_name = self.getEffectiveRankName(player)
        prefix = self.getPrefix(rank_name)
        suffix = self.getSuffix(rank_name)
        name = player.name

        if prefix or suffix:
            return colorize(f"{prefix}{name}{suffix}")
        return name
