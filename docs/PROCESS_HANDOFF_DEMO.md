# Work Unit handoff and recovery: reproducible public evidence

This guide describes a **source-level test**, not an LLM inference benchmark, a remote AI agent or a deployment of the private OS28 Gateway.

## Reproduce from a clean checkout

The demo is available on the **main development branch after v0.1.0**.
The immutable v0.1.0 tag predates this addition. Do not assume the tag has the demo.

Requirements: Python 3.11+ and a local SQLite build.

~~~sh
git clone https://github.com/gyodragos-cell/ana-max-os29-core.git
cd ana-max-os29-core
python scripts/two_process_handoff_demo.py
~~~

On a successful run, the runner emits one JSON object similar to:

~~~json
{
  "agent_a_exit": 0,
  "agent_b_interrupted_exit": 23,
  "agent_b_recovery_exit": 0,
  "completed_status": "completed",
  "crash_after_durable_checkpoint": true,
  "evidence_receipt_count": 2,
  "independent_worker_processes": 3,
  "real_model_agents_involved": false,
  "result": "PASS",
  "revision": 4,
  "schema": "os29.public_process_handoff.v1",
  "temporary_database_removed_after_run": true,
  "trace_event_count": 6,
  "work_id": "public-handoff-<unique-id>"
}
~~~

The work ID changes every run. The script creates and deletes a **temporary SQLite database** and never opens a private OS29 memory store. It never starts the OS28 Gateway, Ollama or a network listener.

## Exactly what is tested

| Process | Action | Observable outcome |
| --- | --- | --- |
| Agent-A subprocess | Creates a Work Unit, records evidence, hands off to B | Exit 0; owner changed to B |
| Agent-B subprocess | Resumes using work ID, saves a revision-checked checkpoint, then deliberately calls os._exit(23) | Exit 23 is **expected**, not a failure; terminates without graceful shutdown |
| Agent-B restarted subprocess | Reopens the store, verifies committed revision and context, runs a real Python smoke, records its actual stdout/stderr/exit code and completes | Exit 0; status completed |
| Parent verification | Reopens SQLite in another Store instance, reconstructs events and receipt | Revision 4, six ordered trace events, two evidence receipts |

The demo checks persistence at a clean process boundary and **after an abrupt process exit**. The run fails if a required state transition, event, smoke command, or revision is missing.

Run the integration tests:

~~~sh
python -m pip install -e ".[test]"
python -m pytest -q tests/test_process_handoff_demo.py tests/test_mcp_process_protocol.py
~~~

The MCP protocol integration test starts separate real Python MCP STDIO server processes against a disposable database, sends JSON-RPC initialize, tools/list, tools/call, create, handoff, resume, evidence and completion, and verifies persistence across server restarts. It also checks malformed JSON and errors from an unknown tool.

## What this does NOT prove

- It does **not** run two different LLMs or independently evaluate reasoning quality.
- OS29 verifies persisted evidence **format and outcome claims**, but cannot cryptographically prove that an external actor truly ran the command it reports. The demonstration runs a real subprocess itself and captures its output.
- It does not prove multi-machine replication, simultaneous high-volume writers, enterprise isolation or encrypted-at-rest storage.
- A deliberately interrupted child exits 23 **by design**; the parent must exit 0 for the demo to pass.
- Source coverage is measured in CI, but unit-test coverage is not proof of production readiness.

## Relation to prior private laboratory tests

The private lab previously demonstrated separate human-directed AI agents handing off real Work Units, including a GPT-1 to GPT-2 task using only a Work Unit ID, with evidence receipts. Those operational records are **not part of this public repository**, because they may contain lab-specific paths and context.

The new public demos provide repeatable, privacy-safe evidence that *any developer* can run without access to that lab. Private real-agent experiments and public deterministic process tests answer different verification questions.

## Review and limitations

The WorkUnitService handles revision-checked checkpoint and completion; the Store holds canonical SQLite trace and mission capsule data. No separate shadow Work Unit database is introduced by these demos.

For unmodified release-tag installation use v0.1.0. For this post-release integration demo use current main (or the specific commit recorded in CI). Future versions should ship changelog and release notes for changes beyond v0.1.0.
