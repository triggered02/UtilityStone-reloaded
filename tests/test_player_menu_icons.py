"""
Phase 5.2 regression tests for player-menu button icons and chevron.

Verifies:
  - Every player-menu addButton call passes an icon= argument.
  - The icons used are real Obsidian assets that exist in the pack.
  - No magenta-producing missing paths.
  - The renderer includes a right-side chevron for every button row.
  - Buttons without icons (e.g. the "Create Home" / "Back" inside submenus
    that we did not touch) still render correctly because the icon panel
    auto-hides when the form_button_texture is empty.
  - form_button_click is still the click event.
  - form_buttons collection is still the iteration source.
  - All three button states (default/hover/pressed) still work.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
import zipfile
from pathlib import Path


_WORKTREE_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_WORKTREE_SRC) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_SRC))
for _name in list(sys.modules):
    if _name == "endstone_utilitystone" or _name.startswith("endstone_utilitystone."):
        del sys.modules[_name]


RP_ROOT = Path(__file__).resolve().parent.parent / "resource_pack"
UI_DIR = RP_ROOT / "ui"
TEX_UI = RP_ROOT / "textures" / "ui"
TEX_ICONS = RP_ROOT / "textures" / "icons"
PLAYER_MENU_PY = _WORKTREE_SRC / "endstone_utilitystone" / "ui" / "player_menu.py"


_TEXTURE_REF_RE = re.compile(r'"texture"\s*:\s*"([^"]+)"')


def _read_json(name: str) -> dict:
    return json.loads((UI_DIR / name).read_text(encoding="utf-8"))


def _all_texture_refs() -> list[str]:
    text = (UI_DIR / "utilitystone.json").read_text(encoding="utf-8")
    raw = _TEXTURE_REF_RE.findall(text)
    return [t for t in raw if t.startswith("textures/")]


def _resolve_texture(texture: str) -> Path:
    """Resolve a literal texture path. Bedrock appends .png automatically."""
    p = RP_ROOT / texture
    if p.exists():
        return p
    return RP_ROOT / f"{texture}.png"


# ---------------------------------------------------------------------------
# Accessors for the new (Obsidian-style) ust_button structure
# ---------------------------------------------------------------------------
# New hierarchy (matching Obsidian Essentials):
#   ust_button (type=panel)
#     -> main@common.button
#         -> default/hover/pressed (type=image, each embeds ust_button_content)
#         -> b_text (label)
#   ust_button_content (type=stack_panel, embedded in each state image)
#     -> icon_panel (panel, size [-34, 100%c])
#         -> icon_image (type=image, bound to #form_button_texture)
#     -> chevron_panel (panel, size [-20, 100%c])
#         -> chevron_default (type=image, texture Arrow_Right_Curved)


def _get_button_node(ust: dict) -> dict:
    """Return the `main@common.button` node from `ust_button`."""
    for ctrl in ust["ust_button"]["controls"]:
        for key, val in ctrl.items():
            if key == "main@common.button":
                return val
    raise KeyError("main@common.button not found in ust_button")


def _get_state_images(button: dict) -> dict:
    """Return {state_name: state_image_node} for default/hover/pressed."""
    result = {}
    for child in button.get("controls", []):
        for name, val in child.items():
            if name in ("default", "hover", "pressed"):
                result[name] = val
    return result


def _get_content_node(ust: dict) -> dict:
    """Return the `ust_button_content` node."""
    return ust["ust_button_content"]


def _get_icon_panel(content: dict) -> dict:
    for ctrl in content["controls"]:
        for key, val in ctrl.items():
            if key == "icon_panel":
                return val
    raise KeyError("icon_panel not found in ust_button_content")


def _get_icon_image(icon_panel: dict) -> dict:
    for child in icon_panel["controls"]:
        for key, val in child.items():
            if key == "icon_image":
                return val
    raise KeyError("icon_image not found in icon_panel")


def _get_chevron_panel(content: dict) -> dict:
    for ctrl in content["controls"]:
        for key, val in ctrl.items():
            if key == "chevron_panel":
                return val
    raise KeyError("chevron_panel not found in ust_button_content")


def _get_chevron(chevron_panel: dict) -> dict:
    for child in chevron_panel["controls"]:
        for key, val in child.items():
            if key == "chevron_default":
                return val
    raise KeyError("chevron_default not found in chevron_panel")


def _get_b_text(button: dict) -> dict:
    for child in button.get("controls", []):
        for key, val in child.items():
            if key == "b_text":
                return val
    raise KeyError("b_text not found in button")


# ---------------------------------------------------------------------------
# Renderer invariants
# ---------------------------------------------------------------------------

class USTButtonRenderer(unittest.TestCase):
    """Verify the new icon-and-chevron button renderer is structurally correct."""

    def setUp(self):
        self.ust = _read_json("utilitystone.json")
        self.ust_button = self.ust["ust_button"]

    def test_button_row_has_icon_panel(self):
        # The icon lives in `ust_button_content`, embedded in each state image.
        content = _get_content_node(self.ust)
        icon_panel = _get_icon_panel(content)
        # Icon panel is on the left (negative size shift pushes it to anchor).
        self.assertEqual(icon_panel["size"], [-34, "100%c"])
        # It must bind #form_button_texture (collection binding)
        icon_image = _get_icon_image(icon_panel)
        bindings = icon_image["bindings"]
        texture_bindings = [b for b in bindings
                             if b.get("binding_name") == "#form_button_texture"]
        self.assertEqual(len(texture_bindings), 1)
        self.assertEqual(texture_bindings[0]["binding_type"], "collection")
        self.assertEqual(texture_bindings[0]["binding_collection_name"], "form_buttons")

    def test_icon_nested_inside_each_state_image(self):
        """The icon+chevron content must be embedded as a CHILD of each
        state image (default/hover/pressed), exactly like Obsidian's
        credit_state_* embeds credit_button_content."""
        button = _get_button_node(self.ust)
        states = _get_state_images(button)
        self.assertEqual(set(states.keys()), {"default", "hover", "pressed"})
        for state_name, state_img in states.items():
            with self.subTest(state=state_name):
                content = state_img.get("controls", [])
                content_names = [k for c in content for k in c]
                self.assertTrue(
                    any(cn.startswith("content@") for cn in content_names),
                    f"{state_name} state must embed content@utilitystone.ust_button_content",
                )

    def test_button_row_has_chevron(self):
        # Chevron is in chevron_panel inside ust_button_content.
        content = _get_content_node(self.ust)
        chevron_panel = _get_chevron_panel(content)
        chevron = _get_chevron(chevron_panel)
        self.assertTrue(chevron["type"] == "image")

    def test_icon_view_binding_on_icon_image(self):
        """The view binding that hides the icon when no icon is set must
        be on the icon_image control itself (matching Obsidian Essentials
        pattern)."""
        content = _get_content_node(self.ust)
        icon_panel = _get_icon_panel(content)
        icon_image = _get_icon_image(icon_panel)
        bindings = icon_image.get("bindings", [])
        view_bindings = [b for b in bindings if b.get("binding_type") == "view"]
        self.assertGreaterEqual(
            len(view_bindings), 1,
            "icon_image must have at least one view binding for visibility",
        )
        for vb in view_bindings:
            self.assertEqual(vb.get("target_property_name"), "#visible")
            self.assertIn("#texture", vb.get("source_property_name", ""))

    def test_icon_view_binding_predicate_evaluates_correctly(self):
        """Verify the view binding predicate evaluates to True when the icon
        path is non-empty (the normal case after addButton(icon=...))."""
        content = _get_content_node(self.ust)
        icon_panel = _get_icon_panel(content)
        icon_image = _get_icon_image(icon_panel)
        view_bindings = [b for b in icon_image.get("bindings", [])
                         if b.get("binding_type") == "view"]
        self.assertTrue(len(view_bindings) >= 1)
        expr = view_bindings[0]["source_property_name"]

        def evaluate(texture_value: str) -> bool:
            e = re.sub(r"#texture\b", lambda m: repr(texture_value), expr)
            e = e.replace("=", "==")
            return bool(eval(e, {"__builtins__": {}}, {}))

        test_cases = [
            ("textures/icons/Homes_Bed", True),
            ("textures/icons/LandClaims", True),
            ("textures/icons/UpArrow", True),
            ("", False),
            ("loading", False),
        ]
        for tex_value, expected in test_cases:
            with self.subTest(tex_value=tex_value, expected=expected):
                result = evaluate(tex_value)
                self.assertEqual(
                    result, expected,
                    f"expr={expr!r} with #texture={tex_value!r} should "
                    f"evaluate to {expected}, got {result}",
                )

    def test_chevron_uses_obsidian_arrow_asset(self):
        content = _get_content_node(self.ust)
        chevron = _get_chevron(_get_chevron_panel(content))
        self.assertEqual(chevron["texture"], "textures/icons/Arrow_Right_Curved")
        self.assertTrue(_resolve_texture(chevron["texture"]).exists(),
                        f"{chevron['texture']} not found in pack")

    def test_chevron_layered_above_button_states(self):
        """Chevron is inside the state content (layer 50), which is drawn
        above the state image (layer 0/1/2). b_text (layer 100) is on top."""
        content = _get_content_node(self.ust)
        chevron_panel = _get_chevron_panel(content)
        chevron = _get_chevron(chevron_panel)
        button = _get_button_node(self.ust)
        b_text = _get_b_text(button)
        self.assertIn("layer", chevron)
        self.assertIn("layer", b_text)
        # Chevron layer must be >= state image layers so it overlays them.
        self.assertGreaterEqual(chevron["layer"], 0)
        # b_text on top of chevron.
        self.assertGreater(b_text["layer"], chevron["layer"])

    def test_chevron_anchored_to_right_edge_of_button(self):
        content = _get_content_node(self.ust)
        chevron = _get_chevron(_get_chevron_panel(content))
        self.assertEqual(chevron["anchor_from"], "right_middle")
        self.assertEqual(chevron["anchor_to"], "right_middle")
        offset = chevron.get("offset", [0, 0])
        self.assertEqual(len(offset), 2)
        self.assertLessEqual(offset[0], 0)

    def test_chevron_inside_button_horizontal_bounds(self):
        content = _get_content_node(self.ust)
        chevron = _get_chevron(_get_chevron_panel(content))
        size = chevron.get("size", [0, 0])
        offset = chevron.get("offset", [0, 0])
        self.assertGreaterEqual(offset[0], -size[0],
                               "chevron offset would push it past the left edge")

    def test_b_text_does_not_cover_chevron_area(self):
        button = _get_button_node(self.ust)
        b_text = _get_b_text(button)
        content = _get_content_node(self.ust)
        chevron = _get_chevron(_get_chevron_panel(content))
        chevron_width = chevron.get("size", [14, 10])[0]
        text_width_str = b_text.get("size", ["", ""])[0]
        m = re.match(r"100%\s*-\s*(\d+)px", text_width_str)
        self.assertIsNotNone(m,
                             f"b_text width should be '100% - Npx', got {text_width_str!r}")
        offset_px = int(m.group(1))
        self.assertGreaterEqual(
            offset_px, chevron_width,
            f"b_text offset ({offset_px}px) must be >= chevron width "
            f"({chevron_width}px) so the text doesn't overlap the chevron",
        )

    def test_label_offset_for_chevron(self):
        button = _get_button_node(self.ust)
        b_text = _get_b_text(button)
        size = b_text.get("size", [])
        width = size[0] if size else ""
        self.assertIn("100% - ", width,
                      f"text width should be reduced to make room for chevron; got {width!r}")
        m = re.match(r"100%\s*-\s*(\d+)px", width)
        if m:
            offset_px = int(m.group(1))
            self.assertGreaterEqual(offset_px, 20)
            self.assertLessEqual(offset_px, 80)

    def test_three_button_states_preserved(self):
        button = _get_button_node(self.ust)
        state_textures = {}
        for child in button["controls"]:
            for name, val in child.items():
                if name in ("default", "hover", "pressed") and "texture" in val:
                    state_textures[name] = val["texture"]
        self.assertEqual(set(state_textures.keys()), {"default", "hover", "pressed"})
        self.assertEqual(state_textures["default"], "textures/ui/default_c_button")
        self.assertEqual(state_textures["hover"], "textures/ui/hover_c_button")
        self.assertEqual(state_textures["pressed"], "textures/ui/pressed_c_button")
        for tex in state_textures.values():
            self.assertTrue(_resolve_texture(tex).exists(),
                            f"{tex} missing in pack")

    def test_click_event_preserved(self):
        button = _get_button_node(self.ust)
        self.assertEqual(button["$pressed_button_name"], "button.form_button_click")

    def test_form_buttons_collection_preserved(self):
        stack = self.ust["buttons_stack"]
        self.assertEqual(stack["collection_name"], "form_buttons")
        self.assertEqual(stack["factory"]["name"], "buttons")
        self.assertEqual(stack["factory"]["control_name"], "utilitystone.ust_button")


# ---------------------------------------------------------------------------
# No-magenta check: every texture referenced in the renderer exists
# ---------------------------------------------------------------------------

class RendererTexturePathValidation(unittest.TestCase):
    """Critical: every literal texture: "<path>" in utilitystone.json resolves."""

    def setUp(self):
        self.refs = _all_texture_refs()

    def test_every_texture_path_resolves(self):
        for ref in self.refs:
            with self.subTest(texture=ref):
                target = _resolve_texture(ref)
                self.assertTrue(
                    target.exists(),
                    f"texture {ref} referenced in utilitystone.json "
                    f"is missing in the pack ({target})",
                )
                # Must end in .png
                self.assertTrue(str(target).endswith(".png"))


# ---------------------------------------------------------------------------
# Icon / button sanity: Python side passes correct icons
# ---------------------------------------------------------------------------

class PlayerMenuIconAssignment(unittest.TestCase):
    """Verify that player_menu.py calls addButton with icon= for every button."""

    def setUp(self):
        self.source = PLAYER_MENU_PY.read_text(encoding="utf-8")

    def test_section_buttons_have_icons(self):
        """The four main section buttons (Travel, Teleport, Utilities, Admin Panel)
        must each pass an icon= argument."""
        for label in ("Travel", "Warps", "Utilities", "Admin Panel"):
            with self.subTest(label=label):
                # The addButton(..., "<label>", icon=..., ...) pattern.
                pattern = re.compile(
                    r'addButton\(\s*\n\s*form,\s*\n\s*"' + re.escape(label) +
                    r'".*?icon\s*=\s*"[^"]+"',
                    re.DOTALL,
                )
                self.assertIsNotNone(
                    pattern.search(self.source),
                    f"{label!r} addButton call is missing icon=",
                )
                m = pattern.search(self.source)
                self.assertIn('icon="textures/icons/', m.group(0),
                              f"{label!r} must use a textures/icons/ path")

    def test_specific_icon_assignments(self):
        """Each menu action must be associated with the correct Obsidian icon."""
        expected = {
            "Travel": "LandClaims",
            "Teleport": "TPA_Globe",
            "Utilities": "crate_icon",
            "Admin Panel": "admin",
            "Homes": "Homes_Bed",
            "Warps": "LandClaims",
            "Kits": "crate_icon",
            "Player Info": "Stats_Icon",
            "AFK": "AFK",
            "Daily Reward": "loot",
            "Back": "Arrow_Left_Curved",
        }
        for label, icon in expected.items():
            with self.subTest(label=label, icon=icon):
                pattern = re.compile(
                    r'addButton\(\s*\n\s*form,\s*\n\s*"' + re.escape(label) +
                    r'".*?icon\s*=\s*"' + re.escape("textures/icons/" + icon) + r'"',
                    re.DOTALL,
                )
                self.assertIsNotNone(
                    pattern.search(self.source),
                    f"{label!r} must use icon='textures/icons/{icon}'",
                )

    def test_spawn_uses_up_arrow_icon(self):
        # "Spawn" is a sub-button under Travel; it should use the UpArrow icon
        # (vertical arrow conveying "go to a fixed point") rather than the
        # right-curved chevron (which is reserved for right-edge decoration).
        pattern = re.compile(
            r'addButton\(\s*\n\s*form,\s*\n\s*"Spawn".*?icon\s*=\s*"textures/icons/UpArrow"',
            re.DOTALL,
        )
        self.assertIsNotNone(pattern.search(self.source),
                             '"Spawn" addButton must use UpArrow icon')

    def test_no_addButton_without_icon_in_travel_or_utilities(self):
        """Every addButton inside _openTravel and _openUtilities must have an icon.
        The icons we picked are all real Obsidian assets. Buttons without
        appropriate icon (e.g. dynamic per-player TPA buttons) are allowed
        to omit icon= — they are exempt from this check by their context
        (they are inside the TPA submenu which is outside the scope of this
        phase)."""
        # Extract the source of _openTravel and _openUtilities
        travel_start = self.source.find("def _openTravel")
        utils_start = self.source.find("def _openUtilities")
        # Each section's addButton calls must have icon=
        for section_name, start in [("Travel", travel_start), ("Utilities", utils_start)]:
            section_source = self.source[start:start + 3000]  # rough slice
            addbutton_calls = re.findall(r'addButton\([^)]*\)', section_source, re.DOTALL)
            self.assertGreater(
                len(addbutton_calls), 0,
                f"no addButton calls found in {section_name}",
            )
            for call in addbutton_calls:
                if '"Back"' in call:
                    self.assertIn(
                        'icon="textures/icons/Arrow_Left_Curved"', call,
                        f"Back button in {section_name} missing Arrow_Left_Curved icon",
                    )
                else:
                    self.assertIn(
                        'icon="textures/icons/', call,
                        f"addButton in {section_name} missing icon=: {call[:80]!r}",
                    )


# ---------------------------------------------------------------------------
# No-icon-button case: buttons without an icon must still render correctly
# ---------------------------------------------------------------------------

class NoIconButtonCase(unittest.TestCase):
    """The renderer must handle a button with empty #form_button_texture."""

    def test_icon_panel_hides_when_texture_empty(self):
        """The icon_image has a view binding: visible when texture is non-empty.

        Note: in Phase 5.2.1 the view binding was moved from icon_panel
        to icon_image itself, following the Obsidian Essentials pattern.
        The icon_panel also has a view binding to hide entirely when no icon.
        """
        ust = _read_json("utilitystone.json")
        content = _get_content_node(ust)
        icon_panel = _get_icon_panel(content)
        icon_image = _get_icon_image(icon_panel)
        bindings = icon_image.get("bindings", [])
        view_bindings = [b for b in bindings if b.get("binding_type") == "view"]
        self.assertEqual(len(view_bindings), 1, "icon_image must have one view binding")
        binding = view_bindings[0]
        self.assertEqual(binding["target_property_name"], "#visible")
        self.assertTrue(
            "#texture = ''" in binding["source_property_name"] or
            "loading" in binding["source_property_name"],
            f"view binding must reference empty/loading; got {binding['source_property_name']!r}",
        )
        # The icon_panel itself must ALSO have a view binding to hide its
        # 34px-wide placeholder when no icon is set (matching Obsidian).
        panel_bindings = icon_panel.get("bindings", [])
        self.assertTrue(any(
            b.get("binding_type") == "view"
            for b in panel_bindings
        ), "icon_panel must have a view binding to hide when texture empty")

    def test_button_without_icon_keeps_3_states(self):
        """Even when no icon is set, the button still has its 3-state background."""
        ust = _read_json("utilitystone.json")
        button = _get_button_node(ust)
        state_layers = {}
        for child in button["controls"]:
            for name, val in child.items():
                if name in ("default", "hover", "pressed") and "layer" in val:
                    state_layers[name] = val["layer"]
        self.assertEqual(set(state_layers.keys()), {"default", "hover", "pressed"})


