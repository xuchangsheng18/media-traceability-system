"""Intentional isolated CI fault; never merge this branch into main."""

import json
from pathlib import Path


def test_main_protection_fault_is_disabled():
    fixture = Path(__file__).resolve().parents[1] / "fixtures/main-protection-probe.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    assert data["fault_enabled"] is False, "EXPECTED_GATE_PROBE_FAILURE_DO_NOT_MERGE"
