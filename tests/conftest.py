"""Test configuration to inject local HA stubs into sys.path."""
import os
import sys


HERE = os.path.dirname(__file__)
STUBS = os.path.join(HERE, "_stubs")
if STUBS not in sys.path:
    sys.path.insert(0, STUBS)
import sys
from pathlib import Path

# Ensure repo root is on sys.path so tests can import custom_components
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
