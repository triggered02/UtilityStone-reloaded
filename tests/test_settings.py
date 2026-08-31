from endstone_utilitystone.core.settings import Settings, plainValue, readBool, readInt, readFloat, readText, sectionOf


class TestSettingsHelpers:
    def test_plainValue_unwrap(self):
        class Fake:
            def unwrap(self):
                return {"a": 1}

        result = plainValue(Fake())
        assert result == {"a": 1}

    def test_plainValue_dict(self):
        result = plainValue({"a": {"b": 1}, "c": [2, 3]})
        assert result == {"a": {"b": 1}, "c": [2, 3]}

    def test_plainValue_passthrough(self):
        assert plainValue(42) == 42
        assert plainValue("hello") == "hello"

    def test_sectionOf_valid(self):
        result = sectionOf({"section": {"key": "value"}}, "section")
        assert result == {"key": "value"}

    def test_sectionOf_missing(self):
        result = sectionOf({"other": {}}, "section")
        assert result == {}

    def test_sectionOf_not_dict(self):
        result = sectionOf({"section": "string"}, "section")
        assert result == {}

    def test_readBool_true(self):
        assert readBool({}, "key", True) is True
        assert readBool({"key": True}, "key", False) is True
        assert readBool({"key": "true"}, "key", False) is True
        assert readBool({"key": "yes"}, "key", False) is True
        assert readBool({"key": "on"}, "key", False) is True
        assert readBool({"key": "1"}, "key", False) is True

    def test_readBool_false(self):
        assert readBool({"key": False}, "key", True) is False
        assert readBool({"key": "false"}, "key", True) is False
        assert readBool({"key": "no"}, "key", True) is False

    def test_readInt_valid(self):
        assert readInt({"key": 42}, "key", 0, 0, 100) == 42

    def test_readInt_clamped(self):
        assert readInt({"key": 200}, "key", 50, 0, 100) == 100
        assert readInt({"key": -5}, "key", 50, 0, 100) == 0

    def test_readInt_invalid(self):
        assert readInt({"key": "abc"}, "key", 50, 0, 100) == 50

    def test_readFloat_valid(self):
        assert readFloat({"key": 3.14}, "key", 0.0, 0.0, 100.0) == 3.14

    def test_readFloat_clamped(self):
        assert readFloat({"key": 200.0}, "key", 50.0, 0.0, 100.0) == 100.0

    def test_readText_valid(self):
        assert readText({"key": "hello"}, "key", "default") == "hello"

    def test_readText_missing(self):
        assert readText({}, "key", "default") == "default"


class TestSettings:
    def test_default_settings(self):
        settings = Settings()
        assert settings.saveIntervalSeconds == 30.0
        assert settings.playtimeSyncSeconds == 120.0
        assert settings.usePrefix is True
        assert settings.homeDefaultLimit == 3
        assert settings.warpsNeedPermission is False
        assert settings.spawnOnFirstJoin is False
        assert settings.teleportWarmupSeconds == 3.0
        assert settings.teleportCooldownSeconds == 5.0
        assert settings.chatManaged is True
        assert settings.afkEnabled is True
        assert settings.discordEnabled is True

    def test_menu_item_defaults(self):
        settings = Settings()
        assert settings.menuItemEnabled is False
        assert settings.menuItemType == "minecraft:written_book"
        assert settings.menuItemName == "UtilityStone Menu"
        assert settings.menuItemLore == "Right-click to open the menu"
        assert settings.menuItemSlot == 8

    def test_menu_item_from_config(self):
        config = {
            "menuItem": {
                "enabled": True,
                "itemType": "minecraft:compass",
                "name": "My Menu",
                "lore": "Click me",
                "slot": 4,
            }
        }
        settings = Settings(config)
        assert settings.menuItemEnabled is True
        assert settings.menuItemType == "minecraft:compass"
        assert settings.menuItemName == "My Menu"
        assert settings.menuItemLore == "Click me"
        assert settings.menuItemSlot == 4

    def test_home_limits(self):
        config = {
            "homes": {
                "defaultLimit": 5,
                "limits": {
                    "utilitystone.homes.vip": 10,
                    "utilitystone.homes.staff": 25,
                },
            }
        }
        settings = Settings(config)
        assert settings.homeDefaultLimit == 5
        assert settings.homeLimits == {
            "utilitystone.homes.vip": 10,
            "utilitystone.homes.staff": 25,
        }

    def test_teleport_settings(self):
        config = {
            "teleport": {
                "warmupSeconds": 5,
                "cooldownSeconds": 10,
                "requestTimeoutSeconds": 120,
                "cancelOnMove": False,
                "moveTolerance": 1.5,
                "pollTicks": 20,
                "rememberDeathLocation": False,
                "historySize": 10,
            }
        }
        settings = Settings(config)
        assert settings.teleportWarmupSeconds == 5.0
        assert settings.teleportCooldownSeconds == 10.0
        assert settings.teleportRequestSeconds == 120.0
        assert settings.teleportCancelOnMove is False
        assert settings.teleportMoveTolerance == 1.5
        assert settings.teleportPollTicks == 20
        assert settings.backOnDeath is False
        assert settings.backHistorySize == 10

    def test_empty_config(self):
        settings = Settings({})
        assert settings.saveIntervalSeconds == 30.0
        assert settings.homeDefaultLimit == 3

    def test_none_config(self):
        settings = Settings(None)
        assert settings.saveIntervalSeconds == 30.0

    def test_kit_names(self):
        config = {
            "kits": {
                "starter": {"items": []},
                "tools": {"items": []},
                "vip": {"items": []},
            }
        }
        settings = Settings(config)
        names = settings.kitNames()
        assert names == ["starter", "tools", "vip"]

    def test_kit_definition(self):
        config = {
            "kits": {
                "starter": {"items": [{"type": "minecraft:stone_sword"}], "cooldown": "24h"},
            }
        }
        settings = Settings(config)
        defn = settings.kitDefinition("starter")
        assert defn is not None
        assert defn["cooldown"] == "24h"

    def test_kit_definition_missing(self):
        settings = Settings()
        assert settings.kitDefinition("nonexistent") is None
