"""
Phase 5: Production Renderer Obsidian Visual Treatment Tests.

These tests prove the production UtilityStone resource pack's
``utilitystone.json`` now renders every UST_MARKER ActionForm with the
Obsidian Essentials visual treatment.

Coverage:

  1. UST_MARKER routing remains intact.
  2. Production utilitystone.json IS the renderer.
  3. form_buttons collection is preserved.
  4. button.form_button_click remains the click event.
  5. default / hover / pressed textures all exist.
  6. close textures exist.
  7. Icon texture references resolve.
  8. NO property_bag mechanism.
  9. NO title-text slicing mechanism.
 10. Arbitrary button labels / counts remain supported.

Also covers general "no magenta" texture-path validation.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


RP_ROOT = Path(__file__).resolve().parent.parent / "resource_pack"
UI_DIR = RP_ROOT / "ui"
TEX_UI = RP_ROOT / "textures" / "ui"


_TEXTURE_REF_RE = re.compile(r'"texture"\s*:\s*"([^"]+)"')


def _read_json(name: str) -> dict:
    return json.loads((UI_DIR / name).read_text(encoding="utf-8"))


def _all_texture_refs() -> list[str]:
    """Every literal ``texture: "..."`` path in utilitystone.json."""
    text = (UI_DIR / "utilitystone.json").read_text(encoding="utf-8")
    raw = _TEXTURE_REF_RE.findall(text)
    return [t for t in raw if t.startswith("textures/")]


def _resolve(path: str) -> Path:
    """Resolve a literal texture path to a real PNG inside the pack."""
    p = RP_ROOT / path
    if p.exists():
        return p
    return RP_ROOT / f"{path}.png"


# ---------------------------------------------------------------------------
# 1. UST_MARKER routing remains intact.
# ---------------------------------------------------------------------------
class USTMarkerRouting(unittest.TestCase):
    def test_global_variable_contains_utilitystone_marker(self):
        gv = _read_json("_global_variables.json")
        self.assertEqual(gv["$utilitystone"], "\u00a7\u2756\u00a7U\u00a7S\u00a7T\u00a7D")

    def test_server_form_routes_utilitystone_marker(self):
        sf = _read_json("server_form.json")
        # The utilitystone factory entry exists in main_screen_content.
        modifications = sf["main_screen_content"]["modifications"][0]["value"]
        has_utilitystone_factory = False
        for entry in modifications:
            for key in entry:
                if "utilitystone" in key:
                    has_utilitystone_factory = True
                    break
        self.assertTrue(has_utilitystone_factory)

    def test_player_menu_form_visibility_binding_uses_utilitystone(self):
        ust = _read_json("utilitystone.json")
        bindings = ust["player_menu_form"]["controls"][1]["main_panel"]["bindings"]
        visibility_bindings = [b for b in bindings if b.get("target_property_name") == "#visible"]
        self.assertEqual(len(visibility_bindings), 1)
        self.assertIn("$utilitystone", visibility_bindings[0]["source_property_name"])

    def test_long_form_fallback_excludes_utilitystone(self):
        # server_form.json's long_form fallback uses a visibility binding that
        # does NOT exclude $utilitystone; in fact the binding does not list
        # $utilitystone among the admin/community markers it hides.
        # That means $utilitystone forms bypass long_form (the vanilla
        # default) and are routed to the utilitystone factory.
        sf = _read_json("server_form.json")
        long_form = sf["long_form@common_dialogs.main_panel_no_buttons"]
        visibility_binding = long_form["bindings"][1]["source_property_name"]
        # The long_form should not include $utilitystone in its exclude
        # list (it currently doesn't, which is why utilitystone panels work).
        self.assertNotIn("$utilitystone", visibility_binding)


# ---------------------------------------------------------------------------
# 2. Production utilitystone.json IS the renderer.
# ---------------------------------------------------------------------------
class ProductionUtilitystoneIsRenderer(unittest.TestCase):
    def test_utilitystone_json_exists(self):
        self.assertTrue((UI_DIR / "utilitystone.json").exists())

    def test_namespace_is_utilitystone(self):
        ust = _read_json("utilitystone.json")
        self.assertEqual(ust["namespace"], "utilitystone")

    def test_player_menu_form_exists(self):
        ust = _read_json("utilitystone.json")
        self.assertIn("player_menu_form", ust)

    def test_player_menu_form_uses_community_bg(self):
        ust = _read_json("utilitystone.json")
        main = ust["player_menu_form"]["controls"][1]["main_panel"]
        bg = main["controls"][0]["background"]
        self.assertEqual(bg["texture"], "textures/ui/community_bg")


# ---------------------------------------------------------------------------
# 3. form_buttons collection is preserved.
# ---------------------------------------------------------------------------
class FormButtonsCollectionPreserved(unittest.TestCase):
    def test_buttons_stack_iterates_form_buttons(self):
        ust = _read_json("utilitystone.json")
        stack = ust["buttons_stack"]
        self.assertEqual(stack["collection_name"], "form_buttons")

    def test_buttons_stack_factory_declares_ust_button(self):
        ust = _read_json("utilitystone.json")
        stack = ust["buttons_stack"]
        self.assertEqual(stack["factory"]["name"], "buttons")
        self.assertEqual(stack["factory"]["control_name"], "utilitystone.ust_button")

    def test_button_text_bound_to_collection(self):
        ust = _read_json("utilitystone.json")
        ust_button = ust["ust_button"]
        # Find the b_text label
        def _find_b_text(node):
            if isinstance(node, dict):
                if "b_text" in node and isinstance(node["b_text"], dict):
                    return node["b_text"]
                for v in node.values():
                    found = _find_b_text(v)
                    if found:
                        return found
            elif isinstance(node, list):
                for v in node:
                    found = _find_b_text(v)
                    if found:
                        return found
            return None

        bt = _find_b_text(ust_button)
        self.assertIsNotNone(bt)
        self.assertEqual(bt["text"], "#form_button_text")
        bindings = bt["bindings"]
        has_collection_binding = any(
            b.get("binding_name") == "#form_button_text"
            and b.get("binding_type") == "collection"
            and b.get("binding_collection_name") == "form_buttons"
            for b in bindings
        )
        self.assertTrue(has_collection_binding)


# ---------------------------------------------------------------------------
# 4. button.form_button_click remains the click event.
# ---------------------------------------------------------------------------
class ClickEventPreserved(unittest.TestCase):
    def test_pressed_button_name_is_form_button_click(self):
        ust = _read_json("utilitystone.json")
        ust_button = ust["ust_button"]
        # Find any control with $pressed_button_name=button.form_button_click
        def _walk(node):
            if isinstance(node, dict):
                if node.get("$pressed_button_name") == "button.form_button_click":
                    yield node
                for v in node.values():
                    yield from _walk(v)
            elif isinstance(node, list):
                for v in node:
                    yield from _walk(v)

        found = list(_walk(ust_button))
        self.assertGreater(len(found), 0, "no control emits button.form_button_click")


# ---------------------------------------------------------------------------
# 5. default / hover / pressed textures all exist.
# ---------------------------------------------------------------------------
class ButtonStateTexturesExist(unittest.TestCase):
    def setUp(self):
        try:
            from PIL import Image
            self.Image = Image
        except ImportError:
            self.Image = None

    def _assert_png(self, path: Path):
        self.assertTrue(path.exists(), f"missing {path.name}")
        self.assertTrue(str(path).endswith(".png"))
        if self.Image is not None:
            with self.Image.open(path) as img:
                self.assertGreater(img.size[0], 0)
                self.assertGreater(img.size[1], 0)

    def test_default_c_button_png_and_metadata(self):
        self._assert_png(TEX_UI / "default_c_button.png")
        self.assertTrue((TEX_UI / "default_c_button.json").exists())

    def test_hover_c_button_png_and_metadata(self):
        self._assert_png(TEX_UI / "hover_c_button.png")
        self.assertTrue((TEX_UI / "hover_c_button.json").exists())

    def test_pressed_c_button_png_and_metadata(self):
        self._assert_png(TEX_UI / "pressed_c_button.png")
        self.assertTrue((TEX_UI / "pressed_c_button.json").exists())

    def test_button_state_images_referenced_in_renderer(self):
        ust_text = (UI_DIR / "utilitystone.json").read_text()
        for tex in (
            "default_c_button",
            "hover_c_button",
            "pressed_c_button",
        ):
            self.assertIn(
                f"textures/ui/{tex}",
                ust_text,
                f"renderer must reference textures/ui/{tex}",
            )


# ---------------------------------------------------------------------------
# 6. close textures exist.
# ---------------------------------------------------------------------------
class CloseButtonTexturesExist(unittest.TestCase):
    def setUp(self):
        try:
            from PIL import Image
            self.Image = Image
        except ImportError:
            self.Image = None

    def test_close_button_default(self):
        p = TEX_UI / "credits_close_d.png"
        self.assertTrue(p.exists())
        if self.Image is not None:
            with self.Image.open(p) as img:
                self.assertGreater(img.size[0], 0)

    def test_close_button_hover(self):
        p = TEX_UI / "credits_close_h.png"
        self.assertTrue(p.exists())
        if self.Image is not None:
            with self.Image.open(p) as img:
                self.assertGreater(img.size[0], 0)

    def test_close_button_pressed(self):
        p = TEX_UI / "credits_close_p.png"
        self.assertTrue(p.exists())
        if self.Image is not None:
            with self.Image.open(p) as img:
                self.assertGreater(img.size[0], 0)

    def test_close_button_emits_menu_exit(self):
        """The close button must send `button.menu_exit` to dismiss the form."""
        ust = _read_json("utilitystone.json")
        main = ust["player_menu_form"]["controls"][1]["main_panel"]
        close_button = None
        for ctrl in main["controls"]:
            for key, val in ctrl.items():
                if key == "close_button":
                    close_button = val
                    break
            if close_button is not None:
                break
        self.assertIsNotNone(close_button, "main_panel must contain a close_button")
        self.assertEqual(close_button["$pressed_button_name"], "button.menu_exit")

    def test_close_button_has_three_state_images(self):
        ust = _read_json("utilitystone.json")
        main = ust["player_menu_form"]["controls"][1]["main_panel"]
        close_button = None
        for ctrl in main["controls"]:
            for key, val in ctrl.items():
                if key == "close_button":
                    close_button = val
                    break
            if close_button is not None:
                break
        names = set()
        for child in close_button["controls"]:
            for name in child:
                names.add(name)
        self.assertEqual(names, {"default", "hover", "pressed"})


# ---------------------------------------------------------------------------
# 7. Icon texture references resolve.
# ---------------------------------------------------------------------------
class IconTexturesResolve(unittest.TestCase):
    def test_icon_panel_supports_form_button_texture(self):
        ust = _read_json("utilitystone.json")
        # The icon lives in `ust_button_content`, embedded in each state image.
        content = ust["ust_button_content"]
        icon_panel = None
        for ctrl in content["controls"]:
            for key, val in ctrl.items():
                if key == "icon_panel":
                    icon_panel = val
                    break
            if icon_panel:
                break
        self.assertIsNotNone(icon_panel, "ust_button_content must have icon_panel")
        # Find the icon_image
        icon_image = None
        for child in icon_panel["controls"]:
            for key, val in child.items():
                if key == "icon_image":
                    icon_image = val
                    break
            if icon_image:
                break
        self.assertIsNotNone(icon_image, "icon_panel must contain icon_image")
        # icon_image must bind #form_button_texture from form_buttons
        bindings = icon_image["bindings"]
        self.assertTrue(any(
            b.get("binding_name") == "#form_button_texture"
            and b.get("binding_type") == "collection"
            and b.get("binding_collection_name") == "form_buttons"
            for b in bindings
        ))

    def test_icon_hides_when_no_icon_set(self):
        """The icon_image has a view binding: visible only when #texture is non-empty.

        Following the working Obsidian Essentials pattern, the view binding is
        on both the icon_panel (which hides when #texture is empty) and the
        icon_image itself (which hides when #texture is empty/loading).
        """
        ust = _read_json("utilitystone.json")
        content = ust["ust_button_content"]
        icon_panel = None
        for ctrl in content["controls"]:
            for key, val in ctrl.items():
                if key == "icon_panel":
                    icon_panel = val
                    break
            if icon_panel:
                break
        self.assertIsNotNone(icon_panel)
        # The icon_image has a view binding on itself.
        icon_image = icon_panel["controls"][0]["icon_image"]
        bindings = icon_image.get("bindings", [])
        view_bindings = [b for b in bindings if b.get("binding_type") == "view"]
        self.assertEqual(
            len(view_bindings), 1,
            "icon_image must have exactly one view binding",
        )
        self.assertEqual(view_bindings[0]["target_property_name"], "#visible")
        self.assertIn("#texture", view_bindings[0]["source_property_name"])
        # It must check the empty / loading case to hide the icon.
        self.assertTrue(
            "''" in view_bindings[0]["source_property_name"] or
            "loading" in view_bindings[0]["source_property_name"],
            f"view binding must reference empty/loading; got {view_bindings[0]['source_property_name']!r}",
        )


# ---------------------------------------------------------------------------
# 8. NO property_bag mechanism.
# ---------------------------------------------------------------------------
class NoPropertyBag(unittest.TestCase):
    """Phase5 brief explicitly forbids property_bag."""

    def test_utilitystone_json_no_property_bag(self):
        text = (UI_DIR / "utilitystone.json").read_text()
        self.assertNotIn("property_bag", text)

    def test_utilitystone_json_no_property_bag_anywhere(self):
        # Walk every control recursively
        data = _read_json("utilitystone.json")
        def _walk(node):
            if isinstance(node, dict):
                self.assertNotIn(
                    "property_bag", node,
                    f"property_bag found in control: {list(node.keys())[:3]}",
                )
                for v in node.values():
                    _walk(v)
            elif isinstance(node, list):
                for v in node:
                    _walk(v)
        _walk(data)


# ---------------------------------------------------------------------------
# 9. NO title-text slicing mechanism.
# ---------------------------------------------------------------------------
class NoTitleSlicing(unittest.TestCase):
    def test_no_percent_8s(self):
        text = (UI_DIR / "utilitystone.json").read_text()
        self.assertNotIn("%.8s", text)

    def test_no_title_to_texture_concatenation(self):
        """No source_property_name that derives a texture path from #title_text.

        The visibility bindings legitimately reference #title_text (that's
        how they detect the marker). This test only flags the forbidden
        pattern where a binding derives a texture path from #title_text.
        """
        data = _read_json("utilitystone.json")
        def _walk(node):
            if isinstance(node, dict):
                target = node.get("target_property_name", "")
                source = node.get("source_property_name", "")
                # If a binding targets a texture-related property, it must
                # NOT derive the texture path from #title_text.
                if target in ("#texture", "#texture_file_system"):
                    self.assertNotIn(
                        "#title_text", source,
                        f"texture must not derive from #title_text: target={target} source={source}",
                    )
                for v in node.values():
                    _walk(v)
            elif isinstance(node, list):
                for v in node:
                    _walk(v)
        _walk(data)


# ---------------------------------------------------------------------------
# 10. Arbitrary button labels / counts remain supported.
# ---------------------------------------------------------------------------
class ArbitraryButtonsSupported(unittest.TestCase):
    def test_button_text_uses_form_button_text_binding(self):
        """The renderer must not assume specific button text — it must
        bind to #form_button_text generically."""
        ust = _read_json("utilitystone.json")
        ust_button = ust["ust_button"]
        # Find the b_text label inside form_button
        def _find_b_text(node):
            if isinstance(node, dict):
                if "b_text" in node and isinstance(node["b_text"], dict):
                    return node["b_text"]
                for v in node.values():
                    found = _find_b_text(v)
                    if found:
                        return found
            elif isinstance(node, list):
                for v in node:
                    found = _find_b_text(v)
                    if found:
                        return found
            return None
        bt = _find_b_text(ust_button)
        self.assertIsNotNone(bt)
        self.assertEqual(bt["text"], "#form_button_text")

    def test_button_factory_does_not_hardcode_count(self):
        """The factory must drive button creation from #form_button_contents / collection length."""
        ust = _read_json("utilitystone.json")
        stack = ust["buttons_stack"]
        bindings = stack["bindings"]
        self.assertTrue(any(
            b.get("binding_name") == "#form_button_contents"
            and b.get("binding_name_override") == "#collection_length"
            for b in bindings
        ))


# ---------------------------------------------------------------------------
# Texture references all resolve (no magenta-producing missing paths).
# ---------------------------------------------------------------------------
class AllTextureReferencesResolve(unittest.TestCase):
    def test_every_texture_path_in_utilitystone_json_resolves(self):
        for ref in _all_texture_refs():
            with self.subTest(texture=ref):
                target = _resolve(ref)
                self.assertTrue(
                    target.exists(),
                    f"texture {ref} referenced in utilitystone.json "
                    f"is missing in the resource pack ({target})",
                )
                self.assertTrue(str(target).endswith(".png"))

    def test_no_texture_path_includes_property_bag_or_first8bytes(self):
        """No texture reference should rely on dynamic title-text computation."""
        for ref in _all_texture_refs():
            self.assertFalse(
                ref.startswith("textures/ui/default_'"),
                f"forbidden dynamic-texture reference: {ref}",
            )
            self.assertNotIn(
                "#title_text", ref,
                f"texture must not depend on #title_text: {ref}",
            )


# ---------------------------------------------------------------------------
# Body interior texture exists and is referenced.
# ---------------------------------------------------------------------------
class BodyInteriorTexture(unittest.TestCase):
    def test_c_body_background_exists(self):
        self.assertTrue((TEX_UI / "c_body_background.png").exists())
        self.assertTrue((TEX_UI / "c_body_background.json").exists())

    def test_renderer_uses_body_background(self):
        ust_text = (UI_DIR / "utilitystone.json").read_text()
        self.assertIn("textures/ui/c_body_background", ust_text)


# ---------------------------------------------------------------------------
# Community background texture and nineslice metadata.
# ---------------------------------------------------------------------------
class CommunityBackground(unittest.TestCase):
    def test_community_bg_png_exists(self):
        self.assertTrue((TEX_UI / "community_bg.png").exists())

    def test_community_bg_nineslice_metadata(self):
        meta = json.loads((TEX_UI / "community_bg.json").read_text())
        # Must have at least nineslice_size to scale properly.
        self.assertIn("nineslice_size", meta)


# ---------------------------------------------------------------------------
# Black fallback texture (Bedrock has it built-in but we ship a local copy).
# ---------------------------------------------------------------------------
class BlackFallback(unittest.TestCase):
    def test_black_png_present(self):
        self.assertTrue((TEX_UI / "Black.png").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)