from __future__ import annotations

import json
from pathlib import Path

from integrations.os28 import MockOS28Provider, ToolDescriptor


def test_os28_mock_is_deterministic_and_offline():
    mock = MockOS28Provider()
    descriptor = mock.list_tools()[0]
    assert isinstance(descriptor, ToolDescriptor)
    assert descriptor.name == "example.echo"
    assert mock.call("example.echo", {"text": "hello"}) == {"text": "hello", "mock": True}


def test_public_mcp_example_uses_placeholder_paths():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "examples" / "mcp_client.example.json").read_text(encoding="utf-8"))
    assert data["mcpServers"]["os29-local"]["env"]["OS29_DB_PATH"].startswith("<local-path>")


def test_readme_clones_new_core_repo():
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert (
        "git clone --branch v0.1.0 "
        "https://github.com/gyodragos-cell/ana-max-os29-core.git"
    ) in readme
    assert "cd ana-max-os29-core" in readme
    assert "git clone https://github.com/gyodragos-cell/ana-max-os29.git" not in readme


def test_ci_runs_windows_linux_and_mandatory_gitleaks():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "os: [ubuntu-latest, windows-latest]" in workflow
    assert "uses: gitleaks/gitleaks-action@v3" in workflow
    assert "fetch-depth: 0" in workflow
    assert "if command -v gitleaks" not in workflow
    assert "if: " not in workflow
