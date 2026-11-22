"""Offline reproducibility for synthetic public mathematical bug demo."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import math

import pytest

FILE = Path(__file__).resolve().parents[1] / "examples" / "cosine_red_green_demo.py"
SPEC = importlib.util.spec_from_file_location("cosine_red_green_demo", FILE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_before_reproduces_impossible_cosine_and_wrong_top1():
    actual = mod.faulty_ranking(mod.QUERY, mod.DOCUMENTS)
    assert actual[0] == ("inflated_magnitude", 20.0)


def test_after_returns_right_top1_and_bounded_cosine():
    actual = mod.cosine_ranking(mod.QUERY, mod.DOCUMENTS)
    assert actual[0] == ("best_angle", 0.8)
    assert all(-1.0 <= score <= 1.0 for _, score in actual)


def test_scale_invariance_for_each_document_and_query():
    baseline = mod.cosine_ranking(mod.QUERY, mod.DOCUMENTS)
    for query_scale in (0.001, 1, 7, 1000):
        for first_scale, second_scale in ((1, 1), (0.01, 100), (100, 0.001)):
            query = tuple(x * query_scale for x in mod.QUERY)
            docs = (
                (mod.DOCUMENTS[0][0], tuple(x * first_scale for x in mod.DOCUMENTS[0][1])),
                (mod.DOCUMENTS[1][0], tuple(x * second_scale for x in mod.DOCUMENTS[1][1])),
            )
            assert mod.cosine_ranking(query, docs) == baseline


@pytest.mark.parametrize("query,docs", [
    ((0.0, 0.0), mod.DOCUMENTS),
    ((1.0, 0.0), (("empty", (0.0, 0.0)),)),
    ((float("nan"), 1.0), mod.DOCUMENTS),
    ((1.0, 0.0), (("invalid", (math.inf, 1.0)),)),
    ((1.0, 0.0), (("wrong", (1.0,)),)),
])
def test_invalid_vectors_rejected(query, docs):
    with pytest.raises(ValueError):
        mod.cosine_ranking(query, docs, top_k=1)


def test_duplicate_document_ids_rejected():
    with pytest.raises(ValueError):
        mod.cosine_ranking((1.0, 0.0), (("x", (1, 0)), ("x", (0, 1))))


def test_deterministic_ties_preserve_original_order():
    actual = mod.cosine_ranking(
        (1.0, 0.0), (("first", (2, 0)), ("second", (3, 0))), top_k=2
    )
    assert [item[0] for item in actual] == ["first", "second"]


def test_entrypoint_invariants():
    actual = mod.demonstrate()
    assert actual["scale_invariant"] is True
    assert actual["zero_vector_rejected"] is True
    assert actual["ai_model_run_by_this_example"] is False
