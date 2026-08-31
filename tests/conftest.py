import importlib
import sys
import types


def _make_module(name):
    mod = types.ModuleType(name)
    mod.__path__ = []
    sys.modules[name] = mod
    return mod


def _make_class(name="FakeClass"):
    return type(name, (), {})


def _real_endstone_available():
    """Check if the real endstone package is installed and importable."""
    try:
        endstone_spec = importlib.util.find_spec("endstone")
        if endstone_spec is None:
            return False
        # Check it's not one of our own mocks
        origin = getattr(endstone_spec, "origin", None)
        if origin and "conftest" in str(origin):
            return False
        # Verify it has real C extensions (pybind11)
        location = getattr(endstone_spec, "submodule_search_locations", None)
        return True
    except Exception:
        return False


# Only create mocks if the real endstone package is NOT installed
if not _real_endstone_available():
    endstone = _make_module("endstone")
    endstone.ColorFormat = type("ColorFormat", (), {
        "GRAY": "\u00a77",
        "GREEN": "\u00a7a",
        "YELLOW": "\u00a7e",
        "RED": "\u00a7c",
        "AQUA": "\u00a7b",
        "WHITE": "\u00a7f",
        "GOLD": "\u00a76",
        "LIGHT_PURPLE": "\u00a7d",
        "DARK_AQUA": "\u00a73",
        "BOLD": "\u00a7l",
        "RESET": "\u00a7r",
    })()

    endstone.Player = type("Player", (), {
        "has_permission": lambda self, p: True,
        "send_message": lambda self, m: None,
        "send_error_message": lambda self, m: None,
        "send_form": lambda self, f: None,
        "perform_command": lambda self, c: None,
        "teleport": lambda self, loc: True,
        "kick": lambda self, msg: None,
    })

    plugin_mod = _make_module("endstone.plugin")
    plugin_mod.Plugin = type("Plugin", (), {
        "api_version": "0.11",
        "load": "POSTWORLD",
        "prefix": "",
        "authors": [],
        "commands": {},
        "permissions": {},
        "data_folder": "",
        "logger": type("Logger", (), {
            "info": lambda self, m: None,
            "warning": lambda self, m: None,
            "error": lambda self, m: None,
        })(),
        "__init__": lambda self: None,
        "on_load": lambda self: None,
        "on_enable": lambda self: None,
        "on_disable": lambda self: None,
        "on_command": lambda self, s, c, a: False,
        "save_default_config": lambda self: None,
        "reload_config": lambda self: {},
        "register_events": lambda self, l: None,
        "_get_description": lambda self: type("Desc", (), {"version": "test"})(),
    })

    event_mod = _make_module("endstone.event")
    event_mod.EventPriority = type("EventPriority", (), {
        "LOW": 0,
        "NORMAL": 1,
        "HIGH": 2,
        "HIGHEST": 3,
        "MONITOR": 4,
    })()
    event_mod.PlayerJoinEvent = _make_class("PlayerJoinEvent")
    event_mod.PlayerQuitEvent = _make_class("PlayerQuitEvent")
    event_mod.PlayerChatEvent = _make_class("PlayerChatEvent")
    event_mod.PlayerCommandEvent = _make_class("PlayerCommandEvent")
    event_mod.ActorDamageEvent = _make_class("ActorDamageEvent")
    event_mod.PlayerDeathEvent = _make_class("PlayerDeathEvent")
    event_mod.PlayerInteractEvent = type("PlayerInteractEvent", (), {
        "Action": type("Action", (), {
            "RightClickAir": 1,
            "RightClickBlock": 2,
            "LeftClickAir": 3,
            "LeftClickBlock": 4,
        })(),
    })()
    event_mod.event_handler = lambda **kw: (lambda f: f)

    form_mod = _make_module("endstone.form")
    form_mod.ActionForm = type("ActionForm", (), {
        "__init__": lambda self, **kw: None,
        "add_button": lambda self, *a, **kw: self,
        "add_label": lambda self, *a, **kw: self,
        "add_header": lambda self, *a, **kw: self,
        "add_divider": lambda self, *a, **kw: self,
    })
    form_mod.ModalForm = type("ModalForm", (), {
        "__init__": lambda self, **kw: None,
        "add_control": lambda self, *a, **kw: self,
    })
    form_mod.MessageForm = type("MessageForm", (), {
        "__init__": lambda self, **kw: None,
    })
    form_mod.Button = type("Button", (), {"__init__": lambda self, **kw: None})
    form_mod.Label = type("Label", (), {"__init__": lambda self, **kw: None})
    form_mod.Header = type("Header", (), {"__init__": lambda self, **kw: None})
    form_mod.Divider = type("Divider", (), {"__init__": lambda self, **kw: None})
    form_mod.TextInput = type("TextInput", (), {"__init__": lambda self, **kw: None})
    form_mod.Toggle = type("Toggle", (), {"__init__": lambda self, **kw: None})
    form_mod.Slider = type("Slider", (), {"__init__": lambda self, **kw: None})
    form_mod.StepSlider = type("StepSlider", (), {"__init__": lambda self, **kw: None})
    form_mod.Dropdown = type("Dropdown", (), {"__init__": lambda self, **kw: None})

    level_mod = _make_module("endstone.level")
    level_mod.Location = type("Location", (), {"__init__": lambda self, *a: None})

    inventory_mod = _make_module("endstone.inventory")
    inventory_mod.ItemStack = type("ItemStack", (), {"__init__": lambda self, *a: None})

    asyncio_mod = _make_module("endstone.asyncio")
    asyncio_mod.submit = lambda f: None
