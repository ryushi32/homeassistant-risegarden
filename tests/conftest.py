"""Test configuration to inject local HA stubs into sys.path."""
import sys
from pathlib import Path


# Add tests/_stubs to sys.path so pytest imports local HA stubs during tests.
HERE = Path(__file__).parent
STUBS = str(HERE / "_stubs")
if STUBS not in sys.path:
    sys.path.insert(0, STUBS)

# Ensure repo root is on sys.path so tests can import custom_components
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
