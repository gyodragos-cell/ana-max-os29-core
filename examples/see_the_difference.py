"""Reproducible OS29 FTS5 before/after demonstration on synthetic data.

The earlier extractor skipped event JSON without an embedded event_id.
The current extractor uses the authoritative SQLite trace_events key.
No private database, model, service or network is used.

From the project root: python examples/see_the_difference.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from os29.models import TraceEvent
from os29.retrieval import refresh_memory_index, search_memory
from os29.store import Store


def run_demo() -> dict[str, object]:
    with TemporaryDirectory(prefix="os29-public-example-") as tempdir:
        store = Store(Path(tempdir) / "example.db")
        recorded = store.record_event(TraceEvent(
            trace_id="example-legacy-001",
            source="example",
            component="example-gateway",
            kind="legacy.gateway.timeout",
            action="recover indexing of legacy gateway timeout event",
            outcome="error",
            attributes={"status_code": 504},
        ).to_dict())
        event_id = recorded["event_id"]

        with store._connect() as conn:
            raw = conn.execute(
                "SELECT event_json FROM trace_events WHERE event_id=?",
                (event_id,),
            ).fetchone()["event_json"]
            event = json.loads(raw)
            assert event.pop("event_id") == event_id
            legacy_raw = json.dumps(event, sort_keys=True, ensure_ascii=True)
            conn.execute(
                "UPDATE trace_events SET event_json=? WHERE event_id=?",
                (legacy_raw, event_id),
            )

        # Model the previous extractor's eligibility rule on the same fixture.
        before = int(bool(json.loads(legacy_raw).get("event_id")))
        refreshed = refresh_memory_index(store)
        found = search_memory(
            store, "legacy gateway timeout", limit=10,
            source_types=["event"], refresh=False,
        )
        after = sum(item["source_ref"] == event_id for item in found["results"])
        with store._connect() as conn:
            stored_raw = conn.execute(
                "SELECT event_json FROM trace_events WHERE event_id=?",
                (event_id,),
            ).fetchone()["event_json"]
            indexed = conn.execute(
                "SELECT COUNT(*) FROM memory_documents WHERE doc_id=?",
                (f"event:{event_id}",),
            ).fetchone()[0]

        assert before == 0
        assert after == 1 and indexed == 1
        assert stored_raw == legacy_raw
        assert refreshed["inserted"] >= 1
        return {
            "previous_index_eligibility": before,
            "current_retrieval_hits": after,
            "historical_json_unchanged": stored_raw == legacy_raw,
            "private_database_touched": False,
        }


if __name__ == "__main__":
    print("OS29 PUBLIC BEFORE / AFTER (synthetic fixture)")
    result = run_demo()
    print("BEFORE legacy record indexed: " + str(result["previous_index_eligibility"]))
    print("AFTER  legacy record retrieved: " + str(result["current_retrieval_hits"]))
    print("RAW EVENT UNCHANGED: " + str(result["historical_json_unchanged"]))
    print("OS29_PUBLIC_DIFFERENCE_DEMO_PASS")
