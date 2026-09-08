"""
UST Bridge Test integration surface
====================================

This module is the **smallest possible public API** that UtilityStone
exposes to integration plugins such as `endstone_ust_bridge_test`.

It is intentionally tiny. It does NOT expose:

    * home / / / / /
    * business logic
    * service objects
    * navigation
    * config
    * permissions beyond the bare minimum needed to gate a test form

The only thing an integration plugin gets is a single method:

    USTBridgeIntegration.open_test_form(player) -> bool

That method opens a real UtilityStone ActionForm built by the same
`stylePlayerMenu()` / `FormManager` / `wrapClick()` pipeline that
`/menu` uses. Because the form's title is prefixed with `UST_MARKER`,
the resource pack's UST renderer draws the panel; because the buttons
are added through `form.add_button(...)` with `fm.wrapClick(...)`
callbacks, the resulting clicks are dispatched back through UtilityStone's
real on_submit / on_click mechanism.

The integration does NOT duplicate any menu code. The form itself is
just three test buttons (TRAVEL / WARPS / CLOSE) that exercise the
critical pipeline path:

    * TRAVEL mirrors the "open sub-menu" path used by Homes/Warps/Kits.
    * WARPS mirrors the "permission-gated feature" path used by
      homes/warps/spawn/tpa/kit/afk.
    * CLOSE mirrors the form-close path.

The integration is resolved from Endstone's PluginManager so an
integration plugin does not need to hard-code a reference to the
UtilityStone instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from endstone_utilitystone.ui.components import (
    addButton,
    addLabel,
    stylePlayerMenu,
)

if TYPE_CHECKING:
    from endstone.plugin import PluginManager

    from endstone_utilitystone.plugin import UtilityStone


# The plugin-name Endstone registers UtilityStone under. The dist name
# is "endstone-utilitystone" and the entry-point name is "utilitystone"
# so the Endstone PluginManager registers it under "utilitystone".
UTILITYSTONE_PLUGIN_NAME = "utilitystone"


class USTBridgeIntegration:
    """
    A thin handle into UtilityStone's UI pipeline, exposed to integration
    plugins for the UST Bridge Test proof-of-concept.

    An integration plugin obtains an instance via
    :meth:`from_plugin_manager` and then calls :meth:`open_test_form`.

    The class does NOT expose UtilityStone's services, navigator, or
    business logic. It only knows how to build and send one test form
    through UtilityStone's normal UI code path.
    """

    def __init__(self, plugin: "UtilityStone") -> None:
        self._plugin = plugin

    # ------------------------------------------------------------------
    # Resolution from Endstone's plugin manager
    # ------------------------------------------------------------------
    @classmethod
    def from_plugin_manager(
        cls, plugin_manager: "PluginManager"
    ) -> "USTBridgeIntegration | None":
        """
        Resolve the integration handle from Endstone's PluginManager.

        Returns ``None`` if UtilityStone is not currently loaded.

        Usage::

            integration = USTBridgeIntegration.from_plugin_manager(
                self.server.plugin_manager
            )
            if integration is None:
                self.logger.warning("UtilityStone is not loaded.")
                return
            integration.open_test_form(player)
        """
        plugin = plugin_manager.get_plugin(UTILITYSTONE_PLUGIN_NAME)
        if plugin is None:
            return None
        # Late import: this file is import-safe even when endstone_utilitystone
        # is not installed.
        from endstone_utilitystone.plugin import UtilityStone
        if not isinstance(plugin, UtilityStone):
            return None
        return cls(plugin)

    # ------------------------------------------------------------------
    # The single integration entry-point
    # ------------------------------------------------------------------
    def open_test_form(self, player) -> bool:
        """
        Open the UST Bridge Test form through UtilityStone's UI pipeline.

        The form is built by the same `stylePlayerMenu()` call that
        `/menu` uses, so it carries the UST marker and the resource pack
        will route it to UtilityStone's custom renderer.

        The buttons are added through the normal `addButton()` helper
        with `fm.wrapClick()` callbacks, so clicks are dispatched through
        UtilityStone's real on_submit mechanism.

        Returns ``True`` if the form was sent successfully, ``False`` if
        the GUI system is not yet ready.
        """
        plugin = self._plugin
        fm = plugin.gui
        if fm is None:
            plugin.logger.warning(
                "USTBridgeIntegration: UtilityStone GUI is not ready."
            )
            return False

        # stylePlayerMenu prepends UST_MARKER and uses UtilityStone's
        # protocol v1 marker. The resource pack's utilitystone.json will
        # therefore render the form using UtilityStone's renderer, NOT
        # the bridge test's diagnostic renderer.
        form = stylePlayerMenu("Server Menu", "Server navigation & utilities")

        # Button 0: TRAVEL — exercises the "open a sub-form" callback path.
        # The callback closes the current form and re-opens /menu so the
        # integration test confirms navigation still works through the
        # real UI pipeline.
        addButton(
            form,
            "TRAVEL",
            icon="textures/icons/LandClaims",
            on_click=fm.wrapClick(
                player,
                lambda: fm.navigator.openPlayerMenu(player),
                "bridge_test:travel",
            ),
        )

        # Button 1: WARPS — exercises the "permission-gated feature" path.
        # Permission failures are handled by hasPermission() in
        # player_menu._openWarps; the test only proves that the form
        # is wired through the same code path used in production.
        addButton(
            form,
            "WARPS",
            icon="textures/icons/TPA_Globe",
            on_click=fm.wrapClick(
                player,
                lambda: _open_warps_via_real_menu(plugin, player),
                "bridge_test:warps",
            ),
        )

        # Button 2: CLOSE — exercises the form-close path. No on_click;
        # the form's natural close behaviour is sufficient. A back-style
        # left-curved arrow is used to signal "leave this form".
        addButton(
            form,
            "CLOSE",
            icon="textures/icons/Arrow_Left_Curved",
        )

        return fm.sendForm(player, form, label="bridge_test")


def _open_warps_via_real_menu(plugin: "UtilityStone", player) -> None:
    """
    Helper invoked by the bridge-test WARPS button. Uses the *real*
    UtilityStone UI code path, not a re-implementation.
    """
    # Late import keeps the module import-safe.
    from endstone_utilitystone.ui.player_menu import _openWarps

    _openWarps(plugin, player)


# ----------------------------------------------------------------------
# Optional Protocol type for type-checkers
# ----------------------------------------------------------------------
class USTBridgeIntegrationLike(Protocol):
    """Type hint used by integration plugins for static analysis."""

    def open_test_form(self, player) -> bool: ...