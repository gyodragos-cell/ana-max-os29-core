# OS29 Core v0.1.0

First public, source-only release of OS29 Core.

## Included

- Local SQLite traces, evidence records, lexical FTS5/BM25 retrieval and Work Unit checkpoints, handoffs and resume by ID.
- Python package, CLI and optional MCP STDIO interface.
- Public OS28 provider contract and deterministic offline mock. **Private OS28 runtime is not included.**
- 69 reviewed source, test, example, workflow and documentation files in the initial core tree.
- Reproducible test suite (91 tests at release preparation), privacy scanning and offline smoke test.

## Compatibility and verification

- Python 3.11+ required by package metadata.
- CI release verification uses **Python 3.12** in fresh virtual environments on **Windows and Ubuntu**.
- Tag publication is gated by successful tests and mandatory Gitleaks.
- No private databases, memory, logs, browser profiles, credentials, or PC-specific launchers are included.

## Install this version

```sh
git clone --branch v0.1.0 --depth 1 https://github.com/gyodragos-cell/ana-max-os29-core.git
cd ana-max-os29-core
python -m venv .venv
```

On Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\offline_smoke.py
```

On Linux or macOS:

```sh
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest -q
.venv/bin/python scripts/offline_smoke.py
```

## Boundaries

OS29 is not an AI model or a hosted reasoning service. FTS5 is lexical retrieval, not semantic RAG. The repository does not provide a live OS28 integration, multi-user enterprise authorization or production deployment guarantees. The legacy ANA MAX portfolio remains in a separate repository, with its own independent history.

The standard GitHub-generated source archives contain only the public Git tree at this tag. No compiled private artifacts are attached.
