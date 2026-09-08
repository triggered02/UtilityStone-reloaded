"""
Tests for the USTBridgeIntegration public API.

These tests prove:

    1. UtilityStone exposes a single public integration class
       (`USTBridgeIntegration`) at the package root and under
       `endstone_utilitystone.integrations`.
    2. The class is resolvable from Endstone's PluginManager via
       `from_plugin_manager`.
    3. The `open_test_form` method produces a real
       `endstone.form.ActionForm` whose title is prefixed with the
       real UtilityStone UST_MARKER (so the production resource-pack
       UST renderer fires).
    4. The integration does NOT expose services, navigator business
       methods, or other private attributes.
    5. Existing player_menu.py callbacks and Navigator methods remain
       unchanged (no regression).

NOTE on test isolation:

Endstone's `endstone.plugin.Plugin` is a C++ extension type. Calling
`UtilityStone()` registers the instance with the C++ runtime, and a
partially-constructed instance can segfault the interpreter at GC time.
To avoid this, the tests that need an actual UtilityStone instance are
written so the instance is fully constructed (gui + navigator) before
the test body runs, and the GC will tear it down cleanly afterwards.
"""

from __future__ import annotations

import inspect
import pathlib
import sys
import types
import unittest


_WORKTREE_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(_WORKTREE_SRC) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_SRC))


