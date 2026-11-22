"""Portable, synthetic RED -> GREEN cosine-search defect demonstration.

This file reproduces the same *class* of ranking bug repaired in a private
two-AI-agent laboratory experiment. It intentionally ships NO private OS29
records, ONNX model, agents, credentials or laboratory logs. Running it does
not invoke any AI model; it independently demonstrates the math.

Run: python examples/cosine_red_green_demo.py
"""
from __future__ import annotations

import json
import math
from typing import Sequence

Vector = Sequence[float]
Document = tuple[str, Vector]

QUERY: Vector = (1.0, 0.0)
DOCUMENTS: tuple[Document, ...] = (
    ("best_angle", (0.8, 0.6)),
    ("inflated_magnitude", (20.0, 20.0)),
)


def _validate(query: Vector, docs: Sequence[Document], top_k: int) -> None:
    if not query or not docs or not 1 <= top_k <= len(docs):
        raise ValueError("Nonempty query/docs and valid top_k required")
    if not all(math.isfinite(value) for value in query):
        raise ValueError("Query contains a nonfinite coordinate")
    q_norm = math.hypot(*query)
    if not math.isfinite(q_norm) or q_norm == 0:
        raise ValueError("Query has zero/invalid magnitude")
    ids = [ident for ident, _ in docs]
    if len(set(ids)) != len(ids):
        raise ValueError("Document IDs must be unique")
    for ident, vector in docs:
        if not ident or len(vector) != len(query):
            raise ValueError("Invalid document ID/dimension")
        if not all(math.isfinite(value) for value in vector):
            raise ValueError("Document contains a nonfinite coordinate")
        norm = math.hypot(*vector)
        if not math.isfinite(norm) or norm == 0:
            raise ValueError("Document has zero/invalid magnitude")


def faulty_ranking(query: Vector, docs: Sequence[Document],
                   *, top_k: int = 2) -> list[tuple[str, float]]:
    """Deliberate baseline bug: RAW DOT product mislabeled as cosine."""
    _validate(query, docs, top_k)
    scores = [
        (index, ident, math.fsum(a * b for a, b in zip(query, vector)))
        for index, (ident, vector) in enumerate(docs)
    ]
    scores.sort(key=lambda item: (-item[2], item[0]))
    return [(ident, round(score, 6)) for _, ident, score in scores[:top_k]]


def cosine_ranking(query: Vector, docs: Sequence[Document],
                   *, top_k: int = 2) -> list[tuple[str, float]]:
    """Correct cosine similarity, independent of positive vector scaling."""
    _validate(query, docs, top_k)
    q_norm = math.hypot(*query)
    scores: list[tuple[int, str, float]] = []
    for index, (ident, vector) in enumerate(docs):
        d_norm = math.hypot(*vector)
        cosine = math.fsum(
            (a / q_norm) * (b / d_norm) for a, b in zip(query, vector)
        )
        scores.append((index, ident, max(-1.0, min(1.0, cosine))))
    scores.sort(key=lambda item: (-item[2], item[0]))
    return [(ident, round(score, 6)) for _, ident, score in scores[:top_k]]


def demonstrate() -> dict[str, object]:
    wrong = faulty_ranking(QUERY, DOCUMENTS)
    correct = cosine_ranking(QUERY, DOCUMENTS)
    if wrong[0] != ("inflated_magnitude", 20.0):
        raise AssertionError("Synthetic RED fixture no longer reproduces the bug")
    if correct[0] != ("best_angle", 0.8):
        raise AssertionError("GREEN output differs from reference cosine")
    scaled = ((DOCUMENTS[0][0], tuple(x * 100 for x in DOCUMENTS[0][1])),
              (DOCUMENTS[1][0], tuple(x * 0.001 for x in DOCUMENTS[1][1])))
    if cosine_ranking(QUERY, scaled) != correct:
        raise AssertionError("Cosine ranking should ignore positive scaling")
    try:
        cosine_ranking((0.0, 0.0), DOCUMENTS)
    except ValueError:
        rejected_zero = True
    else:
        rejected_zero = False
    if not rejected_zero:
        raise AssertionError("A zero-length query must not return a ranking")
    return {
        "source": "synthetic mathematical fixture, no private memory",
        "before_top1": wrong[0][0],
        "before_invalid_cosine": wrong[0][1],
        "after_top1": correct[0][0],
        "after_cosine": correct[0][1],
        "scale_invariant": True,
        "zero_vector_rejected": True,
        "ai_model_run_by_this_example": False,
    }


if __name__ == "__main__":
    result = demonstrate()
    print(json.dumps(result, sort_keys=True))
    print("OS29_PUBLIC_COSINE_RED_GREEN_DEMO_PASS")
