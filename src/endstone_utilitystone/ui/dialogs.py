from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from endstone.form import Label, TextInput

from endstone_utilitystone.ui.components import confirmAction

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


def askConfirmation(plugin: UtilityStone, player, title: str, question: str, onYes: Callable, onNo: Callable | None = None):
    form = confirmAction(title, question, lambda p: onYes(p), lambda p: onNo(p) if onNo else None)
    plugin.gui.sendForm(player, form, label=f"confirm:{title}")


def askTextInput(plugin: UtilityStone, player, title: str, label: str, placeholder: str, current: str, onSubmit: Callable[[str], None], onClose: Callable | None = None):
    from endstone_utilitystone.ui.components import buildModal
    from endstone_utilitystone.ui.manager import FormManager

    controls = [TextInput(label=label, placeholder=placeholder, default_value=current)]

    fm = plugin.gui

    def _handleSubmit(p, data):
        parsed = fm.parseModalData(data)
        if parsed and len(parsed) > 0:
            onSubmit(str(parsed[0]))

    def _handleClose(p):
        if onClose:
            onClose()

    form = buildModal(
        title=title,
        controls=controls,
        onSubmit=fm.wrapSubmit(player, _handleSubmit, title),
        onClose=fm.wrapClose(player, title) if onClose else fm.wrapClose(player, title),
        submitText="Save",
    )
    fm.sendForm(player, form, label=f"textinput:{title}")


def showError(plugin: UtilityStone, player, message: str):
    plugin.messages.failure(player, message)


def showSuccess(plugin: UtilityStone, player, message: str):
    plugin.messages.success(player, message)
