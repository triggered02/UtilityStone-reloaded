from __future__ import annotations

from endstone.form import ActionForm, Label, Header, Divider, ModalForm, MessageForm


# Obsidian-style invisible title signatures. Each char is §-escaped so the whole
# token renders empty in-game; the §❖ prefix namespaces it so other resource
# packs cannot collide. The server_form.json factory detects these via
# bindings (#title_text - $signature).
SIGNATURE_COMMUNITY = "§❖§C§D"
SIGNATURE_ADMIN = "§❖§A§D"
SIGNATURE_COMMUNITY_MODAL = "§❖§C§X"
SIGNATURE_ADMIN_MODAL = "§❖§A§X"


def buildActionMenu(title: str, description: str = "") -> ActionForm:
    return ActionForm(title=title, content=description)


def stylePlayerMenu(title: str, description: str = "") -> ActionForm:
    """Build the /menu player ActionForm with the community styling signature.

    This is the ONLY signature used in PHASE 1. The token is invisible in-game
    but lets the resource pack select the Obsidian community panel.
    """
    return ActionForm(title=SIGNATURE_COMMUNITY + title, content=description)


def addButton(form: ActionForm, text: str, on_click=None, icon: str | None = None):
    return form.add_button(text, icon=icon, on_click=on_click)


def addLabel(form, text: str):
    return form.add_label(text)


def addHeader(form, text: str):
    return form.add_header(text)


def addDivider(form):
    return form.add_divider()


def emptyState(form: ActionForm, message: str, backCallback=None):
    addLabel(form, message)
    if backCallback is not None:
        addButton(form, "Back", on_click=backCallback)


def confirmAction(title: str, question: str, onYes, onNo=None) -> MessageForm:
    def _onSubmit(player, selection):
        if selection == 0:
            onYes(player)
        elif onNo is not None:
            onNo(player)

    form = MessageForm(
        title=title,
        content=question,
        button1="Yes",
        button2="No",
        on_submit=_onSubmit,
    )
    return form


def buildModal(title: str, controls: list, onSubmit, onClose=None, submitText: str | None = None) -> ModalForm:
    form = ModalForm(title=title, controls=controls, on_submit=onSubmit)
    if submitText is not None:
        form.submit_button = submitText
    if onClose is not None:
        form.on_close = onClose
    return form
