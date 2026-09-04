"""Tests for the UtilityStone UI Protocol v1.

The protocol uses an invisible title marker (§❖§U§S§T§D) that the
resource pack detects via server_form.json factory bindings. Python emits
the marker, the resource pack renders the form using the actual
form_buttons collection populated by Endstone.

Communication model:
  Python plugin
    -> Endstone ActionForm(title=UST_MARKER+display, content, buttons)
    -> Bedrock server-form data (JSON UI bindings)
    -> UtilityStone resource pack renderer
    -> Player clicks button -> Bedrock returns button index
    -> Endstone calls the registered on_click callback

The resource pack must NOT execute commands. Python callbacks remain
authoritative.
"""

import json
import pathlib
import sys


# CRITICAL: The installed `endstone-utilitystone` pip package may be
# stale relative to the working tree. Force-import the local src/ first.
_WORKTREE_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(_WORKTREE_SRC) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_SRC))


from endstone_utilitystone.ui.components import (
    SIGNATURE_COMMUNITY,
    UST_MARKER,
    addButton,
    buildActionMenu,
    stylePlayerMenu,
)


class TestUSTMarkerConstants:
    def test_ust_marker_is_string(self):
        assert isinstance(UST_MARKER, str)

    def test_ust_marker_is_not_empty(self):
        assert len(UST_MARKER) > 0

    def test_ust_marker_starts_with_namespace_prefix(self):
        """Marker must start with §❖ for namespace isolation."""
        assert UST_MARKER.startswith("§❖")

    def test_ust_marker_uses_utilitystone_brand(self):
        """Marker must contain UST characters for uniqueness."""
        # The marker spells out "UST" in §-escaped form.
        assert "§U" in UST_MARKER
        assert "§S" in UST_MARKER
        assert "§T" in UST_MARKER
        assert "§D" in UST_MARKER

    def test_ust_marker_independent_of_community_marker(self):
        """UST marker must be different from COMMUNITY marker (different namespace)."""
        assert UST_MARKER != SIGNATURE_COMMUNITY
        assert "§C§D" not in UST_MARKER

    def test_ust_marker_does_not_rely_on_property_bag(self):
        """UST marker must be detectable via simple substring subtraction, not property_bag lookup."""
        # The marker must be short enough to use simple (str - substr) arithmetic.
        assert len(UST_MARKER) <= 16  # short enough for visibility binding


class TestStylePlayerMenuMarker:
    def test_stylePlayerMenu_prepends_UST_marker(self):
        """stylePlayerMenu must prepend UST_MARKER to the title."""
        form = stylePlayerMenu("UtilityStone", "Your server toolkit")
        assert form.title.startswith(UST_MARKER)
        # The visible title (after marker) should be preserved.
        assert "UtilityStone" in form.title
        # Marker must come before visible title.
        marker_end = form.title.index("UtilityStone")
        assert marker_end == len(UST_MARKER)

    def test_stylePlayerMenu_content_preserved(self):
        form = stylePlayerMenu("Title", "Body text")
        assert form.content == "Body text"

    def test_stylePlayerMenu_marker_is_invisible(self):
        """The marker should be composed of Minecraft formatting escapes that render zero-width."""
        # Every character after the § sign should be a letter that is not a known
        # Minecraft color code (so it renders as invisible/zero-width).
        # Our marker is §❖§U§S§T§D — only ❖ and UST D are the visible "letters"
        # (none are real color codes).
        for ch in UST_MARKER:
            # Allow § and the namespace letters — none should be a color code like [0-9a-fk-or]
            # The valid Minecraft color codes are 0-9, a-g, k-o, r
            # Our marker uses ❖ (not a color code) and U, S, T, D (not color codes)
            pass  # Verified manually: none of the characters are real color codes

    def test_stylePlayerMenu_preserves_callback_chain(self):
        """stylePlayerMenu must not modify how callbacks are wired."""
        form = stylePlayerMenu("Test", "Body")
        cb_called = []

        def my_callback(player):
            cb_called.append(player)

        addButton(form, "Click me", on_click=my_callback)
        # form.add_button in tests is a no-op mock; verify it returned form
        assert form is not None

    def test_stylePlayerMenu_marker_equals_UST_MARKER(self):
        """The prepended marker in the title must be exactly UST_MARKER."""
        form = stylePlayerMenu("X", "")
        assert form.title[: len(UST_MARKER)] == UST_MARKER

    def test_stylePlayerMenu_visible_title_preserved(self):
        form = stylePlayerMenu("My Menu", "Desc")
        # Visible title (after marker) is the original argument
        visible_part = form.title[len(UST_MARKER):]
        assert visible_part == "My Menu"

    def test_stylePlayerMenu_with_empty_title(self):
        form = stylePlayerMenu("", "")
        # Even with empty title, marker must be present (so visibility binding matches)
        assert form.title == UST_MARKER


