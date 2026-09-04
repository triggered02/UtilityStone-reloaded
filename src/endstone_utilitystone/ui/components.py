from __future__ import annotations

from endstone.form import ActionForm, Label, Header, Divider, ModalForm, MessageForm


# Obsidian-style invisible title signatures. Each char is §-escaped so the whole
# token renders empty in-game; the §❖ prefix namespaces it so other resource
# packs cannot collide. The server_form.json factory detects these via
# bindings (#title_text - $signature).
#
# COMMUNITY additionally carries the §a§№§r color-mode prefix that Obsidian's
# BP prepends before §❖§C§D. This makes the first 8 UTF-8 bytes of the title
# match the property_bag key "#§a§№", which resolves "c_button" and selects
# textures/ui/default_c_button.png for the button background. Without the prefix,
# the property_bag lookup misses and common.button falls back to its built-in visuals.
SIGNATURE_COMMUNITY = "§a§№§r§❖§C§D"
SIGNATURE_ADMIN = "§❖§A§D"
SIGNATURE_COMMUNITY_MODAL = "§❖§C§X"
SIGNATURE_ADMIN_MODAL = "§❖§A§X"

# UtilityStone UI Protocol v1 marker.
#
# This is a deterministic, invisible-to-player marker emitted at the start of
# /menu form titles. The server_form.json factory detects it via
# `not ((#title_text - $utilitystone) = #title_text)`.
#
# Unlike the COMMUNITY marker (which uses the §a§№§r color-token trick that
# happens to match a property_bag key), this marker does NOT rely on
# property_bag lookups or UTF-8 byte-counting. It is a stable, namespaced,
## §-escaped token.
#
# All six characters (§ ❖ § U § S § T § D) are Minecraft formatting escapes.
# §U/§S/§T/§D are not valid color codes, so they render as zero-width. The
# §❖ prefix namespaces the marker so other resource packs cannot collide.
UST_MARKER = "§❖§U§S§T§D"


def buildActionMenu(title: str, description: str = "") -> ActionForm:
    return ActionForm(title=title, content=description)


def stylePlayerMenu(title: str, description: str = "") -> ActionForm:
    """Build the /menu player ActionForm with the UtilityStone UI marker.

    The marker (UST_MARKER) is prepended to the title. The resource pack's
    server_form.json detects this marker via
    `(not ((#title_text - $utilitystone) = #title_text))` and routes the form
    to UtilityStone's custom renderer instead of vanilla / Obsidian fallback.
    """
    return ActionForm(title=UST_MARKER + title, content=description)


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
