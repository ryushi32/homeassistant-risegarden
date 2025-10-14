import importlib.util
import sys
from pathlib import Path
import types

# Load the light module directly from file to avoid importing Home Assistant packages
ROOT = Path(__file__).resolve().parents[1]
pkg_path = ROOT / "custom_components" / "risegarden"
light_path = pkg_path / "light.py"

# Ensure a package module exists for 'risegarden' with proper __path__ so relative imports work
pkg = types.ModuleType("risegarden")
pkg.__path__ = [str(pkg_path)]
sys.modules["risegarden"] = pkg

spec = importlib.util.spec_from_file_location("risegarden.light", str(light_path))
light = importlib.util.module_from_spec(spec)
sys.modules["risegarden.light"] = light

# Create minimal fake homeassistant package and submodules required by the module
if "homeassistant" not in sys.modules:
    ha = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha

components = types.ModuleType("homeassistant.components")
sys.modules["homeassistant.components"] = components

light_mod = types.ModuleType("homeassistant.components.light")
class _DummyLightEntity:
    pass
light_mod.LightEntity = _DummyLightEntity
sys.modules["homeassistant.components.light"] = light_mod

config_entries_mod = types.ModuleType("homeassistant.config_entries")
class _DummyConfigEntry:
    pass
config_entries_mod.ConfigEntry = _DummyConfigEntry
sys.modules["homeassistant.config_entries"] = config_entries_mod

core_mod = types.ModuleType("homeassistant.core")
class _DummyHomeAssistant:
    pass
core_mod.HomeAssistant = _DummyHomeAssistant
sys.modules["homeassistant.core"] = core_mod

helpers = types.ModuleType("homeassistant.helpers")
sys.modules["homeassistant.helpers"] = helpers

upd = types.ModuleType("homeassistant.helpers.update_coordinator")
class _DummyCoordinatorEntity:
    def __init__(self, coordinator=None):
        pass
class _DummyDataUpdateCoordinator:
    pass
upd.CoordinatorEntity = _DummyCoordinatorEntity
upd.DataUpdateCoordinator = _DummyDataUpdateCoordinator
sys.modules["homeassistant.helpers.update_coordinator"] = upd

spec.loader.exec_module(light)

_brightness_to_level = light._brightness_to_level
_level_to_brightness = light._level_to_brightness


def test_brightness_to_level():
    assert _brightness_to_level(0) == 0
    assert _brightness_to_level(255) == 100
    assert _brightness_to_level(128) in (50, 51)


def test_level_to_brightness():
    assert _level_to_brightness(0) == 0
    assert _level_to_brightness(100) == 255
    assert _level_to_brightness(50) in (127, 128)
