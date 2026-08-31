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
