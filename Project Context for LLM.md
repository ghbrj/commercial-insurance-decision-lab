# Project Briefing — Commercial Insurance Decision Lab
### Handoff document for an AI coding/research assistant

> **Purpose.** This file gives you full context on a personal side project so you can help with implementation, analysis, or design decisions without needing the original conversation. Read it fully before suggesting anything. The owner works on this solo, evenings/weekends, on limited free time — bias suggestions toward small, shippable steps.

---

## 1. Owner, machine, and constraints

- **Solo personal PoC**, run at home, in limited free time. Not an employer project — no proprietary data involved, ever.
- **Machine:** Mac Mini M4, 32 GB unified memory. Local LLM work must respect memory limits (~19 GB model + IDE/Quarto is tight).
- **Domain expertise:** owner is a P&C actuary at a Canadian insurer (Quebec context, French/English). Deliverables should feel familiar to Canadian P&C practitioners (broker submissions, COPE data, TIV, loss runs, CAT zones, delegation of authority, STP/referral vocabulary).
- **Time horizon:** ~13–16 evening sessions are budgeted for v0.1 per the plan. Avoid scope creep.

## 2. Project thesis (frame everything around this)

**The contribution is the evaluation rig, not the demo.** Submission-triage demos are commoditized (Zurich/Cytora, Lemonade, and every insurtech vendor sell this story). What no public PoC has — verified through an extensive research pass — is a rigorous **decision-quality benchmark** for commercial underwriting with:

- controlled synthetic submissions carrying latent ground truth,
- a specialized decision model (**Jev**, from TypeSafe — decision-oriented LLM primitives: Choice/Score/Noul) vs. a **deterministic rules baseline** (the documented underwriting guide, automated) vs. optionally a general local LLM,
- audit trails (reason codes citing guide sections + per-attribute evidence/confidence),
- reproducible runs (caching, versioning, pinned model versions),
- actuarial evaluation (asymmetric error costs, confidence intervals, disagreement review).

Headline for any write-up: *"a rigorous, reusable harness proving when decision models beat rules, by how much, and where they fail"* — not "an LLM can triage."

## 3. v0.1 task scope (locked)

- **Line of business:** commercial property.
- **Task:** submission ingestion + triage routing decision.
- **Decision space (three-way):** `STP_ACCEPT` (straight-through) / `REFER` (to underwriter) / `DECLINE`.
- **Outputs per submission:** decision + reason codes (each citing a guide rule) + evidence trail (doc, field, confidence) + completeness flag (`COMPLETE` | `GAPS` | `CONTRADICTORY`).
- **Corpus:** structured text only for v0.1 — templated broker emails, an ACORD-like form, SOV-style table, loss-run text, with deliberate format variation. **No PDFs** (deferred).
- **Corpus size:** ~80 submissions — 30 routine / 18 complex / 12 ambiguous (dev set, 60) + 20 held out. Statistics are *illustrative, not powered*; claims are directional only.
- **Fictional carrier:** *NorthStar Commercial Insurance* — invented underwriting guide, written from scratch. Explicitly no resemblance to the owner's real employer (Beneva/L'Unique); a data-boundary disclaimer sits in the README.

**Explicitly deferred** (do not reintroduce silently): PDF/real-document rendering, referral-priority ranking, pricing indication tasks, UI, cloud model subscriptions, MLX tuning.

## 4. Core design decisions (already debated and settled — don't relitigate)

1. **Guide-first ground truth.** Author the underwriting guide *before* the corpus. Ground truth is **derived by applying the guide**: eligibility breach → DECLINE (clause cited); enumerated referral trigger → REFER (trigger cited); clean complete profile → STP_ACCEPT. A latent hazard score handles only the borderline residue any discrete guide leaves to judgment. The rules baseline is "the documented guide, automated" — the fairest comparator.
2. **Guide dual representation + consistency test.** `guide.md` (prose) + `rules_table.yaml` (machine-readable, stable `rule_id`s). A pytest suite asserts they agree. Drift between them would silently corrupt ground truth — this test is the guardrail.
3. **Deterministic codebook pattern.** The model classifies submission text into a **pre-defined attribute vocabulary** (COPE enums + explicit `Unknown`); it never invents features. This comes from published best practice (CAS unstructured-claims paper; arXiv 2506.18942 with its pinned companion repo).
4. **Response caching is non-negotiable.** Every model response hits disk (JSONL: prompt, params, raw output, timestamps). Evaluation runs off the cache. Paid/local model calls happen once per configuration; metric iteration is free.
5. **Budget caps + dry-run mode from day one** on every API client (max requests/tokens per run, from `.env`).
6. **Statistical honesty.** Bootstrap/exact-binomial CIs on all rates; paired design (same submissions under both runners); k=5 repetition runs for decision stability; asymmetric error costs (false STP-accept = leakage, costed worst; false decline = lost business; referral misroutes cheaper). 60+20 submissions supports method validation, not production claims.
7. **Synthetic-signal caveat.** Favorable results are partly by construction (the signal was planted). Defensible claims: relative performance (Jev vs rules), failure localization, robustness — never absolute accuracy claims.
8. **Reason-code fidelity is scored separately** — a decision can be right for the wrong reason.
9. **GLM recoverability check** on the generator before any LLM runs: fit a simple GLM on the generated portfolio, confirm the planted drivers are recoverable; if not, fix the generator first.

