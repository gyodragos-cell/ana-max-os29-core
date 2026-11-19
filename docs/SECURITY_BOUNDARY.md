# Security boundary

This public project contains source code, fixtures and interface contracts;
it contains no user runtime state. Source selection is allowlist-based rather
than relying on .gitignore as the primary privacy control.

The installer controls its own local SQLite path. Redaction helpers and
scope checks do not replace an operating-system permissions policy. Optional
network/terminal integrations have their own risk profiles and should be
reviewed before use in production.

This new OS29 Core repository starts from a clean root commit and does not
include Git objects from the separate legacy portfolio repository.
Report discovered credentials privately and rotate them as needed; the
legacy repository's historical data remains a separate review task.
