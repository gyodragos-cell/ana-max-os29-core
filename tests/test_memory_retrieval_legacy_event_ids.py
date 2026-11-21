"""Regression for legacy trace JSON lacking its authoritative DB primary-key ID.

Tests use disposable SQLite stores only; original OS29 trace events are immutable.
"""
from __future__ import annotations

import json
from pathlib import Path

from os29.models import TraceEvent
from os29.retrieval import refresh_memory_index, search_memory
from os29.store import Store


def legacy_event(store: Store, *, kind: str, override_json_id: str | None = None) -> tuple[str, str]:
    event = store.record_event(TraceEvent(
        trace_id="trace-legacy-compat",
        source="pytest",
        component="legacy-index-recovery",
        kind=kind,
        action="recover legacy event index",
        outcome="success",
        attributes={
            "status_code": 200,
            "Authorization": "Bearer hidden-legacy-credential",
            "request_body": "never-index-legacy-private-payload",
        },
    ).to_dict())
    with store._connect() as conn:
        original = conn.execute(
            "SELECT event_json FROM trace_events WHERE event_id=?", (event["event_id"],)
        ).fetchone()["event_json"]
        data = json.loads(original)
        if override_json_id is None:
            data.pop("event_id", None)
        else:
            data["event_id"] = override_json_id
        legacy_raw = json.dumps(data, ensure_ascii=True, sort_keys=True)
        conn.execute(
            "UPDATE trace_events SET event_json=? WHERE event_id=?",
            (legacy_raw, event["event_id"]),
        )
    return event["event_id"], legacy_raw


def test_legacy_missing_id_gets_indexed_under_real_primary_key_without_trace_mutation(tmp_path: Path):
    store = Store(tmp_path / "legacy.db")
    event_id, legacy_raw = legacy_event(store, kind="legacy.recovery")
    first = refresh_memory_index(store)
    assert first["inserted"] == 1
    with store._connect() as conn:
        record = conn.execute(
            "SELECT doc_id, source_ref, title, body, metadata_json "
            "FROM memory_documents WHERE doc_id=?", (f"event:{event_id}",)
        ).fetchone()
        assert record is not None
        assert record["source_ref"] == event_id
        assert json.loads(record["metadata_json"])["event_id"] == event_id
        assert conn.execute(
            "SELECT event_json FROM trace_events WHERE event_id=?", (event_id,)
        ).fetchone()[0] == legacy_raw
        indexed_blob = " ".join(str(record[key]) for key in ("title", "body", "metadata_json"))
        assert "hidden-legacy-credential" not in indexed_blob
        assert "never-index-legacy-private-payload" not in indexed_blob
    found = search_memory(store, "legacy.recovery", source_types=["event"], refresh=False)
    assert found["result_count"] == 1
    assert found["results"][0]["source_ref"] == event_id
    second = refresh_memory_index(store)
    assert second["inserted"] == 0
    assert second["updated"] == 0
    assert second["unchanged"] == 1


def test_existing_matching_event_id_is_kept(tmp_path: Path):
    store = Store(tmp_path / "normal.db")
    observed = store.record_event(TraceEvent(
        trace_id="trace-normal",
        source="pytest",
        component="healthy-event",
        kind="normal.trace",
        action="normal indexed trace",
        outcome="success",
    ).to_dict())
    changed = refresh_memory_index(store)
    assert changed["inserted"] == 1
    found = search_memory(store, "normal.trace", source_types=["event"], refresh=False)
    assert found["result_count"] == 1
    assert found["results"][0]["source_ref"] == observed["event_id"]


def test_conflicting_embedded_event_id_is_not_indexed_under_the_wrong_key(tmp_path: Path):
    store = Store(tmp_path / "mismatch.db")
    authoritative_id, raw = legacy_event(
        store, kind="legacy.spoof", override_json_id="incorrect-legacy-event-id"
    )
    refresh_memory_index(store)
    with store._connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_documents WHERE doc_id IN (?, ?)",
            (f"event:{authoritative_id}", "event:incorrect-legacy-event-id"),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT event_json FROM trace_events WHERE event_id=?", (authoritative_id,)
        ).fetchone()[0] == raw


def test_invalid_json_kept_untouched_and_not_indexed(tmp_path: Path):
    store = Store(tmp_path / "broken.db")
    event_id, _ = legacy_event(store, kind="legacy.broken")
    with store._connect() as conn:
        conn.execute(
            "UPDATE trace_events SET event_json=? WHERE event_id=?",
            ('{"incomplete":', event_id),
        )
    refresh_memory_index(store)
    with store._connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_documents WHERE doc_id=?",
            (f"event:{event_id}",),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT event_json FROM trace_events WHERE event_id=?", (event_id,)
        ).fetchone()[0] == '{"incomplete":'