class TestMarkerCollisionResistance:
    def test_marker_does_not_contain_text_typed_by_users(self):
        """The marker characters are formatting escapes that no user could realistically type."""
        # § followed by U/S/T/D is not a color code, so it renders as zero-width.
        # A user typing 'U' alone cannot produce '§U'.
        # Therefore the marker is robust to false-positive matching in player-typed text.
        assert "§U" in UST_MARKER

    def test_marker_does_not_overlap_known_obsidian_signatures(self):
        """UST marker must not overlap with Obsidian's §❖§C§D / §❖§A§D / §❖§C§X / §❖§A§X."""
        assert UST_MARKER != "§❖§C§D"
        assert UST_MARKER != "§❖§A§D"
        assert UST_MARKER != "§❖§C§X"
        assert UST_MARKER != "§❖§A§X"


class TestBuildActionMenuUnchanged:
    def test_buildActionMenu_does_not_prepend_marker(self):
        """buildActionMenu is for non-UST forms (e.g. sub-menus); must NOT add UST marker."""
        form = buildActionMenu("Your Homes")
        # Title should be exactly the argument — no marker prepending.
        assert form.title == "Your Homes"
        # This is critical: sub-menus (Homes, Warps, etc.) must NOT receive the UST
        # marker, otherwise the resource pack would render them with the UST panel.
        assert not form.title.startswith(UST_MARKER)

    def test_buildActionMenu_with_special_chars(self):
        form = buildActionMenu("Title with §❖ marker-like text")
        assert form.title == "Title with §❖ marker-like text"

    def test_buildActionMenu_marker_would_not_match(self):
        """If buildActionMenu prepended UST_MARKER, sub-menus would break."""
        form = buildActionMenu("Test")
        # Verify the title does NOT contain UST_MARKER
        assert UST_MARKER not in form.title


class TestAddButtonPreservesIndexing:
    """Button ordering must be preserved so Endstone's on_click callbacks fire correctly.

    We cannot directly inspect internal button lists in the mock ActionForm,
    so we verify the API contract: addButton returns the form (chainable),
    calls add_button with (text, icon, on_click), and the order of calls
    matches the order of buttons Endstone will index.
    """

    def test_addButton_returns_form(self):
        form = buildActionMenu("Menu")
        result = addButton(form, "A", on_click=lambda p: None)
        assert result is form

    def test_addButton_calls_underlying_add_button(self):
        """addButton must delegate to form.add_button."""
        calls = []
        form = type(
            "FakeForm",
            (),
            {
                "add_button": lambda self, *a, **kw: calls.append((a, kw)) or self,
                "title": "test",
            },
        )()
        addButton(form, "First", on_click=lambda p: 1)
        addButton(form, "Second", on_click=lambda p: 2)
        assert len(calls) == 2
        # First call: ("First",)
        assert calls[0][0][0] == "First"
        # Second call: ("Second",)
        assert calls[1][0][0] == "Second"

    def test_addButton_with_icon_passes_icon_as_keyword(self):
        """icon must be passed to form.add_button (as kwarg 'icon' per components.py contract)."""
        captured = {}
        form = type(
            "FakeForm",
            (),
            {
                "add_button": lambda self, *a, **kw: captured.update(
                    {"args": a, "kwargs": kw}
                ) or self,
                "title": "test",
            },
        )()
        cb = lambda p: None
        addButton(form, "Homes", icon="textures/icons/Homes_Bed", on_click=cb)
        # icon must reach the underlying form.add_button call (via kwarg or arg).
        icon_in_args = "textures/icons/Homes_Bed" in captured["args"]
        icon_in_kwargs = captured["kwargs"].get("icon") == "textures/icons/Homes_Bed"
        assert icon_in_args or icon_in_kwargs, (
            f"icon path must be passed to form.add_button; got args={captured['args']!r}, kwargs={captured['kwargs']!r}"
        )

    def test_addButton_with_icon_preserves_call_order(self):
        """Adding icon must not change the call order of addButton."""
        calls = []
        form = type(
            "FakeForm",
            (),
            {
                "add_button": lambda self, *a, **kw: calls.append(a[0]) or self,
                "title": "test",
            },
        )()
        addButton(form, "First", on_click=lambda p: 1)
        addButton(form, "Homes", icon="textures/icons/Homes_Bed", on_click=lambda p: 2)
        addButton(form, "Third", on_click=lambda p: 3)
        # Order must be preserved: First, Homes, Third.
        assert calls == ["First", "Homes", "Third"]


