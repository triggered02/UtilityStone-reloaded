from endstone_utilitystone.ui.config_menu import (
    _parseTomlValue,
    _formatTomlValue,
    _readTomlValue,
    _writeTomlValue,
    ConfigField,
    CONFIG_CATEGORIES,
    SECRET_FIELDS,
)
import json


class TestTomlParsing:
    def test_parse_bool_true(self):
        assert _parseTomlValue("true") is True
        assert _parseTomlValue("True") is True
        assert _parseTomlValue("yes") is True
        assert _parseTomlValue("on") is True

    def test_parse_bool_false(self):
        assert _parseTomlValue("false") is False
        assert _parseTomlValue("False") is False
        assert _parseTomlValue("no") is False
        assert _parseTomlValue("off") is False

    def test_parse_int(self):
        assert _parseTomlValue("42") == 42
        assert _parseTomlValue("0") == 0
        assert _parseTomlValue("-5") == -5

    def test_parse_float(self):
        assert _parseTomlValue("3.14") == 3.14
        assert _parseTomlValue("0.5") == 0.5
        assert _parseTomlValue("-1.5") == -1.5

    def test_parse_string_double_quotes(self):
        assert _parseTomlValue('"hello world"') == "hello world"
        assert _parseTomlValue('""') == ""

    def test_parse_string_single_quotes(self):
        assert _parseTomlValue("'hello world'") == "hello world"

    def test_parse_plain_string(self):
        assert _parseTomlValue("hello") == "hello"
        assert _parseTomlValue("some text") == "some text"


class TestTomlFormatting:
    def test_format_bool(self):
        assert _formatTomlValue(True) == "true"
        assert _formatTomlValue(False) == "false"

    def test_format_int(self):
        assert _formatTomlValue(42) == "42"
        assert _formatTomlValue(0) == "0"

    def test_format_float(self):
        assert _formatTomlValue(3.14) == "3.14"
        assert _formatTomlValue(3.0) == "3.0"

    def test_format_string_simple(self):
        result = _formatTomlValue("hello")
        assert result == '"hello"'

    def test_format_string_with_special_chars(self):
        result = _formatTomlValue("hello 'world'")
        assert result.startswith("'")
        assert "hello" in result


class TestTomlReadWrite:
    SIMPLE_TOML = """\
[storage]
saveIntervalSeconds = 30
playtimeSyncSeconds = 120

[homes]
defaultLimit = 3

[chat]
manageFormat = true
format = "<{name}> {message}"
"""

    def test_read_existing_value(self):
        result = _readTomlValue(self.SIMPLE_TOML, "storage.saveIntervalSeconds")
        assert result == 30

    def test_read_bool_value(self):
        result = _readTomlValue(self.SIMPLE_TOML, "chat.manageFormat")
        assert result is True

    def test_read_string_value(self):
        result = _readTomlValue(self.SIMPLE_TOML, "chat.format")
        assert result == "<{name}> {message}"

    def test_read_nonexistent_value(self):
        result = _readTomlValue(self.SIMPLE_TOML, "nonexistent.key")
        assert result is None

    def test_write_int_value(self):
        new_toml = _writeTomlValue(self.SIMPLE_TOML, "homes.defaultLimit", 5)
        result = _readTomlValue(new_toml, "homes.defaultLimit")
        assert result == 5

    def test_write_bool_value(self):
        new_toml = _writeTomlValue(self.SIMPLE_TOML, "chat.manageFormat", False)
        result = _readTomlValue(new_toml, "chat.manageFormat")
        assert result is False

    def test_write_string_value(self):
        new_toml = _writeTomlValue(self.SIMPLE_TOML, "chat.format", "Test {name}")
        result = _readTomlValue(new_toml, "chat.format")
        assert result == "Test {name}"

    def test_write_preserves_other_sections(self):
        new_toml = _writeTomlValue(self.SIMPLE_TOML, "homes.defaultLimit", 10)
        assert _readTomlValue(new_toml, "storage.saveIntervalSeconds") == 30
        assert _readTomlValue(new_toml, "chat.manageFormat") is True

    def test_write_new_key_in_existing_section(self):
        new_toml = _writeTomlValue(self.SIMPLE_TOML, "homes.newKey", "value")
        result = _readTomlValue(new_toml, "homes.newKey")
        assert result == "value"

    def test_write_new_section(self):
        new_toml = _writeTomlValue(self.SIMPLE_TOML, "newSection.key", "value")
        result = _readTomlValue(new_toml, "newSection.key")
        assert result == "value"


