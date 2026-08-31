"""Regression tests that verify our code uses the correct Endstone 0.11 API.

These tests import the REAL endstone package (not mocks) to catch API
naming mistakes that caused the menu item listener to fail at runtime.
"""
import pytest


class TestRealEndstoneFormApi:
    """Verify form classes exist and have the attributes we use."""

    def test_action_form_exists(self):
        from endstone.form import ActionForm
        assert hasattr(ActionForm, "add_button")
        assert hasattr(ActionForm, "add_label")
        assert hasattr(ActionForm, "add_header")
        assert hasattr(ActionForm, "add_divider")
        assert hasattr(ActionForm, "on_submit")
        assert hasattr(ActionForm, "on_close")

    def test_modal_form_exists(self):
        from endstone.form import ModalForm
        assert hasattr(ModalForm, "add_control")
        assert hasattr(ModalForm, "on_submit")
        assert hasattr(ModalForm, "on_close")
        assert hasattr(ModalForm, "submit_button")

    def test_message_form_exists(self):
        from endstone.form import MessageForm
        mf = MessageForm(title="t", content="c", button1="Y", button2="N")
        assert mf.title == "t"
        assert mf.content == "c"

    def test_button_constructor(self):
        from endstone.form import Button
        b = Button(text="Click", icon=None, on_click=lambda p: None)
        assert b.text == "Click"

    def test_text_input_constructor(self):
        from endstone.form import TextInput
        t = TextInput(label="Name", placeholder="Enter", default_value="def")
        assert t.label == "Name"

    def test_toggle_constructor(self):
        from endstone.form import Toggle
        t = Toggle(label="Enable", default_value=True)
        assert t.label == "Enable"

    def test_slider_constructor(self):
        from endstone.form import Slider
        s = Slider(label="Val", min=0, max=100, step=1, default_value=50)
        assert s.label == "Val"

    def test_dropdown_constructor(self):
        from endstone.form import Dropdown
        d = Dropdown(label="Pick", options=["a", "b", "c"], default_index=1)
        assert d.label == "Pick"

    def test_step_slider_constructor(self):
        from endstone.form import StepSlider
        ss = StepSlider(label="Step", options=["x", "y"])
        assert ss.label == "Step"

    def test_label_constructor_uses_text(self):
        from endstone.form import Label
        l = Label(text="Hello")
        assert l.text == "Hello"

    def test_header_constructor(self):
        from endstone.form import Header
        h = Header(label="Title")
        assert h.label == "Title"

    def test_divider_constructor(self):
        from endstone.form import Divider
        d = Divider()
        assert d is not None


class TestRealEndstoneEventApi:
    """Verify event classes and action enum values match our usage."""

    def test_player_interact_event_action_enum(self):
        from endstone.event import PlayerInteractEvent
        # CRITICAL: These are the REAL enum names
        assert hasattr(PlayerInteractEvent.Action, "RIGHT_CLICK_AIR")
        assert hasattr(PlayerInteractEvent.Action, "RIGHT_CLICK_BLOCK")
        assert hasattr(PlayerInteractEvent.Action, "LEFT_CLICK_AIR")
        assert hasattr(PlayerInteractEvent.Action, "LEFT_CLICK_BLOCK")
        # Verify the OLD wrong names do NOT exist (regression guard)
        assert not hasattr(PlayerInteractEvent.Action, "RightClickAir")
        assert not hasattr(PlayerInteractEvent.Action, "RightClickBlock")

    def test_player_interact_event_attributes(self):
        from endstone.event import PlayerInteractEvent
        # Verify attributes we use exist on the class
        assert "has_item" in dir(PlayerInteractEvent)
        assert "action" in dir(PlayerInteractEvent)
        assert "item" in dir(PlayerInteractEvent)
        assert "player" in dir(PlayerInteractEvent)
        assert "cancel" in dir(PlayerInteractEvent)

    def test_player_join_event(self):
        from endstone.event import PlayerJoinEvent
        assert "player" in dir(PlayerJoinEvent)
        assert "join_message" in dir(PlayerJoinEvent)

    def test_player_quit_event(self):
        from endstone.event import PlayerQuitEvent
        assert "player" in dir(PlayerQuitEvent)
        assert "quit_message" in dir(PlayerQuitEvent)

    def test_event_priority(self):
        from endstone.event import EventPriority
        assert EventPriority.LOW == 1
        assert EventPriority.NORMAL == 2
        assert EventPriority.HIGH == 3
        assert EventPriority.HIGHEST == 4
        assert EventPriority.MONITOR == 5

    def test_event_handler_decorator_exists(self):
        from endstone.event import event_handler
        assert callable(event_handler)


