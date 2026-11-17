# Commercial Insurance Decision Lab

A personal, reproducible laboratory for evaluating **decision models**
(e.g., Jev from TypeSafe) against **deterministic rules baselines** on
synthetic commercial P&C underwriting tasks — starting with
**commercial property triage** (STP-Accept / Refer / Decline against a
documented, fictional Canadian carrier underwriting guide).

This is a personal project. No employer, client, or proprietary data is
used, ever. All corpora are synthetic and generated locally.

## Design principles (v0.2 plan)

1. **Task-agnostic engine.** `src/engine/` contains zero task-specific
   code. A task is a directory of declarative specs under `specs/tasks/`.
2. **The underwriting guide is a first-class artifact.** Each task ships
   a fictional carrier guide (prose + machine-readable rules table);
   ground truth is *derived* by applying it, and reason codes cite it.
3. **Cache every model response** to disk; all evaluation runs off the
   cache. LLM/Jev calls happen once per configuration.
4. **Version every run** (manifests: model, seed, prompt hash, corpus
   and guide versions).
5. **Budget caps + dry-run mode** on every paid-API client from day one.
6. **Evaluate actuarially**: confusion matrices with intervals, asymmetric
   error costs, reason-code fidelity, disagreement review.

## Layout

    specs/
      _shared/                      # schemas shared across tasks
      tasks/
        property_triage_v01/        # FIRST REGISTERED TASK (v0.1 scope)
          task_definition.yaml      # decision space, reason codes, output schema
          underwriting_guide/       # NorthStar guide: guide.md + rules_table.yaml
          corpus_spec.yaml          # document types, attributes, injectors
          scorer_config.yaml        # metrics, error-cost vector, CI settings
    src/engine/                     # generic pipeline (never edited per task)
    src/experiments/                # thin task glue (if any)
    corpus/generated/               # versioned generated corpora (gitignored bulk)
    cache/                          # JSONL response caches (gitignored)
    runs/                           # per-run manifests + outputs
    tests/                          # pytest: engine invariants, metrics, guide consistency
    docs/                           # Quarto publication + per-run reports

## Setup

    # requires: uv (brew install uv), Python 3.12+, git
    cp .env.example .env            # add TYPESAFE_API_KEY (keep private!)
    uv sync
    uv run pytest -q                # smoke tests should pass pre-implementation

## Usage (once implemented)

    uv run python -m src.engine.generate_corpus --task property_triage_v01
    uv run python -m src.engine.runner --task property_triage_v01 --runner rules
    uv run python -m src.engine.runner --task property_triage_v01 --runner jev --dry-run
    uv run python -m src.engine.metrics --run <run_id>
    quarto render docs/

See docs/methodology.qmd for the full experiment plan and limitations.
