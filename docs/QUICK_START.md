# Clean-clone quick start

Requirements: Python 3.11+ and Git.

1. Clone the tagged release: git clone --branch v0.1.0 https://github.com/gyodragos-cell/ana-max-os29-core.git
   Then: cd ana-max-os29-core. For ongoing development use the default main branch.
2. Create a Python venv: python -m venv .venv
3. Select the venv interpreter: on Windows .\.venv\Scripts\python.exe;
   on Linux/macOS .venv/bin/python. All commands below use this interpreter.
4. Install: <venv-python> -m pip install -e ".[test]"
5. Compile: <venv-python> -m compileall -q os29 integrations examples scripts tests
6. Test and branch coverage: <venv-python> -m pytest -q --cov=os29 --cov-branch
7. Offline smoke: <venv-python> scripts/offline_smoke.py
8. Privacy scan: <venv-python> scripts/privacy_gate.py

On current main (post v0.1.0 tag), use the public process handoff demo:

    <venv-python> scripts/two_process_handoff_demo.py

It uses temporary SQLite storage and independent Python processes. The v0.1.0
tag does not include this newer demonstration.

Python under .venv should be used after creating the environment. The sample
smoke creates an SQLite file in a temporary directory only. No private storage,
Windows drive layout, third-party gateway or Ollama server is needed.

For MCP clients, adapt examples/mcp_client.example.json with your OWN local
paths. The .env.example is reference material only: it is not automatically
loaded. Do not point test tools at a database containing private memory.