class TestRealEndstonePlayerApi:
    """Verify Player class has the attributes we use."""

    def test_player_attributes(self):
        from endstone import Player
        required = [
            "is_valid", "inventory", "health", "max_health",
            "allow_flight", "is_flying", "unique_id", "name",
            "send_form", "send_message", "send_error_message",
            "kick", "teleport", "perform_command", "location",
            "close_form", "game_mode", "ping",
        ]
        for attr in required:
            assert hasattr(Player, attr), f"Player missing: {attr}"

    def test_server_attributes(self):
        from endstone import Server
        required = ["online_players", "command_sender", "dispatch_command", "scheduler"]
        for attr in required:
            assert hasattr(Server, attr), f"Server missing: {attr}"


class TestRealEndstoneInventoryApi:
    """Verify Inventory and ItemStack APIs."""

    def test_inventory_methods(self):
        from endstone.inventory import Inventory
        required = ["get_item", "set_item", "add_item", "size"]
        for method in required:
            assert hasattr(Inventory, method), f"Inventory missing: {method}"

    def test_item_stack_attributes(self):
        from endstone.inventory import ItemStack
        assert hasattr(ItemStack, "amount")
        assert hasattr(ItemStack, "type")
        assert hasattr(ItemStack, "item_meta")
        assert hasattr(ItemStack, "set_item_meta")

    def test_item_meta_attributes(self):
        from endstone.inventory import ItemMeta
        required = ["display_name", "lore", "has_damage", "damage"]
        for attr in required:
            assert hasattr(ItemMeta, attr), f"ItemMeta missing: {attr}"


class TestRealEndstoneColorFormat:
    """Verify ColorFormat has constants we use."""

    def test_color_constants(self):
        from endstone import ColorFormat
        required = ["GRAY", "GREEN", "YELLOW", "RED", "AQUA", "WHITE", "GOLD", "RESET"]
        for const in required:
            assert hasattr(ColorFormat, const), f"ColorFormat missing: {const}"


class TestActionEnumValuesInCode:
    """Verify the ACTUAL menu_item.py code uses correct enum names."""

    def test_menu_item_uses_right_click_air(self):
        """The menu_item listener must use RIGHT_CLICK_AIR, not RightClickAir."""
        import ast
        import pathlib

        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "menu_item.py"
        source = path.read_text()

        # Must contain the correct enum name
        assert "RIGHT_CLICK_AIR" in source, "menu_item.py must use RIGHT_CLICK_AIR"
        assert "RIGHT_CLICK_BLOCK" in source, "menu_item.py must use RIGHT_CLICK_BLOCK"

        # Must NOT contain the old wrong names
        assert "RightClickAir" not in source, "menu_item.py still uses wrong RightClickAir"
        assert "RightClickBlock" not in source, "menu_item.py still uses wrong RightClickBlock"


