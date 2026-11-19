# Changelog

## Unreleased (after v0.1.0)

- Added reproducible three-process Work Unit handoff, abrupt-exit checkpoint and recovery demo using only disposable SQLite.
- Added separate MCP STDIO JSON-RPC subprocess handoff tests, including malformed input and verification receipts.
- Measure branch coverage in Windows/Ubuntu CI with an initial 60% floor; report actual coverage to guide future tests.
- Documented the difference between prior private agent-to-agent work and privacy-safe public process tests.
- No changes to the immutable v0.1.0 tag or to the private OS28 runtime.


## v0.1.0 — initial public OS29 Core release

- Curated portable OS29 core and WorkUnitService code.
- MCP STDIO and CLI with generic local configuration defaults.
- Optional OS28 provider interface with deterministic offline mock.
- Local privacy scanner, CI, automated tests and isolated smoke.
- Security boundary and documentation; no private runtime data shipped.
- Started an independent, clean repository history for OS29 Core.