## 5. Architecture: task-agnostic engine + registered tasks

The repo must stay **generic to any commercial underwriting task**; triage is merely the first registered task. Adding task #2 (e.g., referral prioritization) = writing a spec directory, zero engine changes.

```
commercial-insurance-decision-lab/     # repo name: see §9 — still being finalized
├── README.md, pyproject.toml, _quarto.yml, .pre-commit-config.yaml
├── specs/
│   ├── _shared/                        # cross-task schemas (attribute codebook, decision enum,
│   │                                   #   reason-code schema, run-manifest schema)
│   └── tasks/
│       └── property_triage_v01/        # THE registered task
│           ├── task_definition.yaml    # decision space, output schema, escalation rules
│           ├── underwriting_guide/     # guide.md (prose, TODO M1) + rules_table.yaml (TODO M1)
│           ├── corpus_spec.yaml        # segments/attributes/injectors (TODO M2)
│           └── scorer_config.yaml      # metrics, error costs, CI settings
├── src/
│   ├── engine/                         # TASK-AGNOSTIC core — must never reference triage/NorthStar
│   │   ├── generate_corpus.py          # M2   ├── jev_client.py      # M0/M4
│   │   ├── rules_engine.py             # M3   ├── runner.py          # M0/M4
│   │   └── metrics.py                  # M5
│   └── experiments/
├── corpus/generated/                   # gitignored bulk (regenerable from spec + seed)
├── cache/                              # JSONL response caches (gitignored)
├── runs/                               # per-run manifests + outputs
├── tests/                              # pytest (invariants now; guide-consistency at M1; generator tests at M2)
├── docs/                               # Quarto site: index/methodology/limitations (.qmd stubs)
└── .github/workflows/ci.yml            # lint + pytest on push; NEVER uses API keys (dry-run mode only)
```

**Engine contract:** every module in `src/engine/` reads only what task specs declare. Modules are currently import-clean stubs with contract docstrings.

## 6. Current status (as of handoff)

- ✅ Repo scaffolded via a bootstrap script; all day-one invariant tests pass (`uv run pytest -q` — 4 tests: gitignore hygiene, `.env.example` keys, task spec registry, decision-space/reason-code resolution).
- ✅ Fixes applied during setup (carry these lessons): invalid YAML in `escalation_rules` (no inline `->` pseudo-syntax in YAML); stubs must import cleanly (no top-level `raise`); **`pythonpath = ["."]` in `[tool.pytest.ini_options]`** so tests can `import src.engine...` without installing the project.
- ✅ Git initialized, initial commit made. Remote push via `gh repo create <name> --private --source=. --push` was the next step; repo **name still being chosen** (§9).
- ⬜ Nothing implemented yet: engine stubs only, guide is a TODO shell, corpus spec is placeholders.

**Environment/tooling:** `uv` (pinned lockfile), Python ≥3.12, deps: pyyaml, pandas, numpy, scipy (bootstrap CIs), statsmodels (GLM check), httpx (Jev transport), python-dotenv; dev: pytest, ruff, pre-commit (optional). CI: GitHub Actions (`setup-uv`, ruff, pytest). **Local AI stack:** Ollama + Qwen3-Coder 30B (~19 GB) driven by OpenCode for repo-level coding tasks; keep context windows moderate; consider a 7–8B fallback model for extraction subtasks under memory pressure. Quarto for publication; docs site renders findings from saved run outputs (executable Python blocks, but analysis logic lives in `src/`, not the `.qmd`).

## 7. Milestones (recommended execution order)