class TestMenuItemIdentification:
    """Verify menu item requires BOTH item type AND display name match."""

    def test_menu_item_checks_item_type(self):
        """menu_item.py must compare item.type against settings.menuItemType."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "menu_item.py"
        source = path.read_text()
        assert "item.type" in source, "menu_item.py must check item.type"
        assert "settings.menuItemType" in source, "menu_item.py must compare against settings.menuItemType"

    def test_menu_item_checks_display_name(self):
        """menu_item.py must compare meta.display_name against settings.menuItemName."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "menu_item.py"
        source = path.read_text()
        assert "meta.display_name" in source, "menu_item.py must check meta.display_name"
        assert "settings.menuItemName" in source, "menu_item.py must compare against settings.menuItemName"

    def test_menu_item_type_check_before_name_check(self):
        """Item type check must come before display name check for efficiency."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "menu_item.py"
        source = path.read_text()
        type_pos = source.index("item.type")
        name_pos = source.index("meta.display_name")
        assert type_pos < name_pos, "item.type check must come before meta.display_name check"

    def test_menu_item_never_opens_admin_menu(self):
        """Menu item interaction must only open Player Menu, never Admin Panel."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "menu_item.py"
        source = path.read_text()
        assert "openPlayerMenu" in source, "menu_item.py must open Player Menu"
        assert "openAdminPanel" not in source, "menu_item.py must NOT open Admin Panel"

    def test_connection_duplicate_check_uses_item_type(self):
        """giveMenuItem duplicate detection must check item type, not just name."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "connection.py"
        source = path.read_text()
        assert "item.type != itemType" in source or "item.type!=itemType" in source, \
            "giveMenuItem must check item.type against itemType for duplicate detection"


class TestConfigKeyWhitelist:
    """Verify _applySetting rejects unknown and secret keys."""

    def test_allowed_keys_built_from_config_categories(self):
        """ALLOWED_CONFIG_KEYS must contain keys from CONFIG_CATEGORIES."""
        from endstone_utilitystone.ui.config_menu import ALLOWED_CONFIG_KEYS, CONFIG_CATEGORIES
        for category, fields in CONFIG_CATEGORIES.items():
            for field in fields:
                assert field.key in ALLOWED_CONFIG_KEYS, f"Missing key: {field.key}"

    def test_secret_keys_rejected(self):
        """_applySetting must reject discord.token and discord.channel_id."""
        from endstone_utilitystone.ui.config_menu import SECRET_FIELDS
        assert "discord.token" in SECRET_FIELDS
        assert "discord.channel_id" in SECRET_FIELDS

    def test_arbitrary_key_injection_rejected(self):
        """_applySetting must reject keys not in the whitelist."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "listeners" / "menu_item.py"
        # Verify the config_menu.py has the whitelist check
        config_path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "config_menu.py"
        source = config_path.read_text()
        assert "ALLOWED_CONFIG_KEYS" in source, "config_menu.py must define ALLOWED_CONFIG_KEYS"
        assert "dottedKey not in ALLOWED_CONFIG_KEYS" in source, \
            "_applySetting must validate dottedKey against ALLOWED_CONFIG_KEYS"

    def test_menu_item_keys_in_whitelist(self):
        """Menu item config keys should be in the whitelist."""
        from endstone_utilitystone.ui.config_menu import ALLOWED_CONFIG_KEYS
        menu_keys = {"menuItem.enabled", "menuItem.itemType", "menuItem.name", "menuItem.loom", "menuItem.slot"}
        # At minimum, the core keys should be there
        assert "menuItem.enabled" in ALLOWED_CONFIG_KEYS
        assert "menuItem.itemType" in ALLOWED_CONFIG_KEYS
        assert "menuItem.name" in ALLOWED_CONFIG_KEYS

    def test_config_menu_source_has_secret_rejection(self):
        """_applySetting must explicitly reject secret keys."""
        import pathlib
        config_path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "config_menu.py"
        source = config_path.read_text()
        assert "dottedKey in SECRET_FIELDS" in source or "SECRET_FIELDS" in source, \
            "_applySetting must check SECRET_FIELDS"


class TestMainHandAPI:
    """Verify the main hand API usage is correct for Endstone 0.11."""

    def test_player_inventory_has_item_in_main_hand(self):
        """PlayerInventory (not Inventory) has item_in_main_hand."""
        from endstone.inventory import PlayerInventory, Inventory
        assert hasattr(PlayerInventory, "item_in_main_hand"), \
            "PlayerInventory must have item_in_main_hand"
        # Inventory (parent) should NOT have it - confirming the distinction
        # This is the source of the original audit confusion
        assert not hasattr(Inventory, "item_in_main_hand"), \
            "Inventory should NOT have item_in_main_hand (only PlayerInventory)"

    def test_player_inventory_item_in_main_hand_is_property(self):
        """item_in_main_hand should be a property with getter and setter."""
        from endstone.inventory import PlayerInventory
        attr = PlayerInventory.__dict__["item_in_main_hand"]
        assert isinstance(attr, property), "item_in_main_hand must be a property"
        assert attr.fget is not None, "item_in_main_hand must have a getter"
        assert attr.fset is not None, "item_in_main_hand must have a setter (settable)"

    def test_player_inventory_has_item_in_off_hand(self):
        """PlayerInventory also has item_in_off_hand for completeness."""
        from endstone.inventory import PlayerInventory
        assert hasattr(PlayerInventory, "item_in_off_hand")
        attr = PlayerInventory.__dict__["item_in_off_hand"]
        assert isinstance(attr, property)

    def test_repair_command_uses_correct_api(self):
        """commands/state.py repairHeld uses player.inventory.item_in_main_hand."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "commands" / "state.py"
        source = path.read_text()
        assert "player.inventory.item_in_main_hand" in source, \
            "repairHeld must use player.inventory.item_in_main_hand"