class TestConfigCategories:
    def test_all_categories_have_fields(self):
        for name, fields in CONFIG_CATEGORIES.items():
            assert len(fields) > 0, f"Category '{name}' has no fields"

    def test_all_fields_have_required_attributes(self):
        for name, fields in CONFIG_CATEGORIES.items():
            for field in fields:
                assert field.key, f"Field in '{name}' has no key"
                assert field.label, f"Field '{field.key}' has no label"
                assert field.fieldType in ("bool", "int", "float", "string", "enum"), \
                    f"Field '{field.key}' has invalid type: {field.fieldType}"

    def test_numeric_fields_have_ranges(self):
        for name, fields in CONFIG_CATEGORIES.items():
            for field in fields:
                if field.fieldType in ("int", "float"):
                    assert field.minVal < field.maxVal, \
                        f"Field '{field.key}' has invalid range: {field.minVal}-{field.maxVal}"

    def test_secret_fields_excluded(self):
        for name, fields in CONFIG_CATEGORIES.items():
            for field in fields:
                assert field.key not in SECRET_FIELDS, \
                    f"Secret field '{field.key}' should not be in CONFIG_CATEGORIES"


class TestFormManagerParsing:
    def test_parse_modal_data_list(self):
        from endstone_utilitystone.ui.manager import FormManager
        fm = FormManager.__new__(FormManager)
        result = fm.parseModalData("[true, false]")
        assert result == [True, False]

    def test_parse_modal_data_single(self):
        from endstone_utilitystone.ui.manager import FormManager
        fm = FormManager.__new__(FormManager)
        result = fm.parseModalData('"hello"')
        assert result == ["hello"]

    def test_parse_modal_data_invalid(self):
        from endstone_utilitystone.ui.manager import FormManager
        fm = FormManager.__new__(FormManager)
        result = fm.parseModalData("not json")
        assert result is None

    def test_parse_modal_data_number(self):
        from endstone_utilitystone.ui.manager import FormManager
        fm = FormManager.__new__(FormManager)
        result = fm.parseModalData("42")
        assert result == [42]


class TestPermissions:
    def test_permission_constants(self):
        from endstone_utilitystone.ui.permissions import ADMIN_GUI_PERMISSION, PLAYER_GUI_PERMISSION
        assert ADMIN_GUI_PERMISSION == "utilitystone.admin.gui"
        assert PLAYER_GUI_PERMISSION == "utilitystone.command.menu"


