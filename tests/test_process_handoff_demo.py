from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "scripts" / "two_process_handoff_demo.py"


def _execute(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DEMO), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )


def test_three_independent_processes_recover_a_crashed_checkpoint():
    process = _execute()
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["schema"] == "os29.public_process_handoff.v1"
    assert result["result"] == "PASS"
    assert result["independent_worker_processes"] == 3
    assert result["agent_a_exit"] == 0
    assert result["agent_b_interrupted_exit"] == 23
    assert result["agent_b_recovery_exit"] == 0
    assert result["crash_after_durable_checkpoint"] is True
    assert result["completed_status"] == "completed"
    assert result["revision"] == 4
    assert result["evidence_receipt_count"] == 2
    assert result["trace_event_count"] == 6
    assert result["temporary_database_removed_after_run"] is True
    assert result["real_model_agents_involved"] is False


def test_each_run_uses_an_independent_work_unit():
    first = _execute()
    second = _execute()
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    a = json.loads(first.stdout)
    b = json.loads(second.stdout)
    assert a["work_id"] != b["work_id"]
    assert a["completed_status"] == b["completed_status"] == "completed"


def test_worker_does_not_depend_on_private_or_implicit_database():
    # Without an OS29_DB_PATH, the isolated worker cannot accidentally
    # modify an unrelated local database.
    # The parent test runner may have OS29_DB_PATH configured; in that case
    # subprocess.run() below explicitly drops it for this boundary check.
    from os import environ

    env = environ.copy()
    env.pop("OS29_DB_PATH", None)
    guarded = subprocess.run(
        [sys.executable, str(DEMO), "--worker", "agent-a", "--work-id", "public-demo-test"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert guarded.returncode != 0
    assert "OS29_DB_PATH" in guarded.stderr
    assert _execute("--worker", "agent-a").returncode != 0
