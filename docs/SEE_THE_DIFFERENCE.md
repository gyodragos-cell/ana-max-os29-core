# See the difference: OS29 Core, before and after

**Working code, not a promise.** This page separates what anyone can reproduce
with the public repository from independent experiments using a private
operator-owned dataset. No private memory, credentials, models, machine
configurations, or runtime logs are shipped here.

## A reproducible improvement: a missing ID no longer loses an event

| | Previous indexing behavior | Current indexing behavior |
|---|---|---|
| Historical event JSON has no embedded event ID | The event is skipped | The SQLite primary key supplies the missing ID in memory |
| Search for that event | **0 matching entries** | **1 matching entry** |
| Original historical JSON | Not recovered | **Unchanged** |
| JSON contains an ID conflicting with SQLite | Could use the wrong embedded ID | **Excluded from the index** |

Run the example from the repository root with Python 3.11+:

    python examples/see_the_difference.py

Output from the synthetic fixture:

    OS29 PUBLIC BEFORE / AFTER (synthetic fixture)
    BEFORE legacy record indexed: 0
    AFTER  legacy record retrieved: 1
    RAW EVENT UNCHANGED: True
    OS29_PUBLIC_DIFFERENCE_DEMO_PASS

The **before** value represents the exact eligibility rule of the previous
extractor applied to the synthetic record. The **after** value comes from a
real FTS5 indexing and retrieval operation. The example uses a disposable
SQLite database and does not start a server. Regression tests also cover
missing, normal, contradictory and malformed event IDs.

    python -m pytest -q tests/test_memory_retrieval_legacy_event_ids.py tests/test_see_the_difference_demo.py

The analogous local repair recovered **9 of 9** historical records during
an operator-run audit, without rewriting any historical event JSON. Those
operator-owned records are **not included** in this repository; the public
fixture above lets anyone independently test the algorithmic fix.

## Experiments: can memory find meaning instead of matching words?

The following are **local research measurements**, not new OS29 Core
production features. The underlying memory corpus is private and cannot
be downloaded from this repository, so these exact scores cannot be
independently reproduced here. Each question had **one nominated relevant
mission**, rather than an exhaustively judged relevance set.

### Pilot 1 — same 256 sampled documents, 22 questions

| Measurement | SQLite FTS5 | Local multilingual E5 |
|---|---:|---:|
| Target mission among top 10 | 12/22 (54.5%) | **16/22 (72.7%)** |
| Romanian paraphrase: target among top 10 | 1/11 (9.1%) | **5/11 (45.5%)** |
| Median CPU query latency | **0.34 ms** | 21.15 ms |

### Pilot 2 — same 512 sampled documents, separate holdout

Fusion settings were chosen on 22 existing development questions. The
following 14 held-out questions concerned **seven different missions** and
were not used for choosing the fusion weight.

| Held-out measurement | FTS5 | Local E5 | Weighted RRF hybrid |
|---|---:|---:|---:|
| Target mission among top 10 | 7/14 | **10/14** | 9/14 |
| Target mission at rank 1 | 6/14 | 6/14 | **7/14** |
| Romanian paraphrases among top 10 | 1/7 | **3/7** | 2/7 |
| Median CPU query latency | **0.42 ms** | 19.18 ms | 19.72 ms |

Document vector preparation for the 512-document E5 run took 40.26 seconds,
*separate from per-query latency*. Both methods used the same sampled text.

**Interpretation:** the semantic model more often retrieved the nominated
mission, but required roughly tens of milliseconds per CPU query versus
fractions of a millisecond for FTS5. A simple rank-fusion hybrid was **not
uniformly superior**. It increased top-1 success in the holdout but lost
one top-10 match compared with E5. The honest next experiment is a
selective semantic fallback with a larger, independently rated test set.

**Limitations:** these are small, evaluator-written query sets on sampled
operator data, with one chosen relevant target per question. They are not
randomized, exhaustive, independently blind evaluations, full-index
benchmarks, or claims of improved production accuracy.

**Release boundary:** this public OS29 Core still ships **lexical FTS5/BM25**
search. It does **not** include a preloaded embedding model, vector
database, automatic Ollama startup or deployed hybrid search. Nothing
about these experiments changes the public runtime's search defaults.

## What users can verify today

- Run the synthetic [before / after demo](../examples/see_the_difference.py)
  without a private installation or external service.
- Run the [legacy-index regression tests](../tests/test_memory_retrieval_legacy_event_ids.py)
  to verify the mismatch and preservation cases.
- Explore the separately reproducible
  [process and MCP handoff demo](PROCESS_HANDOFF_DEMO.md).
- Review the [public release boundary](../PUBLIC_RELEASE_BOUNDARY.md)
  to see exactly which private information is excluded.

We would rather show a measured limitation than claim a breakthrough
unsupported by a reproducible test.