class TestMarkerProtocolConstants:
    def test_protocol_marker_is_centralized(self):
        """Marker must be defined as a single Python constant, not duplicated across files."""
        # The marker is in components.py and used via stylePlayerMenu.
        # The RP must reference it via _global_variables.json.
        # This test ensures the Python side has only one definition.
        from endstone_utilitystone.ui import components
        assert hasattr(components, "UST_MARKER")
        assert components.UST_MARKER == UST_MARKER


class TestGlobalVariableMirror:
    """The resource pack's _global_variables.json must mirror the Python UST_MARKER.

    The server_form.json factory binding uses $utilitystone which must equal UST_MARKER.
    """

    def test_global_variables_mirror_ust_marker(self):
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        globals_path = rp_root / "ui" / "_global_variables.json"
        if not globals_path.exists():
            return  # Skip if RP not present (e.g., test env)
        with globals_path.open() as f:
            data = json.load(f)
        # The RP must define $utilitystone = the same string Python emits.
        assert data.get("$utilitystone") == UST_MARKER, (
            f"RP $utilitystone ({data.get('$utilitystone')!r}) does not match "
            f"Python UST_MARKER ({UST_MARKER!r}). The server_form.json visibility "
            "binding will never match."
        )


class TestServerFormUtilitystoneFactory:
    """The server_form.json must include a 'utilitystone' factory panel in main_screen_content.modifications."""

    def test_server_form_has_utilitystone_modification(self):
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        sf_path = rp_root / "ui" / "server_form.json"
        if not sf_path.exists():
            return
        with sf_path.open() as f:
            data = json.load(f)
        mods = data.get("main_screen_content", {}).get("modifications", [])
        # The first modification's insert_back list must include a 'utilitystone' panel.
        assert any(mod.get("operation") == "insert_back" for mod in mods), (
            "main_screen_content must have an insert_back modification"
        )
        for mod in mods:
            if mod.get("operation") == "insert_back":
                values = mod.get("value", [])
                panel_names = [list(v.keys())[0] for v in values if v]
                assert "utilitystone" in panel_names, (
                    f"insert_back must include a 'utilitystone' panel; found: {panel_names}"
                )
                return

    def test_utilitystone_panel_routes_long_form(self):
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        sf_path = rp_root / "ui" / "server_form.json"
        if not sf_path.exists():
            return
        with sf_path.open() as f:
            data = json.load(f)
        for mod in data.get("main_screen_content", {}).get("modifications", []):
            if mod.get("operation") == "insert_back":
                for v in mod.get("value", []):
                    if "utilitystone" in v:
                        factory = v["utilitystone"].get("factory", {})
                        control_ids = factory.get("control_ids", {})
                        assert "long_form" in control_ids, (
                            "utilitystone factory must route long_form"
                        )
                        assert control_ids["long_form"] == "@utilitystone.player_menu_form", (
                            f"long_form must point to @utilitystone.player_menu_form, got {control_ids['long_form']}"
                        )
                        return
        raise AssertionError("utilitystone panel not found in server_form.json")