# ---------------------------------------------------------------------------
# 1. Importability
# ---------------------------------------------------------------------------
class TestIntegrationIsPublic(unittest.TestCase):
    """The integration class must be reachable from endstone_utilitystone.*."""

    def test_importable_from_package_root(self):
        from endstone_utilitystone import USTBridgeIntegration
        self.assertTrue(callable(USTBridgeIntegration))

    def test_importable_from_integrations_subpackage(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        self.assertTrue(callable(USTBridgeIntegration))

    def test_importable_from_integrations_ust_bridge(self):
        from endstone_utilitystone.integrations.ust_bridge import (
            USTBridgeIntegration,
        )
        self.assertTrue(callable(USTBridgeIntegration))

    def test_plugin_name_constant(self):
        from endstone_utilitystone.integrations.ust_bridge import (
            UTILITYSTONE_PLUGIN_NAME,
        )
        self.assertEqual(UTILITYSTONE_PLUGIN_NAME, "utilitystone")


# ---------------------------------------------------------------------------
# 2. Public surface
# ---------------------------------------------------------------------------
class TestIntegrationPublicSurface(unittest.TestCase):
    """The integration's public surface must be minimal."""

    def setUp(self):
        from endstone_utilitystone.integrations.ust_bridge import (
            USTBridgeIntegration,
        )
        self.cls = USTBridgeIntegration

    def test_class_has_expected_public_methods(self):
        # We tolerate dunders + classmethod + the two integration methods.
        public = [
            n for n in dir(self.cls)
            if not n.startswith("_") and callable(getattr(self.cls, n))
        ]
        self.assertIn("open_test_form", public)
        self.assertIn("from_plugin_manager", public)

    def test_does_not_expose_services(self):
        attrs = [n for n in dir(self.cls) if not n.startswith("_")]
        forbidden = ("homes", "warps", "ranks", "teleports",
                     "kits", "safeareas", "dailyRewards", "discord")
        for f in forbidden:
            self.assertFalse(
                hasattr(self.cls, f),
                f"USTBridgeIntegration must NOT expose {f!r}",
            )


# ---------------------------------------------------------------------------
# 3. Resolution from PluginManager
# ---------------------------------------------------------------------------
class TestIntegrationFromPluginManager(unittest.TestCase):
    """`from_plugin_manager` returns the integration or None."""

    def _make_pm(self, plugin):
        pm = types.SimpleNamespace()
        pm.get_plugin = lambda name: plugin if name == "utilitystone" else None
        return pm

    def _build_utilitystone_with_gui(self):
        """Build a fully-constructed UtilityStone (avoids native segfaults).

        Returns a (plugin, fm) pair. We keep the FormManager attached to
        the plugin instance so that Python's GC tears them down together
        cleanly.
        """
        from endstone_utilitystone.plugin import UtilityStone
        from endstone_utilitystone.ui.manager import FormManager
        from endstone_utilitystone.ui.navigation import Navigator
        plugin = UtilityStone()
        plugin.gui = FormManager(plugin)
        plugin.gui.navigator = Navigator(plugin.gui)
        return plugin

    def test_returns_integration_when_loaded(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        plugin = self._build_utilitystone_with_gui()
        handle = USTBridgeIntegration.from_plugin_manager(self._make_pm(plugin))
        self.assertIsNotNone(handle)
        self.assertIsInstance(handle, USTBridgeIntegration)

    def test_returns_none_when_not_loaded(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        handle = USTBridgeIntegration.from_plugin_manager(self._make_pm(None))
        self.assertIsNone(handle)

    def test_returns_none_for_wrong_plugin_type(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        fake_other = types.SimpleNamespace(name="something-else")
        handle = USTBridgeIntegration.from_plugin_manager(
            self._make_pm(fake_other)
        )
        self.assertIsNone(handle)


# ---------------------------------------------------------------------------
# 4. open_test_form produces a real UtilityStone ActionForm
# ---------------------------------------------------------------------------
class TestOpenTestForm(unittest.TestCase):
    """The integration must hand us a real UtilityStone ActionForm."""

    def setUp(self):
        from endstone_utilitystone.ui.manager import FormManager
        from endstone_utilitystone.ui.navigation import Navigator
        from endstone_utilitystone.plugin import UtilityStone

        # Build a fully-constructed UtilityStone so GC can tear it down
        # cleanly. We do NOT touch plugin.gui after this point.
        self.plugin = UtilityStone()
        self.plugin.gui = FormManager(self.plugin)
        self.plugin.gui.navigator = Navigator(self.plugin.gui)

        self.player = types.SimpleNamespace(
            unique_id="test-pid",
            name="TestPlayer",
            is_valid=True,
            has_permission=lambda p: True,
            send_message=lambda m: None,
            perform_command=lambda c: None,
        )

        # Capture dict shared with the patched instance method.
        self._captured = {"form": None, "label": None}

        fm = self.plugin.gui

        def fake_send(player, form, label=""):
            self._captured["form"] = form
            self._captured["label"] = label
            return True

        fm.sendForm = fake_send

    def test_open_test_form_returns_true(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        integration = USTBridgeIntegration(self.plugin)
        result = integration.open_test_form(self.player)
        self.assertTrue(result)

    def test_open_test_form_uses_real_ActionForm(self):
        from endstone.form import ActionForm
        from endstone_utilitystone.integrations import USTBridgeIntegration
        integration = USTBridgeIntegration(self.plugin)
        integration.open_test_form(self.player)
        form = self._captured["form"]
        self.assertIsInstance(form, ActionForm)

    def test_open_test_form_title_has_ust_marker(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        from endstone_utilitystone.ui.components import UST_MARKER
        integration = USTBridgeIntegration(self.plugin)
        integration.open_test_form(self.player)
        form = self._captured["form"]
        self.assertTrue(
            form.title.startswith(UST_MARKER),
            f"Form title {form.title!r} must start with UST_MARKER {UST_MARKER!r}",
        )

    def test_open_test_form_title_visible_part(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        from endstone_utilitystone.ui.components import UST_MARKER
        integration = USTBridgeIntegration(self.plugin)
        integration.open_test_form(self.player)
        form = self._captured["form"]
        visible = form.title[len(UST_MARKER):]
        self.assertEqual(visible, "Server Menu")

    def test_open_test_form_uses_bridge_test_send_form_label(self):
        from endstone_utilitystone.integrations import USTBridgeIntegration
        integration = USTBridgeIntegration(self.plugin)
        integration.open_test_form(self.player)
        self.assertEqual(self._captured["label"], "bridge_test")

    def test_open_test_form_returns_false_when_gui_uninitialised(self):
        """If plugin.gui is None, open_test_form must return False.

        We use a plain stub plugin (NOT a UtilityStone instance) to avoid
        Endstone's native destructor segfaulting at GC time on a
        partially-constructed instance.
        """
        from endstone_utilitystone.integrations import USTBridgeIntegration
        stub = types.SimpleNamespace(
            gui=None,
            logger=types.SimpleNamespace(warning=lambda m: None),
        )
        integration = USTBridgeIntegration(stub)

        class _NoopPlayer:
            unique_id = "x"
            name = "x"
            def send_message(self, m): pass

        result = integration.open_test_form(_NoopPlayer())
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# 5. The integration is not duplicating player_menu logic
# ---------------------------------------------------------------------------
class TestIntegrationDoesNotDuplicateMenu(unittest.TestCase):
    """The integration must be tiny: it must not redefine player_menu code."""

    def test_no_player_menu_definitions_in_integration(self):
        path = (
            pathlib.Path(__file__).resolve().parent.parent
            / "src" / "endstone_utilitystone" / "integrations" / "ust_bridge.py"
        )
        source = path.read_text()
        self.assertNotIn("def _openHomes", source)
        self.assertNotIn("def _openWarps", source)
        self.assertNotIn("def _openKits", source)
        self.assertNotIn("def _openTeleport", source)
        self.assertNotIn("def _goHome", source)

    def test_integration_uses_form_manager_for_sending(self):
        path = (
            pathlib.Path(__file__).resolve().parent.parent
            / "src" / "endstone_utilitystone" / "integrations" / "ust_bridge.py"
        )
        source = path.read_text()
        self.assertIn("fm.sendForm", source)


# ---------------------------------------------------------------------------
# 6. Regression: existing UtilityStone behaviour unchanged
# ---------------------------------------------------------------------------
class TestNoRegression(unittest.TestCase):
    """Existing UtilityStone code paths must remain intact."""

    def test_player_menu_callbacks_intact(self):
        path = (
            pathlib.Path(__file__).resolve().parent.parent
            / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        )
        source = path.read_text()
        for needle in (
            "def _openHomes(",
            "def _openWarps(",
            "def _openKits(",
            "def _openTeleport(",
            "def _goHome(",
            "def _goWarp(",
            "def _claimKit(",
            "fm.wrapClick",
            "stylePlayerMenu",
            "buildActionMenu",
        ):
            self.assertIn(needle, source, f"player_menu.py missing {needle!r}")

    def test_navigator_intact(self):
        path = (
            pathlib.Path(__file__).resolve().parent.parent
            / "src" / "endstone_utilitystone" / "ui" / "navigation.py"
        )
        source = path.read_text()
        for needle in (
            "class Navigator",
            "def openPlayerMenu",
            "def openAdminPanel",
            "def openConfigEditor",
        ):
            self.assertIn(needle, source, f"navigation.py missing {needle!r}")

    def test_form_manager_intact(self):
        from endstone_utilitystone.ui.manager import FormManager
        sig = inspect.signature(FormManager.sendForm)
        params = list(sig.parameters.keys())
        self.assertEqual(params[:3], ["self", "player", "form"])
        self.assertEqual(params[3], "label")

    def test_stylePlayerMenu_intact(self):
        from endstone_utilitystone.ui.components import (
            stylePlayerMenu, UST_MARKER,
        )
        form = stylePlayerMenu("Foo", "Bar")
        self.assertTrue(form.title.startswith(UST_MARKER))
        self.assertEqual(form.title[len(UST_MARKER):], "Foo")
        self.assertEqual(form.content, "Bar")


if __name__ == "__main__":
    unittest.main(verbosity=2)