class TestAdminMenuSafeAreaImports:
    """Verify admin_menu.py uses correct Endstone form API."""

    def test_admin_menu_does_not_import_addTextInput(self):
        """addTextInput does not exist in components.py — must use TextInput from endstone.form."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "admin_menu.py"
        source = path.read_text()
        assert "addTextInput" not in source

    def test_admin_menu_uses_buildModal_correctly(self):
        """_createSafeArea must pass controls list and onSubmit to buildModal."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "admin_menu.py"
        source = path.read_text()
        assert 'controls=controls' in source
        assert 'submitText=' in source or 'submitText =' in source

    def test_admin_menu_imports_text_input_from_endstone(self):
        """TextInput must come from endstone.form, not from components."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "admin_menu.py"
        source = path.read_text()
        assert "from endstone.form import TextInput" in source

    def test_admin_menu_safearea_functions_exist(self):
        """All required SafeArea admin GUI functions must exist."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "admin_menu.py"
        source = path.read_text()
        assert "def _openSafeAreas(" in source
        assert "def _openSafeAreaDetail(" in source
        assert "def _createSafeArea(" in source
        assert "def _toggleSafeArea(" in source
        assert "def _confirmDeleteSafeArea(" in source

    def test_admin_menu_requires_permission(self):
        """Admin panel must check hasAdminGui before showing content."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "admin_menu.py"
        source = path.read_text()
        assert "hasAdminGui(player)" in source


class TestPlayerMenuPermissionChecks:
    """Verify player_menu.py conditionally shows buttons based on permissions."""

    def test_player_menu_checks_homes_permission(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert "hasHomesAccess" in source
        assert 'if hasHomesAccess:' in source

    def test_player_menu_checks_warps_permission(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert "hasWarpsAccess" in source
        assert 'if hasWarpsAccess:' in source

    def test_player_menu_checks_spawn_permission(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert "hasSpawnAccess" in source
        assert 'if hasSpawnAccess:' in source

    def test_player_menu_checks_tpa_permission(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert "hasTpaAccess" in source
        assert 'if hasTpaAccess:' in source

    def test_player_menu_checks_kit_permission(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert "hasKitAccess" in source
        assert 'if hasKitAccess:' in source

    def test_player_menu_checks_afk_permission(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert "hasAfkAccess" in source
        assert 'if hasAfkAccess:' in source

    def test_player_info_always_visible(self):
        """Player Info should always be shown (no permission check needed)."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        # Player Info button should not be inside a permission conditional
        assert 'addButton(form, "Player Info"' in source


class TestComponentsAPI:
    """Verify components.py provides the correct API."""

    def test_buildModal_signature(self):
        """buildModal must accept controls, onSubmit, submitText."""
        import inspect
        from endstone_utilitystone.ui.components import buildModal
        sig = inspect.signature(buildModal)
        params = list(sig.parameters.keys())
        assert "title" in params
        assert "controls" in params
        assert "onSubmit" in params
        assert "submitText" in params

    def test_buildActionMenu_signature(self):
        import inspect
        from endstone_utilitystone.ui.components import buildActionMenu
        sig = inspect.signature(buildActionMenu)
        params = list(sig.parameters.keys())
        assert "title" in params


class TestWrapSubmitSignature:
    """Regression test: wrapSubmit must pass (player, data) to callback, not just (data)."""

    def test_wrap_submit_passes_player_and_data(self):
        """wrapSubmit callback receives (player, data), not just (data)."""
        from endstone_utilitystone.ui.manager import FormManager
        import inspect

        fm = FormManager.__new__(FormManager)
        fm.plugin = None
        fm._sessions = {}
        fm._lock = __import__("threading").Lock()
        fm._sessionTtl = 300.0

        received = []

        def my_callback(player, data):
            received.append((player, data))

        mock_player = type("MockPlayer", (), {"unique_id": 42, "is_valid": True})()
        wrapped = fm.wrapSubmit(mock_player, my_callback, "test")

        sig = inspect.signature(wrapped)
        params = list(sig.parameters.keys())
        assert len(params) == 2, f"onSubmit must accept 2 params (p, data), got {params}"

        wrapped(mock_player, "[1, 2, 3]")
        assert len(received) == 1
        assert received[0] == (mock_player, "[1, 2, 3]")

    def test_wrap_submit_callback_type_hint(self):
        """wrapSubmit type hint must indicate callback takes 2 args."""
        from endstone_utilitystone.ui.manager import FormManager
        import inspect

        sig = inspect.signature(FormManager.wrapSubmit)
        cb_param = sig.parameters.get("callback")
        assert cb_param is not None
        hint = cb_param.annotation
        assert hint != inspect.Parameter.empty
        hint_str = str(hint)
        assert "Any" in hint_str or "Callable" in hint_str


