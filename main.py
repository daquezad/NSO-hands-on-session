"""mkdocs-macros local entry — `module_name: main` resolves to this file (not the stdlib `main`)."""

import importlib.util
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "macros" / "main.py"
_spec = importlib.util.spec_from_file_location("mkdocs_macros_custom", _IMPL)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
define_env = _mod.define_env

__all__ = ["define_env"]
