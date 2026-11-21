"""Contract regression for the public, isolated before/after demonstration."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from see_the_difference import run_demo


def test_public_demo_recovers_legacy_trace_without_editing_original_json():
    result = run_demo()
    assert result["previous_index_eligibility"] == 0
    assert result["current_retrieval_hits"] == 1
    assert result["historical_json_unchanged"] is True
    assert result["private_database_touched"] is False