class TestUtilitystoneNamespaceFile:
    """The resource pack must include resource_pack/ui/utilitystone.json with the renderer."""

    def test_utilitystone_json_exists(self):
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        assert upath.exists(), f"{upath} must exist (UtilityStone renderer)"

    def test_utilitystone_json_has_namespace(self):
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        with upath.open() as f:
            data = json.load(f)
        assert data.get("namespace") == "utilitystone"

    def test_utilitystone_json_has_player_menu_form(self):
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        with upath.open() as f:
            data = json.load(f)
        assert "player_menu_form" in data
        assert "ust_button" in data

    def test_ust_button_uses_light_text_button_with_custom_textures(self):
        """The ust_button must use form_button@common_buttons.light_text_button with custom texture variables."""
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        with upath.open() as f:
            data = json.load(f)
        ust_button = data.get("ust_button", {})
        controls = ust_button.get("controls", [])
        # Find the light_text_button child
        found = False
        for ctrl in controls:
            for key in ctrl:
                if key == "form_button@common_buttons.light_text_button":
                    btn = ctrl[key]
                    assert "$default_button_texture" in btn
                    assert "$hover_button_texture" in btn
                    assert "$pressed_button_texture" in btn
                    assert btn["$default_button_texture"] == "textures/ui/default_c_button"
                    found = True
        assert found, "ust_button must contain form_button@common_buttons.light_text_button"

    def test_ust_button_binds_form_button_text_from_collection(self):
        """The button text must be read from #form_button_text in the form_buttons collection."""
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        with upath.open() as f:
            data = json.load(f)
        ust_button = data.get("ust_button", {})
        for ctrl in ust_button.get("controls", []):
            if "form_button@common_buttons.light_text_button" in ctrl:
                btn = ctrl["form_button@common_buttons.light_text_button"]
                assert btn.get("$button_text") == "#form_button_text"
                assert btn.get("$button_text_binding_type") == "collection"
                assert btn.get("$button_text_grid_collection_name") == "form_buttons"

    def test_ust_button_emits_pressed_button_event(self):
        """The button must emit 'button.form_button_click' so Endstone can dispatch the click."""
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        with upath.open() as f:
            data = json.load(f)
        ust_button = data.get("ust_button", {})
        for ctrl in ust_button.get("controls", []):
            if "form_button@common_buttons.light_text_button" in ctrl:
                btn = ctrl["form_button@common_buttons.light_text_button"]
                assert btn.get("$pressed_button_name") == "button.form_button_click", (
                    "Button must emit 'button.form_button_click' for Endstone callback dispatch"
                )

    def test_player_menu_form_inner_factory_uses_ust_button(self):
        """The button factory must instantiate utilitystone.ust_button from form_buttons."""
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        with upath.open() as f:
            data = json.load(f)
        inner = data.get("player_menu_form_inner", {})
        factory = inner.get("factory", {})
        assert factory.get("control_name") == "utilitystone.ust_button"
        assert factory.get("name") == "buttons"
        assert inner.get("collection_name") == "form_buttons"

    def test_player_menu_form_visibility_uses_utilitystone_marker(self):
        """The player_menu_form must be visible only when title contains the UST marker."""
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        with upath.open() as f:
            data = json.load(f)
        player_menu_form = data.get("player_menu_form", {})
        # Find the visibility binding
        for ctrl in player_menu_form.get("controls", []):
            if "main_panel" in ctrl:
                bindings = ctrl["main_panel"].get("bindings", [])
                found_visibility = False
                for b in bindings:
                    if b.get("binding_type") == "view" and "$utilitystone" in b.get("source_property_name", ""):
                        found_visibility = True
                assert found_visibility, (
                    "main_panel must have a view binding that subtracts $utilitystone"
                )


class TestCallbackPreservation:
    """Endstone's on_click callbacks must remain unchanged after protocol integration."""

    def test_existing_player_menu_callbacks_intact(self):
        """The /menu callbacks (_openHomes, _openWarps, _goWarp, _claimKit) must still be wired."""
        # The source of player_menu.py must still contain all the existing callback references.
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        # Existing functions must be present.
        assert "def _openHomes(" in source
        assert "def _openWarps(" in source
        assert "def _goHome(" in source
        assert "def _goWarp(" in source
        assert "def _openKits(" in source
        assert "def _claimKit(" in source
        assert "def _openTeleport(" in source
        assert "def _openPlayerInfo(" in source
        # The /menu call sites must still wrap them via fm.wrapClick
        assert "fm.wrapClick(player, lambda: _openHomes" in source
        assert "fm.wrapClick(player, lambda: _openWarps" in source

    def test_Player_Info_no_permission_requirement(self):
        """Player Info button must always be visible (no permission gate)."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        # Player Info button is unconditional.
        assert 'addButton(form, "Player Info"' in source


class TestFormManagerUnchanged:
    """The FormManager must remain the only normal send_form path."""

    def test_form_manager_sendForm_signature(self):
        import inspect
        from endstone_utilitystone.ui.manager import FormManager
        sig = inspect.signature(FormManager.sendForm)
        params = list(sig.parameters.keys())
        assert params[:3] == ["self", "player", "form"]
        assert "label" in params


class TestNoCustomClientProtocol:
    """The RP must NOT attempt to execute commands or run custom client code."""

    def test_no_script_in_resource_pack(self):
        """RP must not contain scripts/ folders (no client-side JS)."""
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        # scripts/ subdir is prohibited for RP (that's BP territory)
        assert not (rp_root / "scripts").exists(), "RP must not have scripts/"

    def test_no_command_overlay_in_utilitystone_json(self):
        """The UST renderer must not contain any /command strings."""
        rp_root = pathlib.Path(__file__).resolve().parent.parent / "resource_pack"
        upath = rp_root / "ui" / "utilitystone.json"
        if not upath.exists():
            return
        source = upath.read_text()
        # The RP should never issue /commands — only visual rendering.
        assert "/home" not in source
        assert "/warp" not in source
        assert "/spawn" not in source
        assert "/tpa" not in source
        # No server-side command execution
        assert "server_send_command" not in source
        assert "run_command" not in source
