"""Compatibility wrapper for the legacy `type_system` package name."""

from importlib import import_module
import sys

_base_ts = import_module("base.type_system")
sys.modules[__name__] = _base_ts