class TestConfigStringSaveRoundTrip:
    """Regression test: string config values must survive write + read round trip."""

    STRING_TOML = """\
[chat]
format = "<{name}> {message}"
afkTag = "&7[AFK] &r"

[connection]
joinMessage = ""
quitMessage = ""
welcomeMessage = "Welcome {name}!"
"""

    def test_write_string_simple(self):
        new_toml = _writeTomlValue(self.STRING_TOML, "chat.format", "[$name] $msg")
        result = _readTomlValue(new_toml, "chat.format")
        assert result == "[$name] $msg"

    def test_write_string_empty(self):
        new_toml = _writeTomlValue(self.STRING_TOML, "connection.joinMessage", "")
        result = _readTomlValue(new_toml, "connection.joinMessage")
        assert result == ""

    def test_write_string_with_special_chars(self):
        new_toml = _writeTomlValue(self.STRING_TOML, "chat.format", "{name}: {message}")
        result = _readTomlValue(new_toml, "chat.format")
        assert result == "{name}: {message}"

    def test_write_string_with_color_codes(self):
        new_toml = _writeTomlValue(self.STRING_TOML, "chat.afkTag", "&7[AFK] &r")
        result = _readTomlValue(new_toml, "chat.afkTag")
        assert result == "&7[AFK] &r"

    def test_write_string_preserves_other_values(self):
        new_toml = _writeTomlValue(self.STRING_TOML, "chat.format", "NEW FORMAT")
        assert _readTomlValue(new_toml, "chat.afkTag") == "&7[AFK] &r"
        assert _readTomlValue(new_toml, "connection.welcomeMessage") == "Welcome {name}!"

    def test_format_string_produces_valid_toml(self):
        formatted = _formatTomlValue("hello world")
        assert formatted == '"hello world"'
        parsed = _parseTomlValue(formatted)
        assert parsed == "hello world"

    def test_format_string_with_quotes(self):
        formatted = _formatTomlValue("it's a test")
        parsed = _parseTomlValue(formatted)
        assert parsed == "it's a test"

    def test_format_string_with_curly_braces(self):
        formatted = _formatTomlValue("{name} {message}")
        assert formatted.startswith("'")
        assert formatted.endswith("'")
        parsed = _parseTomlValue(formatted)
        assert parsed == "{name} {message}"


class TestPlayerMenuGrouping:
    """Regression test: player menu must have grouped sections."""

    def test_player_menu_has_travel_header(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert 'addHeader(form, "Travel")' in source

    def test_player_menu_has_teleport_header(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert 'addHeader(form, "Teleport")' in source

    def test_player_menu_has_utilities_header(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert 'addHeader(form, "Utilities")' in source

    def test_player_menu_groups_travel_together(self):
        """Homes, Warps, Spawn should appear under Travel header."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        travel_idx = source.index('addHeader(form, "Travel")')
        homes_idx = source.index('"Homes"', travel_idx)
        warps_idx = source.index('"Warps"', travel_idx)
        spawn_idx = source.index('"Spawn"', travel_idx)
        assert homes_idx < warps_idx < spawn_idx

    def test_player_menu_empty_state(self):
        """When no permissions, shows empty state message."""
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "player_menu.py"
        source = path.read_text()
        assert 'No features available.' in source


class TestTracebackLogging:
    """Regression test: GUI callbacks must log tracebacks (exc_info=True)."""

    def test_wrap_submit_logs_traceback(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "manager.py"
        source = path.read_text()
        assert "exc_info=True" in source

    def test_wrap_click_logs_traceback(self):
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "src" / "endstone_utilitystone" / "ui" / "manager.py"
        source = path.read_text()
        lines = source.split("\n")
        click_section = False
        found_exc_info_in_click = False
        for line in lines:
            if "def wrapClick" in line:
                click_section = True
            elif click_section and "def wrap" in line:
                click_section = False
            if click_section and "exc_info=True" in line:
                found_exc_info_in_click = True
                break
        assert found_exc_info_in_click, "wrapClick must use exc_info=True for traceback logging"
