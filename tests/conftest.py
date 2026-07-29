"""Shared test helpers: load the captured REE fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict[str, Any]:
    # json.loads is typed as returning Any; narrow it here so --strict stays clean and
    # every fixture is known to be an object rather than a bare list or scalar.
    payload: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return payload


@pytest.fixture
def demanda_good() -> dict[str, Any]:
    return _load("demanda_good.json")


@pytest.fixture
def demanda_malformed() -> dict[str, Any]:
    return _load("demanda_malformed.json")


@pytest.fixture
def generacion_good() -> dict[str, Any]:
    return _load("generacion_good.json")


@pytest.fixture
def precios_2024_good() -> dict[str, Any]:
    return _load("precios_2024_good.json")


@pytest.fixture
def precios_2025_good() -> dict[str, Any]:
    return _load("precios_2025_good.json")
