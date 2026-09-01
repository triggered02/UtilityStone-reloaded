"""
Rank management commands.

/rank list
/rank info <rank>
/rank create <rank>
/rank delete <rank>
/rank set <player> <rank>
/rank remove <player>
/rank player <player>
"""

from __future__ import annotations

from endstone_utilitystone.commands.base import CommandGroup
from endstone_utilitystone.services.ranks import DEFAULT_RANK


class RankCommands(CommandGroup):
    def bindings(self) -> dict:
        return {
            "rank": self.rankCommand,
        }

    def rankCommand(self, sender, args: list) -> bool:
        if not args:
            self.messages.failure(sender, "Usage: /rank <list|info|create|delete|set|remove|player>")
            return True

        sub = args[0].lower()
        rest = args[1:]

        handlers = {
            "list": self.rankList,
            "info": self.rankInfo,
            "create": self.rankCreate,
            "delete": self.rankDelete,
            "set": self.rankSet,
            "remove": self.rankRemove,
            "player": self.rankPlayer,
        }

        handler = handlers.get(sub)
        if handler is None:
            self.messages.failure(sender, f"Unknown subcommand '{sub}'. Use: list, info, create, delete, set, remove, player")
            return True

        return handler(sender, rest)

    # ------------------------------------------------------------------
    # /rank list
    # ------------------------------------------------------------------
    def rankList(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.admin.ranks.view"):
            self.messages.failure(sender, "You do not have permission to view ranks.")
            return True

        ranks = self.plugin.ranks.listRanks()
        if not ranks:
            self.messages.failure(sender, "No ranks defined.")
            return True

        lines = [f"&eRanks ({len(ranks)}):"]
        for name in ranks:
            definition = self.plugin.ranks.getRankDefinition(name)
            priority = definition.get("priority", 0) if definition else 0
            prefix = definition.get("prefix", "") if definition else ""
            display = f"  &f{name} &7(pri: {priority})"
            if prefix:
                display += f" &7prefix: {prefix}"
            lines.append(colorize(display))

        sender.send_message("\n".join(lines))
        return True

    # ------------------------------------------------------------------
    # /rank info <rank>
    # ------------------------------------------------------------------
    def rankInfo(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.admin.ranks.view"):
            self.messages.failure(sender, "You do not have permission to view ranks.")
            return True

        if not args:
            self.messages.failure(sender, "Usage: /rank info <rank>")
            return True

        name = args[0].lower()
        definition = self.plugin.ranks.getRankDefinition(name)
        if definition is None:
            self.messages.failure(sender, f"Rank '{name}' does not exist.")
            return True

        perms = self.plugin.ranks.resolvePermissions(name)
        priority = definition.get("priority", 0)
        prefix = definition.get("prefix", "")
        suffix = definition.get("suffix", "")
        inheritance = definition.get("inheritance", [])

        lines = [
            f"&eRank: &f{name}",
            f"  &7Priority: &f{priority}",
            f"  &7Prefix: &f{prefix or '(none)'}",
            f"  &7Suffix: &f{suffix or '(none)'}",
            f"  &7Inherits: &f{', '.join(inheritance) if inheritance else '(none)'}",
            f"  &7Own permissions: &f{len(definition.get('permissions', []))}",
            f"  &7Total (resolved): &f{len(perms)}",
        ]

        if perms:
            lines.append("  &7All permissions:")
            for p in sorted(perms):
                lines.append(f"    &f{p}")

        sender.send_message("\n".join(lines))
        return True

    # ------------------------------------------------------------------
    # /rank create <rank>
    # ------------------------------------------------------------------
    def rankCreate(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.admin.ranks.create"):
            self.messages.failure(sender, "You do not have permission to create ranks.")
            return True

        if not args:
            self.messages.failure(sender, "Usage: /rank create <rank>")
            return True

        name = args[0].lower()
        ok, msg = self.plugin.ranks.createRank(name)
        if ok:
            self.messages.success(sender, msg)
        else:
            self.messages.failure(sender, msg)
        return True

    # ------------------------------------------------------------------
    # /rank delete <rank>
    # ------------------------------------------------------------------
    def rankDelete(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.admin.ranks.delete"):
            self.messages.failure(sender, "You do not have permission to delete ranks.")
            return True

        if not args:
            self.messages.failure(sender, "Usage: /rank delete <rank>")
            return True

        name = args[0].lower()
        ok, msg = self.plugin.ranks.deleteRank(name)
        if ok:
            self.messages.success(sender, msg)
        else:
            self.messages.failure(sender, msg)
        return True

    # ------------------------------------------------------------------
    # /rank set <player> <rank>
    # ------------------------------------------------------------------
    def rankSet(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.admin.ranks.assign"):
            self.messages.failure(sender, "You do not have permission to assign ranks.")
            return True

        if len(args) < 2:
            self.messages.failure(sender, "Usage: /rank set <player> <rank>")
            return True

        target = self.requireTarget(sender, args[0])
        if target is None:
            return True

        rank_name = args[1].lower()
        ok, msg = self.plugin.ranks.setPlayerRank(str(target.unique_id), rank_name)
        if ok:
            self.messages.success(sender, f"Set {target.name}'s rank to '{rank_name}'.")
        else:
            self.messages.failure(sender, msg)
        return True

    # ------------------------------------------------------------------
    # /rank remove <player>
    # ------------------------------------------------------------------
    def rankRemove(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.admin.ranks.assign"):
            self.messages.failure(sender, "You do not have permission to modify ranks.")
            return True

        if not args:
            self.messages.failure(sender, "Usage: /rank remove <player>")
            return True

        target = self.requireTarget(sender, args[0])
        if target is None:
            return True

        ok, msg = self.plugin.ranks.removePlayerRank(str(target.unique_id))
        if ok:
            self.messages.success(sender, f"Removed {target.name}'s rank.")
        else:
            self.messages.failure(sender, msg)
        return True

    # ------------------------------------------------------------------
    # /rank player <player>
    # ------------------------------------------------------------------
    def rankPlayer(self, sender, args: list) -> bool:
        if not sender.has_permission("utilitystone.admin.ranks.view"):
            self.messages.failure(sender, "You do not have permission to view ranks.")
            return True

        if not args:
            self.messages.failure(sender, "Usage: /rank player <player>")
            return True

        target = self.requireTarget(sender, args[0])
        if target is None:
            return True

        rank_name = self.plugin.ranks.getEffectiveRankName(target)
        definition = self.plugin.ranks.getRankDefinition(rank_name)
        priority = definition.get("priority", 0) if definition else 0
        perms = self.plugin.ranks.resolvePermissions(rank_name)

        sender.send_message(
            f"&e{target.name}'s rank: &f{rank_name} &7(pri: {priority}, {len(perms)} permissions)"
        )
        return True


def colorize(text: str) -> str:
    from endstone_utilitystone.util.text import colorize as _colorize
    return _colorize(text)
