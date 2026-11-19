#!/usr/bin/env python3
"""Reproducible OS29 Work Unit handoff with independent Python processes.

No AI model, OS28 gateway, or private OS29 database is required. The runner
always creates its own disposable SQLite store and starts three new processes:
agent A, agent B (interrupted), and restarted agent B.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
from uuid import uuid4

# Make direct checkout execution work before installing the package.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from os29.store import Store
from os29.work_units import WorkUnitService


CRASH_EXIT_CODE = 23
SMOKE_MARKER = "OS29_PROCESS_RECOVERY_SMOKE_OK"
AGENT_A = "demo-agent-a"
AGENT_B = "demo-agent-b"


def _require(condition: bool, explanation: str) -> None:
    if not condition:
        raise RuntimeError(explanation)


def _service() -> WorkUnitService:
    database = os.environ.get("OS29_DB_PATH")
    if not database:
        raise RuntimeError("Worker requires OS29_DB_PATH from the isolated demo runner")
    return WorkUnitService(Store(Path(database)))


def _agent_a(work_id: str) -> None:
    service = _service()
    created = service.create(
        work_id=work_id,
        project="Portable OS29 Core demo",
        objective="Prove cross-process handoff, committed checkpoint and recovery",
        owner_agent=AGENT_A,
        allowed_scope=["temporary SQLite database used only by this demo"],
        current_state={"phase": "created", "fixture": "public demo"},
        known_good=["SQLite store and WorkUnitService available"],
        known_bad=[],
        open_issues=[],
        next_steps=["Agent B resumes using only the Work Unit ID"],
        context_refs=["public-demo:handoff"],
    )
    _require(created["status"] == "active", "agent A failed to create Work Unit")
    service.record_evidence_receipt(
        work_id=work_id,
        actor_agent=AGENT_A,
        action="prepare independent process handoff",
        outcome="observed",
        evidence={"step": "created in a separate Python process"},
        next_action="send Work Unit ID to agent B",
    )
    handoff = service.handoff(
        work_id=work_id,
        from_agent=AGENT_A,
        to_agent=AGENT_B,
        summary="Agent A committed the initial state and evidence",
        next_action="Agent B resumes by Work Unit ID",
    )
    _require(handoff["status"] == "handoff_ready", "agent A did not persist handoff")
    print("AGENT_A_HANDOFF_PASS", flush=True)


def _agent_b_crash(work_id: str) -> None:
    service = _service()
    resumed = service.resume(work_id=work_id, agent_id=AGENT_B)
    _require(resumed["status"] == "handoff_ready", "agent B failed to recover handoff")
    _require(resumed["owner_agent"] == AGENT_B, "handoff owner was not updated")
    _require(resumed["evidence_receipt_count"] == 1, "agent A evidence not persisted")
    checkpoint = service.checkpoint(
        work_id=work_id,
        actor_agent=AGENT_B,
        expected_revision=resumed["revision"],
        current_state={"phase": "agent-b-checkpoint-persisted", "progress": "resumed"},
        next_steps=["Restart agent B after a hard process exit"],
        tools_used=["Python", "WorkUnitService"],
        tests=[{"name": "resume context", "result": "pass"}],
        idempotency_key="demo-crash-checkpoint",
    )
    _require(checkpoint["revision"] == 3, "unexpected checkpoint revision")
    print("AGENT_B_CHECKPOINT_COMMITTED_BEFORE_HARD_EXIT", flush=True)
    # Deliberately bypass finally/atexit: the parent expects exactly this exit.
    os._exit(CRASH_EXIT_CODE)


def _agent_b_recover(work_id: str) -> None:
    service = _service()
    resumed = service.resume(work_id=work_id, agent_id=AGENT_B)
    _require(resumed["revision"] == 3, "checkpoint revision was lost across crash")
    _require(
        resumed["current_state"].get("phase") == "agent-b-checkpoint-persisted",
        "checkpoint content was lost across crash",
    )
    _require(resumed["evidence_receipt_count"] == 1, "agent A receipt was lost")
    command = [sys.executable, "-c", f"print({SMOKE_MARKER!r})"]
    executed = subprocess.run(
        command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=False
    )
    _require(executed.returncode == 0, "independent smoke command failed")
    _require(executed.stdout.strip() == SMOKE_MARKER, "smoke output did not match")
    service.record_evidence_receipt(
        work_id=work_id,
        actor_agent=AGENT_B,
        action="execute real Python recovery smoke",
        outcome="success",
        evidence={
            "command": "python -c print(OS29_PROCESS_RECOVERY_SMOKE_OK)",
            "exit_code": executed.returncode,
            "stdout": executed.stdout,
            "stderr": executed.stderr,
        },
        next_action="complete after persistent evidence verification",
        idempotency_key="demo-agent-b-verified-smoke",
    )
    complete = service.complete(
        work_id=work_id, actor_agent=AGENT_B, expected_revision=resumed["revision"]
    )
    _require(complete["status"] == "completed", "restarted agent B did not complete")
    _require(complete["revision"] == 4, "unexpected final revision")
    print("AGENT_B_RECOVERY_AND_COMPLETION_PASS", flush=True)


def _worker_command(
    worker: str, work_id: str, database: Path
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["OS29_DB_PATH"] = str(database)
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker", worker, "--work-id", work_id],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def run() -> dict[str, Any]:
    work_id = "public-handoff-" + uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix="os29-public-process-demo-") as temporary:
        db = Path(temporary) / "demo.db"
        results: dict[str, subprocess.CompletedProcess[str]] = {}
        stages = [
            ("agent-a", 0, "AGENT_A_HANDOFF_PASS"),
            ("agent-b-crash", CRASH_EXIT_CODE, "AGENT_B_CHECKPOINT_COMMITTED_BEFORE_HARD_EXIT"),
            ("agent-b-recover", 0, "AGENT_B_RECOVERY_AND_COMPLETION_PASS"),
        ]
        for stage, expected_exit, marker in stages:
            result = _worker_command(stage, work_id, db)
            results[stage] = result
            _require(
                result.returncode == expected_exit,
                f"{stage}: expected exit {expected_exit}, got {result.returncode}; stderr={result.stderr[-600:]}",
            )
            _require(
                marker in result.stdout,
                f"{stage}: expected marker missing; stdout={result.stdout[-600:]}",
            )
        reopened = WorkUnitService(Store(db))
        unit = reopened.get(work_id=work_id)
        trace = reopened.store.list_trace(work_id)
        kinds = [event["kind"] for event in trace]
        expected_kinds = [
            "work_unit.created",
            "work_unit.evidence_receipt",
            "work_unit.handoff",
            "work_unit.checkpoint",
            "work_unit.evidence_receipt",
            "work_unit.completed",
        ]
        _require(kinds == expected_kinds, f"unexpected persistent trace: {kinds}")
        _require(unit["status"] == "completed", "final Work Unit did not survive reopening")
        _require(unit["revision"] == 4, "final revision did not survive reopening")
        _require(unit["owner_agent"] == AGENT_B, "completing agent differs from handoff recipient")
        receipt = reopened.receipt(work_id=work_id)["receipt"]
        _require(receipt["status"] == "completed", "exportable receipt lost completion")
        _require(len(receipt["evidence"]) == 2, "exportable receipt lost evidence")
        summary = {
            "schema": "os29.public_process_handoff.v1",
            "result": "PASS",
            "work_id": work_id,
            "independent_worker_processes": 3,
            "agent_a_exit": results["agent-a"].returncode,
            "agent_b_interrupted_exit": results["agent-b-crash"].returncode,
            "agent_b_recovery_exit": results["agent-b-recover"].returncode,
            "crash_after_durable_checkpoint": True,
            "completed_status": unit["status"],
            "revision": unit["revision"],
            "trace_event_count": len(trace),
            "evidence_receipt_count": len(receipt["evidence"]),
            "temporary_database_removed_after_run": True,
            "real_model_agents_involved": False,
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("agent-a", "agent-b-crash", "agent-b-recover"))
    parser.add_argument("--work-id", help="Work Unit identifier for an internal worker stage")
    arguments = parser.parse_args()
    if arguments.worker:
        if not arguments.work_id:
            parser.error("--worker requires --work-id")
        workers = {
            "agent-a": _agent_a,
            "agent-b-crash": _agent_b_crash,
            "agent-b-recover": _agent_b_recover,
        }
        workers[arguments.worker](arguments.work_id)
        return 0
    if arguments.work_id:
        parser.error("--work-id is only valid with --worker")
    try:
        print(json.dumps(run(), sort_keys=True))
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"HANDOFF_DEMO_FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