| # | Milestone | Deliverable |
|---|-----------|-------------|
| **M0** | Jev dry run | Minimal `jev_client.py`: one synthetic risk, one question batch (Choice + Score + Noul) against **pinned** Jev version (1.14.x — verify current at docs.typesafe.ai). Confirms API assumptions: what state/questions accept, determinism across repeats, sampling controls, latency. Writes cache + run manifest. **Do this before building anything else around it.** |
| **M1** | NorthStar guide authored | `guide.md` (2–3 pages: appetite statement, eligibility, qualification criteria, protective safeguards, financial standards, DOA grid) + `rules_table.yaml` (~10–15 rules with ids/kinds/operators/outcomes/reason codes) + `test_guide_consistency.py`. |
| **M2** | Corpus generator | `generate_corpus.py` reads corpus spec; attribute codebook (COPE + TIV + CAT zones incl. BC quake/Alberta hail + loss history) with enums + `Unknown`; injectors: format variation, gaps, contradictions, twins (identical except one attribute), borderline scores, out-of-appetite-dressed-up. Ground truth emitted by applying the guide. Generator invariant tests (twins differ as expected, monotonicity, segment mixes). GLM recoverability check passes. |
| **M3** | Rules engine baseline | Applies `rules_table.yaml` to each submission's ground-truth attributes. Rules-baseline unit tests (known risk → known decision). |
| **M4** | Runners + Jev integration | `runner.py` executes a configured runner over the corpus, writes per-run manifests (run id, task, guide/corpus/question versions, runner, model name+version, temperature/seed, prompt hash, per-submission predictions + probabilities + reason codes + evidence). Includes the local-LLM runner path (same structured output categories required of the general model). |
| **M5** | Metrics + analysis | `metrics.py`: three-way confusion matrices (pooled + per segment), bootstrap CIs, cost-weighted aggregates with sensitivity analysis over error costs, reason-code fidelity, STP/referral rates, k=5 stability, McNemar-style paired comparison, disagreement review export (one row per submission where runners differ, with the evidence needed to adjudicate). Tightens the placeholder metric contract test. |
| **M6** | Quarto publication | Rendered site: experimental setup, synthetic portfolio, results with auto-generated tables/charts from `runs/`, findings, limitations. Optional French summary. Committee-summary formatting (STP rate, referral rate, leakage proxies). |

Suggested git-milestone commits exist per milestone in the plan; README documents the project, not a dev log.

## 8. Robustness & evaluation specifics to honor (from the v0.2 plan)

- **Controlled twins** (identical submissions differing in one attribute — e.g., US-revenue pct 5%→60%, generic vs. 60%-roofing contractor) test whether semantic assessments move appropriately.
- **Contradiction probes**: declared industry vs. operations description clash (e.g., "software development" that "manufactures and installs control panels").
- **Missing attributes / verbose padding / irrelevant info / borderline scores / wording paraphrase variants** all injected systematically and tracked by injector tag, so error analysis can be segmented by failure mode.
- **Disagreement review is a first-class artifact**, not an appendix: cases where Jev and rules diverge get individually inspected with the audit trail visible.
- **Deferred "guide amendment" experiment** (post-v0.1, very presentable): re-score the same corpus under a modified appetite; tests guide-interpretation agility.
- **Regulatory framing (Canadian):** governance expectations come from OSFI Model Risk Management guidance (E-23 analogue) for federally regulated insurers and Quebec AMF expectations provincially. ⚠️ The owner knows these specific instrument names/dates must be **re-verified against osfi-bsif.gc.ca and lafq.ca/AMF sources before citing them in any workplace-facing material** — do not assert them as verified facts.

## 9. Open items

- **Repo name**: owner wants something smarter/lighter than `commercial-insurance-decision-lab`; shortlisted candidates included `paper-risks` (top pick — synthetic portfolio of nonexistent businesses), `true-north-triage`, `second-underwriter`. Not yet renamed/pushed; renaming later is trivial on GitHub.
- **Jev API surface verification (M0)**: all Jev behaviors assumed in the plan (state+questions→structured answers via Choice/Score/Noul primitives, multi-question batching, version pinning at 1.14.x, sampling controls) are **unverified assumptions** until the dry run.
- **Cloud upgrade path**: explicitly *not* subscribed now; local-first. Only trial one month of an agentic-coding subscription (Claude Pro or ChatGPT Plus/Codex) if OpenCode+Qwen genuinely bottlenecks; track intervention rate before deciding.

## 10. Hard data boundary (non-negotiable)

Use only: synthetic policy/risk data, fictional underwriting criteria, public insurance concepts, public TypeSafe/Jev docs, the owner's own code. **Never use:** employer policies/submissions/manuals, real insured/broker information, internal rating or referral rules, internal code or datasets — not even anonymized fragments. README carries an explicit disclaimer. If any suggestion would require proprietary material, refuse it.

## 11. Known caveats inherited from the research phase (state these when discussing results)

- Small-corpus: directional findings only; report CIs, label as illustrative.
- Planted-signal: absolute accuracy claims invalid; compare runners relatively.
- Star counts/vendor benchmark claims from the research pass were indicative, not audited.
- Anything the assistant adds that contradicts this brief should be challenged by the owner; anything in this brief the owner has since changed supersedes it.

---

**How to help best:** pick the nearest milestone (currently M0), keep changes small and tested, respect the engine/task separation, keep paid-API calls behind budget caps, and always preserve reproducibility (specs + seed → corpus; cache + manifest → results → report).