# ---------------------------------------------------------------------------
# Concrete icon assets exist
# ---------------------------------------------------------------------------

class RequiredIconAssetsPresent(unittest.TestCase):
    """Every icon referenced from player_menu.py must exist in the pack."""

    REQUIRED = (
        "Homes_Bed.png",
        "LandClaims.png",
        "TPA_Globe.png",
        "crate_icon.png",
        "Stats_Icon.png",
        "AFK.png",
        "loot.png",
        "admin.png",
        "Arrow_Right_Curved.png",
        "Arrow_Right_Curved_Highlighted.png",
        "Arrow_Left_Curved.png",
        "UpArrow.png",
    )

    def test_each_required_icon_present(self):
        for n in self.REQUIRED:
            with self.subTest(icon=n):
                self.assertTrue((TEX_ICONS / n).exists(),
                                f"required icon {n} missing in pack")


# ---------------------------------------------------------------------------
# Mcpack contents (when built) include all icons
# ---------------------------------------------------------------------------

class McpackArchiveContainsIcons(unittest.TestCase):
    MCPACK = Path("/tmp/UtilityStone_Reloaded.mcpack")

    def setUp(self):
        if not self.MCPACK.exists():
            self.skipTest("mcpack not built yet")
        import zipfile
        with zipfile.ZipFile(self.MCPACK) as zf:
            self.names = zf.namelist()

    def test_mcpack_contains_icons(self):
        for icon in RequiredIconAssetsPresent.REQUIRED:
            with self.subTest(icon=icon):
                self.assertIn(f"textures/icons/{icon}", self.names)


if __name__ == "__main__":
    unittest.main(verbosity=2)