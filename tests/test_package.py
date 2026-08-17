from __future__ import annotations

import importlib


def test_package_exports_version() -> None:
    package = importlib.import_module("overlord_worldsim")

    assert package.__version__ == "0.1.0"
