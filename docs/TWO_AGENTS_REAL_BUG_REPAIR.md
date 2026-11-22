# Two AI agents, one real bug: RED → PATCH → GREEN

This public walkthrough reproduces the **mathematical bug class** that was
repaired in a separate local OS29 laboratory using GPT-6 and a local Qwen
coding model. The runnable example is deliberately **synthetic and offline**.
It does **not** simulate an AI model call or silently ship private memory.

## The bug that was discovered

A retrieval helper described a score as *cosine similarity* but computed
an unnormalized dot product instead. A large-magnitude document therefore
received a score of **20**, which cannot be a cosine similarity, and displaced
the semantically closer document.

The public example reproduces that defect using two fabricated 2-D vectors:

| Step | Top-ranked document | Score |
| --- | --- | ---: |
| RED: dot product masquerading as cosine | inflated_magnitude | 20.000000 |
| GREEN: normalized cosine | best_angle | 0.800000 |

The mathematical change that distinguishes the relevant ONNX expressions:

```diff
- scores = np.dot(query / query_norm, doc_vectors.T / doc_norm)
+ scores = np.dot(query / query_norm, (doc_vectors / doc_norm).T)
```

First normalize **each document row**, *then* transpose. A zero-length query
or document must be rejected **before** division; individual zero coordinates
are normal and valid. The example uses Python standard-library math, with no
NumPy/ONNX dependency, to verify the same invariants.

## Run the difference yourself

From the repository root:

```shell
python examples/cosine_red_green_demo.py
python -m pytest -q tests/test_cosine_red_green_demo.py
```

The demo prints machine-readable **before/after** ranks and these checks:

```text
OS29_PUBLIC_COSINE_RED_GREEN_DEMO_PASS
```

Tests cover scale invariance, bounded similarity, invalid and zero vectors,
stable ties, and deterministic reproduction of the original error.

## What the real AI collaboration established

In the local experiment, the initial **five of seven** targeted tests failed
against the exact original experimental ONNX function. The work was stored in
an OS29 Work Unit. A separate local Qwen agent resumed it by **ID only** and
independently reproduced the failing tests.

The smaller Qwen 3B model generated three rejected patches. Qwen 7B generated
patches that made substantial progress, but **none passed all seven tests**.
GPT-6 inspected Qwen 7B's actual generated function, corrected exactly one
matrix-normalization/transposition expression, then independently verified
the combined change.

After the collaborative fix:

- **7/7** targeted tests passed.
- **50** randomized trials of **12** vectors each matched a separate
  mathematical reference.
- An actual cached local ONNX retrieval test passed.
- The complete OS29 laboratory regression reported **433 passed**.
- Existing Golden Compare and Gate both passed; Golden was not promoted.
- Canonical private SQLite records and the FTS5 retrieval path were unchanged.

The source snapshots, raw model generation attempts, evidence receipts and
machine-specific logs **remain in the private lab**. These results describe a
measured local demonstration, **not** publicly reproduced AI reasoning or a
claim that Qwen repaired the bug unaided.

## Why this matters for OS29

The technical insight is not merely "an AI can write code." It is that a
**Work Unit carries a bug reproduction, evidence and next action between
sessions**, so an independent agent can retry the work and a reviewer can
reject invalid code without losing provenance. Red/green tests and receipts
distinguish a partial suggestion from an accepted fix.

For an entirely portable **separate-process** handoff demonstration, see
`scripts/two_process_handoff_demo.py`. That script demonstrates process
continuity, not two independently reasoned LLMs. The example in this page
demonstrates mathematical correctness, not OS29 production vector search.

## Scope of this release

This change adds documentation, an offline demonstration and tests.
It does not add a new OS29 semantic backend, run an AI model, start Ollama,
alter production FTS5, require any credentials, or upload private files.
