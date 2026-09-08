"""
Regression tests for player-menu submenu content isolation.

Each submenu (Homes, Warps, Spawn, Teleport, Kits, Player Info, AFK,
Daily Reward, Admin Panel) must contain ONLY its own buttons — never
content from another section.

These tests reproduce the bug report:
    "Clicking Travel should open ONLY the Travel submenu. Instead, the
     resulting form contains Travel + Utilities + Admin content together."

The renderer is correct. The bug, if present, is in
player_menu.py / components.py / FormManager / navigation.py.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest
from typing import Any
from unittest import mock


# Force-load the worktree sources first so we don't accidentally pick up an
# older /root/utilitystone-fresh-server/.venv-installed endstone_utilitystone.
_WORKTREE_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(_WORKTREE_SRC) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_SRC))
for _name in list(sys.modules):
    if _name == "endstone_utilitystone" or _name.startswith("endstone_utilitystone."):
        del sys.modules[_name]


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

class _CapturingForm:
    """Records every add_* call made against an ActionForm."""

    def __init__(self, title: str = "", content: str = ""):
        self.title = title
        self.content = content
        self.buttons: list[dict[str, Any]] = []
        self.labels: list[dict[str, Any]] = []
        self.headers: list[dict[str, Any]] = []
        self.dividers: list[dict[str, Any]] = []

    def add_button(self, text: str, icon: str | None = None, on_click=None):
        self.buttons.append({"text": text, "icon": icon, "on_click": on_click})
        return self

    def add_label(self, text: str):
        self.labels.append({"text": text})
        return self

    def add_header(self, text: str):
        self.headers.append({"text": text})
        return self

    def add_divider(self):
        self.dividers.append({})
        return self


# A sentinel "form label" the test can compare against. The ActionForm
# constructor in real endstone.form accepts `title=`, `content=`, `on_submit=`,
# etc. We replace the form class wholesale so that any ActionForm(...) call
# returns a _CapturingForm instance.
class _FakeActionFormFactory:
    def __init__(self):
        self.created: list[_CapturingForm] = []

    def __call__(self, title: str = "", content: str = "", on_submit=None, **kwargs):
        form = _CapturingForm(title=title, content=content)
        self.created.append(form)
        return form


def _make_player(uid: str = "test-uid", name: str = "TestPlayer",
                 perm_keys: set[str] | None = None):
    """Player that grants permission iff perm_key is in perm_keys."""
    perm_keys = perm_keys or set()

    class _P:
        pass

    p = _P()
    p.name = name
    p.unique_id = uid
    p.is_valid = True
    p.health = 20.0
    p.max_health = 20.0
    # _openPlayerInfo uses player.location; provide a stub.
    p.location = type(
        "Loc",
        (),
        {
            "dimension": type("Dim", (), {"name": type("N", (), {"title": lambda self: "Overworld"})()})(),
            "block_x": 0, "block_y": 64, "block_z": 0,
        },
    )()
    p.game_mode = type("GM", (), {"name": type("N", (), {"title": lambda self: "Survival"})()})()
    p.ping = 0
    p.messages: list[str] = []
    def _perm(k): return k in perm_keys
    p.has_permission = _perm
    p.send_message = lambda m: p.messages.append(m)
    p.perform_command = lambda c: None
    p.ignored = []
    p.first_seen = 0.0
    p.last_seen = 0.0
    p.playtime = 0.0
    return p


def _make_plugin_stub(player, **services):
    """Build a UtilityStone stand-in with the minimum attributes
    player_menu.py / daily_rewards.py / admin_menu.py / ranks.py / etc.
    rely on. Returns (plugin, sent_forms) where sent_forms captures every
    form sent to the player."""

    sent: list[_CapturingForm] = []

    class _P:
        pass

    p = _P()
    p.gui = mock.MagicMock()
    p.gui.sendForm = mock.MagicMock(side_effect=lambda player_arg, form, label="": sent.append(form) or True)
    p.gui.wrapClick = lambda player, callback, label="": (lambda x: callback())

    # Service stubs
    p.homes = services.get("homes") or _ServiceStub(nameList=lambda *a, **kw: [], limitFor=lambda *a, **kw: 3)
    p.warps = services.get("warps") or _ServiceStub(visibleTo=lambda *a, **kw: [])
    p.spawns = services.get("spawns") or _ServiceStub()
    p.teleports = services.get("teleports") or _ServiceStub(incomingFor=lambda *a, **kw: [])
    p.kits = services.get("kits") or _ServiceStub(availableTo=lambda *a, **kw: [])
    p.dailyRewards = services.get("dailyRewards")  # may be None
    p.ranks = services.get("ranks") or _ServiceStub()
    p.sessions = services.get("sessions") or _ServiceStub(of=lambda *a, **kw: None)
    p.messages = _MessagesStub()
    p.profiles = services.get("profiles") or _ServiceStub(profileFor=lambda *a, **kw: {"firstSeen": 0.0, "lastSeen": 0.0, "playtime": 0.0})
    p.punishments = services.get("punishments") or _ServiceStub(muteFor=lambda *a, **kw: None)
    p.safeareas = services.get("safeareas") or _ServiceStub()
    p.server = _ServerStub()

    # The Navigator — must provide openPlayerMenu / openAdminPanel etc.
    nav = mock.MagicMock()
    nav.openPlayerMenu = mock.MagicMock(side_effect=lambda pl: _make_submenu_stub(p, pl, label="player_menu"))
    nav.openAdminPanel = mock.MagicMock(side_effect=lambda pl: _make_submenu_stub(p, pl, label="admin_panel"))
    p.gui.navigator = nav

    return p, sent


class _ServiceStub:
    """Generic service stub.

    All attributes default to callables that return None / [] / empty.
    Pass keyword args to override specific attributes (which become
    plain instance attributes, shadowing the default callables).
    """
    def __init__(self, **overrides):
        for k, v in overrides.items():
            setattr(self, k, v)

    def _default(self, *a, **kw):
        return None

    def __getattr__(self, name):
        # Returns a no-op callable for any method call.
        return self._default


class _MessagesStub:
    def info(self, *a, **kw): pass
    def success(self, *a, **kw): pass
    def failure(self, *a, **kw): pass
    def warn(self, *a, **kw): pass
    def notice(self, *a, **kw): pass


class _ServerStub:
    logger = _MessagesStub()
    online_players = []
    scheduler = _ServiceStub(run_task=lambda *a, **kw: type("Task", (), {"task_id": 1})())


def _make_submenu_stub(plugin, player, label=""):
    """A fake 'send_form' that records a submenu open and returns True."""
    f = _CapturingForm(title=label)
    plugin.gui._sent_forms.append(f)
    return True


# ---------------------------------------------------------------------------
# Patches applied at test-instance level (setUp/tearDown) to avoid leaking
# the fake ActionForm into other test modules.
# ---------------------------------------------------------------------------

# Per-test factory instance (a new factory for every test, so the "created"
# list starts empty).
def _new_factory():
    return _FakeActionFormFactory()


class _ModulePatcher:
    """Replaces endstone.form.ActionForm and components.ActionForm on
    __enter__ and restores them on __exit__."""

    def __enter__(self):
        import endstone.form as _ef
        import endstone_utilitystone.ui.components as _comp
        self._ef = _ef
        self._comp = _comp
        self._saved_ef = _ef.ActionForm
        self._saved_comp = _comp.ActionForm
        factory = _new_factory()
        _ef.ActionForm = factory
        _comp.ActionForm = factory
        self.factory = factory
        return factory

    def __exit__(self, *exc):
        self._ef.ActionForm = self._saved_ef
        self._comp.ActionForm = self._saved_comp


def setUpModule():
    # No-op. Patching happens per-test in PlayerMenuSubmenuIsolation.setUp.
    pass


def tearDownModule():
    # No-op. Patching is reverted per-test.
    pass


# ---------------------------------------------------------------------------
# Helper: assert a submenu contains only the expected button text labels
# ---------------------------------------------------------------------------

def _button_texts(form):
    return [b["text"] for b in form.buttons]


def _header_texts(form):
    return [h["text"] for h in form.headers]


# ---------------------------------------------------------------------------
# Player-menu isolation tests
# ---------------------------------------------------------------------------

class PlayerMenuSubmenuIsolation(unittest.TestCase):
    """Each submenu function must populate a fresh form with only its own items."""

    def setUp(self):
        from endstone_utilitystone.ui import player_menu, daily_rewards
        from endstone_utilitystone.ui.permissions import hasAdminGui

        # Patch ActionForm (both endstone.form.ActionForm and the symbol
        # components.py already imported at module-load time) for the
        # duration of this test only.
        self._patcher = _ModulePatcher()
        self._patcher.__enter__()

        # Build a player with FULL permissions (admin + all commands).
        self.player = _make_player(perm_keys={
            "utilitystone.command.homes",
            "utilitystone.command.warp",
            "utilitystone.command.spawn",
            "utilitystone.command.tpa",
            "utilitystone.command.kit",
            "utilitystone.command.afk",
            "utilitystone.command.dailyreward",
            "utilitystone.admin.gui",
            "utilitystone.admin.dailyrewards.view",
        })

        # Build plugin stub with minimal services.
        self.plugin, self.sent = _make_plugin_stub(self.player)

        # Override gui.sendForm to capture forms as a list, not MagicMock.
        self.sent_forms: list[_CapturingForm] = []
        self.plugin.gui.sendForm = lambda player_arg, form, label="": self.sent_forms.append(form) or True
        # Override send_form on the captured player so it doesn't error.
        self.player.send_form = lambda f: None

        self.player_menu = player_menu
        self.daily_rewards = daily_rewards

    def tearDown(self):
        # Restore the real ActionForm so other test modules aren't affected.
        self._patcher.__exit__(None, None, None)

    # ---- Helpers to dispatch a submenu ----------------------------------

    def _build_main(self):
        return self.player_menu.openPlayerMenu(self.plugin, self.player)

    def _dispatch(self, callback):
        """Invoke a click callback from a button in the main menu.
        Returns the resulting submenu form, if any."""
        # The Main menu uses inner _build closures; we re-call _openHomes etc.
        callback()
        return self.sent_forms[-1] if self.sent_forms else None

    # ---- Tests --------------------------------------------------------

    def test_main_menu_contains_only_main_buttons(self):
        form = self.sent_forms[-1] if self.sent_forms else None
        # No main menu yet — open it.
        self._build_main()
        form = self.sent_forms[-1]

        button_texts = _button_texts(form)
        header_texts = _header_texts(form)

        # Main menu now exposes only SECTION buttons (Travel, Warps,
        # Utilities) plus Admin Panel. The leaf items live inside
        # their respective section submenus.
        for required in ("Travel", "Warps", "Utilities", "Admin Panel"):
            self.assertIn(required, button_texts,
                          f"main menu missing section button {required!r}")

        # Main menu must NOT contain any sub-submenu leaf items.
        forbidden_in_main = (
            "Homes",       # travel submenu
            "Spawn",       # travel submenu
            "TPA",         # teleport submenu
            "Kits",        # utilities submenu
            "Player Info", # utilities submenu
            "AFK",         # utilities submenu
            "Daily Reward",  # utilities submenu
            "Reload Config",  # admin submenu
            "Configuration",  # admin submenu
            "Server Tools",  # admin submenu
            "Back to Menu",  # admin submenu
        )
        for f in forbidden_in_main:
            self.assertNotIn(f, button_texts,
                             f"main menu leaked submenu item {f!r}")

    def test_open_homes_produces_only_homes_content(self):
        from endstone_utilitystone.ui.player_menu import _openHomes
        # Open the main menu first.
        self._build_main()
        # Then dispatch the Homes callback.
        _openHomes(self.plugin, self.player)
        homes_form = self.sent_forms[-1]

        # Homes form should NOT contain content from other sections.
        button_texts = _button_texts(homes_form)
        header_texts = _header_texts(homes_form)

        # Forbidden: Travel / Teleport / Utilities / Admin section content.
        forbidden_buttons = ("Warps", "Spawn", "TPA", "Kits", "Player Info",
                             "AFK", "Daily Reward", "Admin Panel")
        for fb in forbidden_buttons:
            self.assertNotIn(fb, button_texts,
                             f"_openHomes leaked {fb!r} button from another section")

        forbidden_headers = ("Teleport", "Utilities", "Server Tools")
        for fh in forbidden_headers:
            self.assertNotIn(fh, header_texts,
                             f"_openHomes leaked {fh!r} header from another section")

    def test_open_warps_produces_only_warps_content(self):
        from endstone_utilitystone.ui.player_menu import _openWarps
        self._build_main()
        _openWarps(self.plugin, self.player)
        warps_form = self.sent_forms[-1]

        button_texts = _button_texts(warps_form)
        header_texts = _header_texts(warps_form)

        forbidden_buttons = ("Homes", "Spawn", "TPA", "Kits", "Player Info",
                             "AFK", "Daily Reward", "Admin Panel", "Create Home")
        for fb in forbidden_buttons:
            self.assertNotIn(fb, button_texts,
                             f"_openWarps leaked {fb!r} button from another section")

        forbidden_headers = ("Travel", "Teleport", "Utilities", "Server Tools")
        for fh in forbidden_headers:
            self.assertNotIn(fh, header_texts,
                             f"_openWarps leaked {fh!r} header from another section")

    def test_open_teleport_produces_only_teleport_content(self):
        from endstone_utilitystone.ui.player_menu import _openTeleport
        self._build_main()
        _openTeleport(self.plugin, self.player)
        tele_form = self.sent_forms[-1]

        button_texts = _button_texts(tele_form)
        header_texts = _header_texts(tele_form)

        # Teleport submenu contains TPA-to-* and TPAHERE-* buttons.
        # It must NOT contain Homes/Warps/Spawn/Kits/AFK/Admin.
        forbidden_buttons = ("Homes", "Warps", "Spawn", "Kits", "Player Info",
                             "AFK", "Daily Reward", "Admin Panel", "Create Home")
        for fb in forbidden_buttons:
            self.assertNotIn(fb, button_texts,
                             f"_openTeleport leaked {fb!r} button from another section")

        forbidden_headers = ("Travel", "Utilities", "Server Tools")
        for fh in forbidden_headers:
            self.assertNotIn(fh, header_texts,
                             f"_openTeleport leaked {fh!r} header from another section")

    def test_open_player_info_produces_only_player_info_content(self):
        from endstone_utilitystone.ui.player_menu import _openPlayerInfo
        self._build_main()
        _openPlayerInfo(self.plugin, self.player)
        info_form = self.sent_forms[-1]

        button_texts = _button_texts(info_form)
        header_texts = _header_texts(info_form)

        forbidden_buttons = ("Homes", "Warps", "Spawn", "TPA", "Kits",
                             "AFK", "Daily Reward", "Admin Panel", "Create Home")
        for fb in forbidden_buttons:
            self.assertNotIn(fb, button_texts,
                             f"_openPlayerInfo leaked {fb!r} button from another section")

        forbidden_headers = ("Travel", "Teleport", "Utilities", "Server Tools")
        for fh in forbidden_headers:
            self.assertNotIn(fh, header_texts,
                             f"_openPlayerInfo leaked {fh!r} header from another section")

    def test_open_travel_section_produces_only_travel_items(self):
        """The new _openTravel section opener must produce only Travel items."""
        from endstone_utilitystone.ui.player_menu import _openTravel
        _openTravel(self.plugin, self.player)
        self.assertTrue(self.sent_forms, "_openTravel did not send a form")
        form = self.sent_forms[-1]

        button_texts = _button_texts(form)
        header_texts = _header_texts(form)

        # Travel items: Homes, Warps, Spawn, Back.
        for required in ("Homes", "Warps", "Spawn", "Back"):
            self.assertIn(required, button_texts,
                          f"_openTravel missing {required!r}")

        # Travel section MUST NOT contain items from other sections.
        forbidden_in_travel = ("TPA", "Kits", "Player Info", "AFK",
                                "Daily Reward", "Admin Panel")
        for fb in forbidden_in_travel:
            self.assertNotIn(fb, button_texts,
                             f"_openTravel leaked {fb!r} from another section")

        # Forbidden headers.
        for fh in ("Teleport", "Utilities", "Server Tools"):
            self.assertNotIn(fh, header_texts,
                             f"_openTravel leaked {fh!r} header")

        # Title must be "Travel" or close to it.
        self.assertIn(form.title, ("Travel",))

    def test_open_teleport_section_produces_only_teleport_items(self):
        """The new Teleport section opener must produce only Teleport items."""
        from endstone_utilitystone.ui.player_menu import _openTeleport
        _openTeleport(self.plugin, self.player)
        self.assertTrue(self.sent_forms)
        form = self.sent_forms[-1]

        button_texts = _button_texts(form)
        header_texts = _header_texts(form)

        # TPA sends TPA-to-PlayerName buttons (only if there are other players
        # online, which there aren't in our mock, so only headers + Back).
        self.assertIn("Back", button_texts)

        # Travel items must NOT appear.
        forbidden_in_tele = ("Homes", "Warps", "Spawn", "Kits", "Player Info",
                              "AFK", "Daily Reward", "Admin Panel")
        for fb in forbidden_in_tele:
            self.assertNotIn(fb, button_texts,
                             f"_openTeleport leaked {fb!r} from another section")

        for fh in ("Travel", "Utilities", "Server Tools"):
            self.assertNotIn(fh, header_texts,
                             f"_openTeleport leaked {fh!r} header")

        self.assertEqual(form.title, "Teleport")

    def test_open_utilities_section_produces_only_utilities_items(self):
        """The new _openUtilities section opener must produce only Utilities items."""
        from endstone_utilitystone.ui.player_menu import _openUtilities
        _openUtilities(self.plugin, self.player)
        self.assertTrue(self.sent_forms)
        form = self.sent_forms[-1]

        button_texts = _button_texts(form)
        header_texts = _header_texts(form)

        # Utilities items: Kits, Player Info, AFK, Daily Reward, Homes, Teleport, Back.
        for required in ("Player Info", "Back"):
            self.assertIn(required, button_texts,
                          f"_openUtilities missing {required!r}")

        # Non-utility items must NOT appear.
        forbidden_in_util = ("Admin Panel", "Create Home")
        for fb in forbidden_in_util:
            self.assertNotIn(fb, button_texts,
                             f"_openUtilities leaked {fb!r} from another section")

        for fh in ("Travel", "Teleport", "Server Tools"):
            self.assertNotIn(fh, header_texts,
                             f"_openUtilities leaked {fh!r} header")

        self.assertEqual(form.title, "Utilities")

    def test_open_kits_produces_only_kits_content(self):
        from endstone_utilitystone.ui.player_menu import _openKits
        # Make a player with kit access.
        player = _make_player(perm_keys={"utilitystone.command.kit"})
        plugin, sent = _make_plugin_stub(player)
        sent_forms: list[_CapturingForm] = []
        plugin.gui.sendForm = lambda pl, f, label="": sent_forms.append(f) or True
        from endstone_utilitystone.ui.player_menu import openPlayerMenu
        openPlayerMenu(plugin, player)
        _openKits(plugin, player)
        kits_form = sent_forms[-1]

        button_texts = _button_texts(kits_form)
        header_texts = _header_texts(kits_form)

        forbidden_buttons = ("Homes", "Warps", "Spawn", "TPA", "Player Info",
                             "AFK", "Daily Reward", "Admin Panel", "Create Home")
        for fb in forbidden_buttons:
            self.assertNotIn(fb, button_texts,
                             f"_openKits leaked {fb!r} button from another section")

        forbidden_headers = ("Travel", "Teleport", "Utilities", "Server Tools")
        for fh in forbidden_headers:
            self.assertNotIn(fh, header_texts,
                             f"_openKits leaked {fh!r} header from another section")

    def test_admin_panel_only_admin_buttons(self):
        """Admin Panel opens via Navigator.openAdminPanel -> admin_menu.openAdminPanel.

        Admin panel content must NOT include Travel/Teleport/Utilities/Player Menu items
        (except "Back to Menu", which is the explicit return-to-player-menu button).
        """
        from endstone_utilitystone.ui.admin_menu import openAdminPanel
        plugin, sent = _make_plugin_stub(self.player)
        sent_forms: list[_CapturingForm] = []
        plugin.gui.sendForm = lambda pl, f, label="": sent_forms.append(f) or True

        # We need the admin_menu module to find the player_menu module — patch it
        # so the Back callback doesn't recurse into Navigator.openPlayerMenu
        # (which is already mocked to no-op).
        openAdminPanel(plugin, self.player)
        admin_form = sent_forms[-1]

        button_texts = _button_texts(admin_form)

        # Admin panel must contain admin entries:
        for required in ("Player Management", "Homes", "Warps", "Spawn", "Kits",
                         "Safe Areas", "Ranks", "Daily Rewards"):
            self.assertIn(required, button_texts,
                          f"admin panel missing {required!r}")

        # Admin panel must NOT contain player-only items (Travel submenu items,
        # TPA submenu items, Utilities-specific items like AFK).
        forbidden_in_admin = ("TPA", "AFK", "Daily Reward")  # 'Daily Reward' w/o 's'
        for f in forbidden_in_admin:
            self.assertNotIn(f, button_texts,
                             f"openAdminPanel leaked {f!r} from player menu")


# ---------------------------------------------------------------------------
# Server Menu & Navigation Back-Flow Verification
# ---------------------------------------------------------------------------

class TestServerMenuAndNavigation(unittest.TestCase):
    """Verify Server Menu title, submenus, navigation back-flow, permission gating, and utilities expansion."""

    def setUp(self):
        from endstone_utilitystone.ui import player_menu
        self._patcher = _ModulePatcher()
        self._patcher.__enter__()
        self.player_menu = player_menu

    def tearDown(self):
        self._patcher.__exit__(None, None, None)

    def test_server_menu_title(self):
        player = _make_player()
        plugin, sent = _make_plugin_stub(player)
        self.player_menu.openPlayerMenu(plugin, player)
        form = sent[-1]
        from endstone_utilitystone.ui.components import UST_MARKER
        self.assertTrue(form.title.startswith(UST_MARKER))
        visible_title = form.title[len(UST_MARKER):]
        self.assertEqual(visible_title, "Server Menu")

    def test_admin_panel_hidden_for_non_admins(self):
        non_admin = _make_player(perm_keys={"utilitystone.command.homes"})
        plugin, sent = _make_plugin_stub(non_admin)
        self.player_menu.openPlayerMenu(plugin, non_admin)
        form = sent[-1]
        button_texts = _button_texts(form)
        self.assertNotIn("Admin Panel", button_texts)

    def test_admin_panel_visible_for_admins(self):
        admin = _make_player(perm_keys={"utilitystone.admin.gui", "utilitystone.command.homes"})
        plugin, sent = _make_plugin_stub(admin)
        self.player_menu.openPlayerMenu(plugin, admin)
        form = sent[-1]
        button_texts = _button_texts(form)
        self.assertIn("Admin Panel", button_texts)

    def test_utilities_permission_gating(self):
        from endstone_utilitystone.ui.player_menu import _openUtilities
        # Player with ONLY kit permission
        player = _make_player(perm_keys={"utilitystone.command.kit"})
        plugin, sent = _make_plugin_stub(player)
        _openUtilities(plugin, player)
        form = sent[-1]
        button_texts = _button_texts(form)
        self.assertIn("Kits", button_texts)
        self.assertIn("Player Info", button_texts)
        self.assertNotIn("Daily Reward", button_texts)
        self.assertNotIn("Homes", button_texts)
        self.assertNotIn("Teleport", button_texts)
        self.assertNotIn("AFK", button_texts)

    def test_navigation_back_flow(self):
        """Verify Server Menu -> Submenu -> Back -> Server Menu flow."""
        player = _make_player(perm_keys={
            "utilitystone.command.homes",
            "utilitystone.command.warp",
            "utilitystone.command.spawn",
            "utilitystone.command.kit",
            "utilitystone.admin.gui",
        })
        plugin, sent = _make_plugin_stub(player)
        from endstone_utilitystone.ui.player_menu import openPlayerMenu, _openTravel, _openWarps, _openUtilities
        plugin.gui.navigator.openPlayerMenu = lambda pl: openPlayerMenu(plugin, pl)

        # 1. Travel -> Back
        _openTravel(plugin, player)
        travel_form = sent[-1]
        back_btn = [b for b in travel_form.buttons if b["text"] == "Back"][0]
        back_btn["on_click"](player)
        from endstone_utilitystone.ui.components import UST_MARKER
        self.assertTrue(sent[-1].title.endswith("Server Menu"))

        # 2. Warps -> Back
        _openWarps(plugin, player)
        warps_form = sent[-1]
        back_btn = [b for b in warps_form.buttons if b["text"] == "Back"][0]
        back_btn["on_click"](player)
        self.assertTrue(sent[-1].title.endswith("Server Menu"))

        # 3. Utilities -> Back
        _openUtilities(plugin, player)
        utils_form = sent[-1]
        back_btn = [b for b in utils_form.buttons if b["text"] == "Back"][0]
        back_btn["on_click"](player)
        self.assertTrue(sent[-1].title.endswith("Server Menu"))

        # 4. Admin Panel -> Back
        from endstone_utilitystone.ui.admin_menu import openAdminPanel
        openAdminPanel(plugin, player)
        admin_form = sent[-1]
        back_btn = [b for b in admin_form.buttons if b["text"] == "Back to Menu"][0]
        back_btn["on_click"](player)
        self.assertTrue(sent[-1].title.endswith("Server Menu"))


# ---------------------------------------------------------------------------
# Cross-call pollution regression
# ---------------------------------------------------------------------------

class FormStateIsolationAcrossCalls(unittest.TestCase):
    """Calling multiple _openXxx in sequence must not pollute later forms."""

    def setUp(self):
        from endstone_utilitystone.ui import player_menu
        self._patcher = _ModulePatcher()
        self._patcher.__enter__()

        self.player = _make_player(perm_keys={
            "utilitystone.command.homes", "utilitystone.command.warp",
            "utilitystone.command.spawn", "utilitystone.command.tpa",
            "utilitystone.command.kit", "utilitystone.command.afk",
            "utilitystone.command.dailyreward",
        })
        self.plugin, _ = _make_plugin_stub(self.player)
        self.player_menu = player_menu
        self.sent_forms: list[_CapturingForm] = []
        self.plugin.gui.sendForm = lambda pl, f, label="": self.sent_forms.append(f) or True

    def tearDown(self):
        self._patcher.__exit__(None, None, None)

    def test_no_pollution_across_consecutive_calls(self):
        from endstone_utilitystone.ui.player_menu import (
            _openHomes, _openWarps, _openTeleport,
            _openKits, _openPlayerInfo, _openTravel, _openUtilities,
        )

        # Sequence: main -> Travel -> Homes -> Warps -> Teleport -> Utilities ->
        # Kits -> PlayerInfo. Every submenu must produce only its own items.
        self.player_menu.openPlayerMenu(self.plugin, self.player)
        _openTravel(self.plugin, self.player)
        travel_form = self.sent_forms[-1]
        _openHomes(self.plugin, self.player)
        homes_form = self.sent_forms[-1]
        _openWarps(self.plugin, self.player)
        warps_form = self.sent_forms[-1]
        _openTeleport(self.plugin, self.player)
        tele_form = self.sent_forms[-1]
        _openUtilities(self.plugin, self.player)
        utilities_form = self.sent_forms[-1]
        _openKits(self.plugin, self.player)
        kits_form = self.sent_forms[-1]
        _openPlayerInfo(self.plugin, self.player)
        info_form = self.sent_forms[-1]

        forms = [travel_form, homes_form, warps_form, tele_form,
                 utilities_form, kits_form, info_form]
        for f in forms:
            self.assertIsNotNone(f, "form missing in sequence")

        # Each form is a different instance.
        unique_ids = {id(f) for f in forms}
        self.assertEqual(len(unique_ids), len(forms),
                         f"Forms share instances: {len(unique_ids)} unique of {len(forms)}")

        # Travel and Utilities share Back and Homes.
        travel_texts = set(_button_texts(travel_form))
        utilities_texts = set(_button_texts(utilities_form))
        shared = travel_texts & utilities_texts
        self.assertIn("Back", shared)

        # Travel form must NOT contain Teleport / Utilities items.
        for forbidden in ("TPA", "Kits", "Player Info", "AFK", "Daily Reward"):
            self.assertNotIn(forbidden, travel_texts,
                             f"Travel form contains {forbidden!r}")

        # Utilities form must NOT contain Warps / Spawn items.
        for forbidden in ("Warps", "Spawn"):
            self.assertNotIn(forbidden, utilities_texts,
                             f"Utilities form contains {forbidden!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)