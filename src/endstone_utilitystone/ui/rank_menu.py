"""
Rank Admin GUI — Manage ranks via the Admin Panel.

Navigation:
    Admin Panel → Ranks → Rank List
    Admin Panel → Ranks → Select Rank → Rank Details
    Admin Panel → Ranks → Create Rank
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from endstone_utilitystone.ui.components import (
    addDivider,
    addHeader,
    addLabel,
    addButton,
    buildActionMenu,
    buildModal,
    emptyState,
)
from endstone_utilitystone.ui.permissions import hasAdminGui, hasPermission
from endstone_utilitystone.services.ranks import DEFAULT_RANK

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


# ---------------------------------------------------------------------------
# Permission gate
# ---------------------------------------------------------------------------
def _requireRankPerm(plugin, player, perm: str, label: str) -> bool:
    if not hasPermission(player, perm):
        plugin.messages.failure(player, f"You do not have permission to {label}.")
        return False
    return True


# ---------------------------------------------------------------------------
# Rank List
# ---------------------------------------------------------------------------

def openRankList(plugin: UtilityStone, player) -> bool:
    fm = plugin.gui

    if not _requireRankPerm(plugin, player, "utilitystone.admin.ranks.view", "view ranks"):
        return False

    form = buildActionMenu("Rank Management", "Manage server ranks")

    ranks = plugin.ranks.listRanks()
    addLabel(form, f"{len(ranks)} ranks defined")

    for name in ranks:
        definition = plugin.ranks.getRankDefinition(name)
        priority = definition.get("priority", 0) if definition else 0
        prefix = definition.get("prefix", "") if definition else ""
        display = f"{name} (pri: {priority})"
        if prefix:
            display += f"  {prefix}"

        addButton(
            form,
            display,
            on_click=fm.wrapClick(player, lambda p=player, n=name: _openRankDetail(plugin, p, n), f"rank_detail:{name}"),
        )

    addDivider(form)

    if hasPermission(player, "utilitystone.admin.ranks.create"):
        addButton(
            form,
            "Create Rank",
            on_click=fm.wrapClick(player, lambda: _openCreateRank(plugin, player), "rank_create"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: _openAdminPanel(plugin, player), "back"))
    return fm.sendForm(player, form, label="rank_list")


def _openAdminPanel(plugin: UtilityStone, player) -> None:
    from endstone_utilitystone.ui.admin_menu import openAdminPanel
    openAdminPanel(plugin, player)


# ---------------------------------------------------------------------------
# Rank Details
# ---------------------------------------------------------------------------

def _openRankDetail(plugin: UtilityStone, player, rank_name: str) -> None:
    fm = plugin.gui

    if not _requireRankPerm(plugin, player, "utilitystone.admin.ranks.view", "view rank details"):
        return

    definition = plugin.ranks.getRankDefinition(rank_name)
    if definition is None:
        plugin.messages.failure(player, f"Rank '{rank_name}' not found.")
        return

    form = buildActionMenu(f"Rank: {rank_name}")

    priority = definition.get("priority", 0)
    prefix = definition.get("prefix", "")
    suffix = definition.get("suffix", "")
    inheritance = definition.get("inheritance", [])
    permissions = definition.get("permissions", [])
    resolved = plugin.ranks.resolvePermissions(rank_name)

    addHeader(form, "Information")
    addLabel(form, f"Name: {rank_name}")
    addLabel(form, f"Priority: {priority}")
    addLabel(form, f"Prefix: {prefix or '(none)'}")
    addLabel(form, f"Suffix: {suffix or '(none)'}")
    addLabel(form, f"Inherits: {', '.join(inheritance) if inheritance else '(none)'}")
    addLabel(form, f"Own permissions: {len(permissions)}")
    addLabel(form, f"Total resolved: {len(resolved)}")

    addDivider(form)
    addHeader(form, "Actions")

    if hasPermission(player, "utilitystone.admin.ranks.edit"):
        addButton(
            form,
            "Edit Priority",
            on_click=fm.wrapClick(player, lambda: _editPriority(plugin, player, rank_name), f"rank_pri:{rank_name}"),
        )
        addButton(
            form,
            "Edit Prefix",
            on_click=fm.wrapClick(player, lambda: _editPrefix(plugin, player, rank_name), f"rank_prefix:{rank_name}"),
        )
        addButton(
            form,
            "Edit Suffix",
            on_click=fm.wrapClick(player, lambda: _editSuffix(plugin, player, rank_name), f"rank_suffix:{rank_name}"),
        )
        addButton(
            form,
            "Edit Permissions",
            on_click=fm.wrapClick(player, lambda: _editPermissions(plugin, player, rank_name), f"rank_perms:{rank_name}"),
        )
        addButton(
            form,
            "Edit Inheritance",
            on_click=fm.wrapClick(player, lambda: _editInheritance(plugin, player, rank_name), f"rank_inherit:{rank_name}"),
        )

    if rank_name != DEFAULT_RANK and hasPermission(player, "utilitystone.admin.ranks.delete"):
        addButton(
            form,
            "Delete Rank",
            on_click=fm.wrapClick(player, lambda: _confirmDeleteRank(plugin, player, rank_name), f"rank_del:{rank_name}"),
        )

    addButton(form, "Back", on_click=fm.wrapClick(player, lambda: openRankList(plugin, player), "back"))
    fm.sendForm(player, form, label=f"rank_detail:{rank_name}")


# ---------------------------------------------------------------------------
# Create Rank
# ---------------------------------------------------------------------------

def _openCreateRank(plugin: UtilityStone, player) -> None:
    fm = plugin.gui

    controls = [
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Rank Name", placeholder="e.g., vip, moderator"
        ),
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Priority", placeholder="e.g., 100"
        ),
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Prefix", placeholder="e.g., &6[VIP] "
        ),
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Suffix", placeholder="e.g., &r"
        ),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if not parsed or len(parsed) < 4:
            plugin.messages.failure(player, "Please fill in all fields.")
            fm.untrack(player)
            return

        name = str(parsed[0]).strip()
        if not name:
            plugin.messages.failure(player, "Rank name cannot be empty.")
            fm.untrack(player)
            return

        try:
            priority = int(str(parsed[1]).strip() or "0")
        except (ValueError, TypeError):
            priority = 0

        prefix = str(parsed[2]).strip()
        suffix = str(parsed[3]).strip()

        ok, msg = plugin.ranks.createRank(name, priority=priority, prefix=prefix, suffix=suffix)
        if ok:
            plugin.messages.success(player, msg)
        else:
            plugin.messages.failure(player, msg)
        fm.untrack(player)

    form = buildModal(
        "Create Rank",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, "rank_create"),
        submitText="Create",
    )
    fm.sendForm(player, form, label="rank_create_modal")


# ---------------------------------------------------------------------------
# Edit Priority
# ---------------------------------------------------------------------------

def _editPriority(plugin: UtilityStone, player, rank_name: str) -> None:
    fm = plugin.gui
    definition = plugin.ranks.getRankDefinition(rank_name)
    current = definition.get("priority", 0) if definition else 0

    controls = [
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Priority", placeholder="Higher = more important", default_value=str(current)
        ),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            try:
                new_pri = int(str(parsed[0]).strip())
            except (ValueError, TypeError):
                new_pri = current
            ok, msg = plugin.ranks.updateRank(rank_name, priority=new_pri)
            if ok:
                plugin.messages.success(player, f"Priority of '{rank_name}' set to {new_pri}.")
            else:
                plugin.messages.failure(player, msg)
        fm.untrack(player)

    form = buildModal(
        f"Edit Priority: {rank_name}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, f"rank_pri_edit:{rank_name}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"rank_pri_edit:{rank_name}")


# ---------------------------------------------------------------------------
# Edit Prefix
# ---------------------------------------------------------------------------

def _editPrefix(plugin: UtilityStone, player, rank_name: str) -> None:
    fm = plugin.gui
    definition = plugin.ranks.getRankDefinition(rank_name)
    current = definition.get("prefix", "") if definition else ""

    controls = [
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Prefix", placeholder="e.g., &6[VIP] ", default_value=current
        ),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            new_prefix = str(parsed[0])
            ok, msg = plugin.ranks.updateRank(rank_name, prefix=new_prefix)
            if ok:
                display = new_prefix or "(empty)"
                plugin.messages.success(player, f"Prefix of '{rank_name}' set to {display}.")
            else:
                plugin.messages.failure(player, msg)
        fm.untrack(player)

    form = buildModal(
        f"Edit Prefix: {rank_name}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, f"rank_prefix_edit:{rank_name}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"rank_prefix_edit:{rank_name}")


# ---------------------------------------------------------------------------
# Edit Suffix
# ---------------------------------------------------------------------------

def _editSuffix(plugin: UtilityStone, player, rank_name: str) -> None:
    fm = plugin.gui
    definition = plugin.ranks.getRankDefinition(rank_name)
    current = definition.get("suffix", "") if definition else ""

    controls = [
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Suffix", placeholder="e.g., &r", default_value=current
        ),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            new_suffix = str(parsed[0])
            ok, msg = plugin.ranks.updateRank(rank_name, suffix=new_suffix)
            if ok:
                display = new_suffix or "(empty)"
                plugin.messages.success(player, f"Suffix of '{rank_name}' set to {display}.")
            else:
                plugin.messages.failure(player, msg)
        fm.untrack(player)

    form = buildModal(
        f"Edit Suffix: {rank_name}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, f"rank_suffix_edit:{rank_name}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"rank_suffix_edit:{rank_name}")


# ---------------------------------------------------------------------------
# Edit Permissions
# ---------------------------------------------------------------------------

def _editPermissions(plugin: UtilityStone, player, rank_name: str) -> None:
    fm = plugin.gui
    definition = plugin.ranks.getRankDefinition(rank_name)
    current = definition.get("permissions", []) if definition else []

    controls = [
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Permissions (comma-separated)",
            placeholder="e.g., utilitystone.command.homes, utilitystone.command.kit",
            default_value=", ".join(current),
        ),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            raw = str(parsed[0]).strip()
            if raw:
                perms = [p.strip() for p in raw.split(",") if p.strip()]
            else:
                perms = []
            ok, msg = plugin.ranks.updateRank(rank_name, permissions=perms)
            if ok:
                plugin.messages.success(player, f"Permissions of '{rank_name}' updated ({len(perms)} nodes).")
            else:
                plugin.messages.failure(player, msg)
        fm.untrack(player)

    form = buildModal(
        f"Edit Permissions: {rank_name}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, f"rank_perms_edit:{rank_name}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"rank_perms_edit:{rank_name}")


# ---------------------------------------------------------------------------
# Edit Inheritance
# ---------------------------------------------------------------------------

def _editInheritance(plugin: UtilityStone, player, rank_name: str) -> None:
    fm = plugin.gui
    definition = plugin.ranks.getRankDefinition(rank_name)
    current = definition.get("inheritance", []) if definition else []

    all_ranks = plugin.ranks.listRanks()
    available = [r for r in all_ranks if r != rank_name]

    controls = [
        __import__("endstone.form", fromlist=["TextInput"]).TextInput(
            label="Inherit from (comma-separated)",
            placeholder=f"Available: {', '.join(available) if available else 'none'}",
            default_value=", ".join(current),
        ),
    ]

    def _onSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            raw = str(parsed[0]).strip()
            if raw:
                parents = [x.strip() for x in raw.split(",") if x.strip()]
            else:
                parents = []
            ok, msg = plugin.ranks.updateRank(rank_name, inheritance=parents)
            if ok:
                plugin.messages.success(player, f"Inheritance of '{rank_name}' updated.")
            else:
                plugin.messages.failure(player, msg)
        fm.untrack(player)

    form = buildModal(
        f"Edit Inheritance: {rank_name}",
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _onSubmit, f"rank_inherit_edit:{rank_name}"),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"rank_inherit_edit:{rank_name}")


# ---------------------------------------------------------------------------
# Delete Rank (with confirmation)
# ---------------------------------------------------------------------------

def _confirmDeleteRank(plugin: UtilityStone, player, rank_name: str) -> None:
    from endstone_utilitystone.ui.dialogs import askConfirmation

    def _doDelete(p):
        ok, msg = plugin.ranks.deleteRank(rank_name)
        if ok:
            plugin.messages.success(player, msg)
        else:
            plugin.messages.failure(player, msg)
        plugin.gui.untrack(player)

    askConfirmation(
        plugin,
        player,
        "Delete Rank",
        f"Are you sure you want to delete rank '{rank_name}'?",
        onYes=_doDelete,
    )
