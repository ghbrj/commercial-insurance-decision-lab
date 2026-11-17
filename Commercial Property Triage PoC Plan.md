# Commercial Property Underwriting Triage PoC
## Rationale and design plan — v0.2

*A personal, reproducible experiment: Jev decision models vs. deterministic rules on synthetic commercial property submissions evaluated against a documented underwriting guide — run locally on a Mac Mini M4, documented in the language of Canadian P&C underwriting.*

---

## 1. Rationale

### 1.1 The task, and why it is first

Commercial insurance underwriting is language-heavy document work: broker submissions, statements of values (SOVs), loss runs, and supplemental applications arrive in inconsistent formats and must be read, reconciled, classified, and routed. Ingestion and triage — *read the submission, assess it against the carrier's documented risk appetite and qualification criteria, and route it* — is the entry gate of the commercial underwriting workflow and the sub-task with the best-documented GenAI production results in the industry (e.g., Zurich's commercial submission digitisation: manual triage time 75→15 minutes, straight-through intake 10%→95%).

Within triage, this PoC anchors on a single **discrete decision**: for each submission, choose

- **STP-Accept** (eligible for straight-through processing),
- **Refer** (route to an underwriter — per the authority grid, not discretion), or
- **Decline** (outside documented appetite),

each accompanied by **reason codes tied to underwriting guide sections** and a **completeness/ambiguity flag**. A discrete decision is measurable in actuarial terms (three-way confusion matrix, asymmetric error costs), maps naturally onto Jev's `Choice` primitive, and forces the full ingestion problem — extraction is only exercised because routing is impossible without reading the documents. Commercial property is the subline: its attribute space (COPE data — construction, occupancy, protection, exposure — plus TIV, CAT zone, and loss history) is compact enough to encode as a documented rulebook in a few evenings, while remaining the way commercial property underwriters actually think.

Deferred to later phases, pluggable into the same framework: referral prioritization (queue ranking), pricing indication support, renewal/policy-check triage, and field-level extraction benchmarking.

### 1.2 Why this PoC can make a strong impression

Triage demos are commoditized in 2026 — every vendor sells one. What the public landscape lacks (confirmed by the research review behind this plan) is a **decision-quality evaluation rig**: controlled synthetic submissions with known ground truth, a deterministic baseline to beat, audit trails, uncertainty quantification, and reproducible versioned runs. No vendor publishes that, because rigorous evaluation exposes failure modes. This PoC's contribution is therefore not "an LLM can triage submissions" but **"a rigorous, reusable harness demonstrating when decision models beat rules, by how much, with what error structure, and where they fail."** That is the artifact an employer cannot buy off the shelf — and it doubles as a governance rehearsal: the evidence-trail, model-inventory and lifecycle patterns are precisely what Canadian regulators expect. OSFI Guideline E-23 on model risk management (finalized 2025, effective May 1, 2027) explicitly brings AI/ML models under principles-based, full-lifecycle oversight for federally regulated insurers, while Quebec's AMF has issued its own AI/model-risk guidance for provincially regulated insurers — so documenting provenance, runs, and validation in this rig is directly aligned with how Canadian insurers (whether under OSFI or AMF supervision) will have to govern AI-supported underwriting decisions.

### 1.3 Making it legible to Canadian P&C readers (documentation design)

Everything the lab produces — specs, reports, and codebook values — deliberately speaks the vocabulary and formats familiar to people working at Canadian P&C carriers:

- **Fictional insurer with a written underwriting guide.** The lab is anchored on *NorthStar Commercial Insurance*, a fictional Canadian commercial P&C insurer, with a documented **underwriting guide** (appetite statement, eligible/ineligible classes, TIV caps, CAT zone restrictions, protective-safeguard requirements, financial standards) and a **delegation-of-authority grid** defining what STP/refer/decline means. Ground truth is expressed as decisions *under that guide* — exactly how appetite works at real carriers, rather than arbitrary labels.
- **Canadian underwriting terminology throughout**: broker submission, COPE data, statement of values, 5-year loss runs, TIV, business interruption, CAT zone, declination, referral, authority grid, risk appetite. Extraction codebook values (construction classes, occupancy types) follow classifications a commercial property underwriter recognizes instantly.
- **Canadian catastrophe geography in the corpus**: CAT zone attributes include earthquake zones (British Columbia) and hail-prone regions (Alberta) — realistic Canadian property appetite constraints, even in v0.1's simple form.
- **Reports shaped like underwriting artifacts**: run reports formatted as underwriting-committee-style summaries (decision, reason codes, guide references, supporting evidence), metrics named the way underwriting managers discuss them (**STP rate, referral rate, leakage** from false binds, **false declines**/lost business).
- **Bilingual-friendly outputs**: Quarto reports in English, with an optional French summary section given a Quebec-adjacent audience — trivial with Quarto, high familiarity payoff.

### 1.4 Secondary goals

- A reproducible benchmark corpus (tasks + guide + ground truth + rubric) that survives model and Jev version swaps.
- A spec-driven architecture that scales to most commercial underwriting tasks with minimal new code.
- Professional-grade hygiene: pinned dependencies, versioned runs, cached outputs, tests — habits that transfer directly to production AI work.

### 1.5 Constraints acknowledged up front

Solo experimenter, evenings and weekends, Mac Mini M4 (32 GB), modest API budget for Jev. All implications are priced into the design: small corpora, confidence intervals over point estimates, aggressive caching, and a hard v0.1 milestone with everything else deferred.

### 1.6 Data boundary

Strictly no employer, client, or proprietary underwriting data — no Beneva/L'Unique content, and no reproduction of any real carrier's guide. NorthStar's underwriting guide is written from scratch, generic, and clearly fictional. This is a personal project on personal hardware; the boundary is absolute and pre-committed.

---

## 2. Development environment

### 2.1 Hardware and models

- **Mac Mini M4, 32 GB RAM.**
- **Primary local model:** Qwen3-Coder 30B (~19 GB) via Ollama, for the coding/development loop.
- **Fallback small model:** a 7–8B model resident for auxiliary tasks (schema validation, lightweight extraction smoke tests) so experiments are never blocked by memory pressure when the 30B model occupies the GPU/RAM. Design assumption: the *decision* step may need the strongest model; *extraction and formatting* degrade gracefully on small models.
- **Jev (TypeSafe decision model), pinned at 1.14.0** (not `jev-latest`). API key via `TYPESAFE_API_KEY` in a `.env` file excluded by `.gitignore`; repository kept private.
- Editor/notebook stack as convenient (VS Code, OpenCode, Quarto for the write-up), but the experiment itself lives in plain Python modules + config files, not notebooks, except for the final report.

### 2.2 Assumptions to verify before building (half-day dry run)

Confirm against the pinned Jev version: what `Choice` / `Score` / `Noul` accept as inputs; whether sampling randomness is controllable; response payload shape. Build one tiny end-to-end example (3 submissions, 1 guide rule) before the full harness. Every Jev-behavior assumption in this plan is provisional until this dry run.

---

## 3. Architecture: a spec-driven experiment rig

The repository is a **generic decision laboratory, not a triage project**: the name and structure carry no task-specific vocabulary, because tasks are registered, not hardcoded.

The rig is task-agnostic. A commercial underwriting task enters the system as **declarative artifacts**, not as code:

1. **Task Definition** — decision space (STP-Accept/Refer/Decline), allowed reason codes, escalation rules, output schema.
2. **Underwriting Guide** — the fictional carrier's documented appetite and qualification criteria, in human-readable form (Markdown/Quarto), machine-actionable via a companion rule table. Decisions cite guide sections; the guide is a first-class, versioned artifact of the corpus.
3. **Corpus Spec** — document types to generate, attribute schema, latent rulebook implementing the guide (ground-truth generator), noise/ambiguity injectors.
4. **Scorer Config** — metric set, asymmetric error costs, confidence-interval method, significance thresholds.

Adding a later task (referral prioritization, renewal triage, pricing support) means registering a new task directory with its spec set — the pipeline is untouched. This mirrors how the IAA Actuarial AI Case Studies collection and the research benchmark literature organize task extensibility.

### 3.1 Repository structure (v0.1) — generic, task-agnostic

```
commercial-insurance-decision-lab/
├── README.md                         # rationale, reproduction steps
├── _quarto.yml                       # publication: index, methodology, limitations
├── pyproject.toml                    # pinned deps (uv)
├── .gitignore                        # excludes .env, generated corpora, caches
├── .env.example                      # TYPESAFE_API_KEY placeholder (never committed)
│
├── specs/                            # declarative task registration
│   ├── _shared/                      # schemas shared across tasks
│   └── tasks/
│       └── property_triage_v01/
│           ├── task_definition.yaml  # decision space, reason codes, schema
│           ├── underwriting_guide/   # fictional NorthStar guide (markdown) + rules table (yaml)
│           ├── corpus_spec.yaml      # document types, attributes, injectors
│           └── scorer_config.yaml    # metrics, error-cost vector, CI method
│
├── src/
│   ├── engine/                       # task-agnostic core (never edited per task)
│   │   ├── generate_corpus.py        # reads corpus_spec + guide rules table
│   │   ├── jev_client.py             # budget-capped, dry-run, retry, temperature/seed logging
│   │   ├── rules_engine.py           # guide-driven deterministic baseline (spec-driven)
│   │   ├── runner.py                 # iterate corpus → write cached responses
│   │   └── metrics.py                # confusion matrices, CIs, segment stats
│   └── experiments/                  # thin, task-specific glue (if any)
│
├── corpus/
│   └── generated/                    # versioned corpora (gitignored if large)
│
├── cache/                            # JSONL: prompt hash, params, raw response, ts
├── runs/                             # one dir per run: manifest + outputs
├── tests/                            # pytest: guide-rule engine, generator invariants, metrics
└── docs/                             # index.qmd, methodology.qmd, limitations.qmd, reports per run
```

Key design points versus a task-named repo:

- The repo name (`commercial-insurance-decision-lab`) and `src/engine/` contain **zero triage-specific code**; triage lives entirely under `specs/tasks/property_triage_v01/`.
- The **underwriting guide ships inside the task spec** — it is documentation *and* executable logic (rules table) *and* the citation target for reason codes.
- `rules_engine.py` is generic: it executes whatever eligibility/qualification/threshold rules a task's rules table declares, so the baseline for any future task is "the documented guide, automated" rather than ad-hoc keywords.

### 3.2 The five non-negotiable engineering rules

1. **Cache every model response** to disk before anything else consumes it. All metric iteration runs off the cache; expensive LLM/Jev calls happen once per configuration. This is the single highest-leverage choice for limited free time.
2. **Version every run**: manifest per run recording Jev version, model identity, prompt hash, temperature/seed, corpus version, **guide version**, timestamps. Results are keyed to manifests.
3. **Budget cap + dry-run mode** in `jev_client.py` from day one: max requests/tokens per invocation, simulated responses in dry-run. A runaway paid-API loop is the classic solo-experiment killer.
4. **Tests for the deterministic parts**: pytest coverage for the guide-rule engine (known submissions → known decisions per guide section), generator invariants (latent score distribution, twin pairs identical before noise), and metrics (hand-computed fixtures).
5. **Sequential, batch-friendly execution**: runs are resumable and can proceed overnight in modest chunks.

---

## 4. Phase 1 — Author the underwriting guide, then build the corpus

The original plan jumped from attributes to decisions; in reality, submissions are never evaluated in a vacuum — they are assessed **against a documented risk appetite and qualification criteria**, typically codified in underwriting guides and manuals. The lab therefore starts with the guide, and the corpus is generated to exercise it.

### 4.1 The NorthStar underwriting guide (write this first)

A short, realistic, purely fictional document (~2–3 pages) with the sections a Canadian commercial property underwriter expects:

1. **Appetite statement** — classes and occupancies NorthStar writes; target account profile.
2. **Eligibility criteria (hard rules)** — ineligible occupancies (e.g., no cannabis grow-ops, no high-rise wood-frame); construction-class minimums; TIV caps per location; CAT zone restrictions (EQ-dominant zones in BC, hail belt in Alberta: capacity limits or automatic referral); premises conditions (vacancy limits, roof age maximums).
3. **Qualification criteria (submission requirements)** — the submission is not actionable without: complete COPE data, signed supplemental application, 5-year loss runs, current SOV with TIV detail, BI worksheet above a TIV threshold.
4. **Protective safeguards standards** — sprinkler requirements by occupancy/TIV band; alarm grades.
5. **Financial standards** — years in business, revenue stability, prior-claims thresholds.
6. **Delegation-of-authority grid** — precisely defines STP-eligible (all criteria met, latent profile clean), referral triggers (list enumerated: TIV cap proximity, CAT zone, contradiction in COPE data, loss history pattern, missing qualification item), and decline conditions (ineligible class, hard-limit breach).
7. **Rules table (machine-readable companion)** — the same criteria as a YAML table: rule id, guide section reference, attribute, operator, threshold, outcome (STP/REFER/DECLINE), reason code. One source of truth, two representations: the human-readable guide is generated from — or checked against — the rules table by a consistency test.

The guide is versioned (`guide_v01`). Its version appears in every run manifest, and a later-phase experiment re-scores the same corpus under an amended guide (`guide_v02`) to measure appetite-change sensitivity — a realistic and very presentable result.

### 4.2 Generator design: the rulebook implements the guide

Each synthetic risk gets a **latent hazard score** computed from a documented rulebook — an explicit function of risk attributes (construction class, occupancy, protection/sprinkler status, TIV band, stories, CAT zone, loss history, roof age, vacancy, adjacent hazards). But the latent score alone no longer decides the outcome: ground truth is **derived from applying the guide**:

- **Eligibility rules** (hard): any breach → Decline, with the guide section and reason code.
- **Referral triggers** (enumerated): any hit → Refer, with the trigger cited.
- **Qualification completeness**: a submission qualifies for STP-Accept only if its latent profile is clean **and** its documents are complete and unambiguous; missing or contradictory evidence routes to Refer regardless of hazard.
- **Latent score**: resolves genuinely borderline, clean-profile risks that the guide's discrete rules leave to judgment (the realistic residue of underwriting) — threshold logic documented in the guide's appetite statement.

Ground truth is thus *derived, exact, traceable to guide clauses, and reproducible* — no annotator disputes on the bulk corpus, and every expected decision carries a citation (`guide_section_id`, `rule_id`), which doubles as the rubric for judging model reason codes.

### 4.3 Noise and difficulty injectors (Corpus Spec)

- **Format variation:** ACORD-like structured application form; loose broker email narrative; tabular SOV + 5-year loss-run text. Same underlying risk, different presentation.
- **Information gaps:** omitted sprinkler status, missing construction class, stale loss runs — hits qualification criteria and forces the completeness logic.
- **Contradictions:** email says "fully sprinklered," SOV says partial; SOV TIV disagrees with the application.
- **Twins:** matched pairs differing in exactly one guide-driving attribute (e.g., TIV straddling a cap; CAT zone flip), so the decision flips — an attribution test against the guide.
- **Borderline profiles:** latent hazards straddling the appetite threshold; accounts that satisfy every hard rule but sit near a referral trigger.
- **Out-of-appetite realism:** plausible-looking risks that cleanly violate stated appetite (ineligible occupancy dressed up in strong financials) — testing whether the model respects the guide over surface impressions.

### 4.4 Segments (mapped to guide outcomes)

- **Routine** (≈50%): complete documentation, clear attributes, unambiguously STP-eligible or clearly out of appetite.
- **Complex** (≈30%): multi-location SOVs, mixed occupancy, layered loss history, at least one contradiction or referral trigger.
- **Ambiguous** (≈20%): information gaps, borderline latent scores, unusual formats, trigger-proximate profiles — resolvable only by underwriter judgment. The ambiguous segment is where Refer should dominate — and where model overconfidence vs. the rules baseline is most visible.

### 4.5 v0.1 corpus scale

Approximately **60 submissions** (~30 routine / 18 complex / 12 ambiguous) plus a **held-out set of 20** for the final validation run (used exactly once per model version). Small corpora are an acknowledged limitation; the evaluation section compensates with interval estimates and repeated runs rather than pretending statistical power that isn't there.

### 4.6 Generator validation (before any LLM run)

- **Guide-consistency test:** the human-readable guide and the machine rules table provably agree (pytest fixture walking every rule).
- **Outcome distribution sanity:** STP/Refer/Decline proportions per segment as designed; twins identical pre-noise; monotonicity of the latent rulebook.
- **Recoverability check:** fit a simple Poisson/binomial GLM of outcome on attributes and confirm the encoded drivers are recoverable (the pattern used in published GAN-synthesized ratemaking validations). If the signal isn't recoverable, fix the generator first.
- **Manual pass:** hand-triage 10 generated submissions blind against the guide, compare to latent truth — a realism and label-sanity check, and a rehearsal for the second annotator pass weeks later (self-consistency over time).

---

## 5. Phase 2 — Runners

### 5.1 Deterministic rules baseline: the guide, automated

`rules_engine.py` executes the guide's machine-readable rules table over the *parsed* structured attributes (assume extraction is given — this isolates the decision layer). Outcomes: eligibility breaches → Decline; trigger hits → Refer; complete clean profiles → STP-Accept; missing attributes → conservative Refer. Purpose: (a) a floor to beat — and a realistic one, because it is literally "what a carrier could automate today with a rules engine implementing its guide"; (b) a diagnostic — when Jev and the rules engine disagree, the divergence localizes to either reading (extraction) or judging (decision).

### 5.2 Jev decision pipeline

Three steps, each cached:

1. **Extraction** — Jev (or the local model, ablated separately) converts submission text into the fixed attribute vocabulary from the Task Definition. **Codebook pattern:** every attribute has an enumerated allowed-value set + explicit `Unknown`. Nothing outside the codebook can enter the pipeline; unmappable text flags for review. Per-attribute confidence and source-document provenance are recorded (the audit-trail pattern used in production underwriting-agent architectures — and what model-risk governance under OSFI E-23 / AMF guidance will expect).
2. **Decision** — Jev `Choice` over {STP-Accept, Refer, Decline} with **reason codes that must cite guide sections** (e.g., `DECLINE-INELIGIBLE_OCCUPANCY §2`, `REFER-TIV_CAP_PROXIMITY §2`, `REFER-INCOMPLETE_COPE §3`), consuming extracted attributes + confidence flags. `Noul` captures the uncertainty/referral rationale; `Score` (later phase) can rank the Refer queue.
3. **Run manifest** appended per submission.

Record temperature/seed with every call; disable sampling randomness where the client allows; run each configuration **k=5 times** on a subsample to measure decision stability (published actuarial-GenAI case studies replicate runs and report determinism — a cheap, persuasive result to replicate here).

### 5.3 Ablations (cheap because of caching)

- Jev with the strong vs. fallback local model doing extraction (measures how far extraction can be downsized).
- With vs. without per-attribute provenance in the prompt.
- With vs. without guide text provided in context (does citing the guide improve decision quality, or only the reason-code quality?).
- Ambiguous-segment-only scoring (the hard-problem slice).

---

## 6. Phase 3 — Evaluation

### 6.1 Actuarial, not anecdotal — in underwriting managers' language

- **Three-way confusion matrix** (STP-Accept/Refer/Decline) per segment and pooled, with **bootstrap confidence intervals** (and exact binomial intervals for small strata). No bare accuracy claims.
- **Asymmetric error accounting** per Scorer Config, reported with the vocabulary underwriting managers use: **leakage** (false STP-Accept — a mis-bound bad risk, the worst error), **false decline** (lost business), **misroute** (false Refer in either direction — efficiency, not correctness). Each with its own interval.
- **Operational metrics alongside accuracy**: projected **STP rate** and **referral rate** on the corpus — the numbers a triage initiative is actually sold on (cf. the industry's 10%→95% straight-through results).
- **Reason-code fidelity**: beyond the decision, are the cited guide sections correct? A decision can be right for the wrong reason; on a compliance artifact this matters. Scored as agreement between model citations and the ground-truth `rule_id`s.
- **Cost-weighted aggregate:** an explicit, stated-in-config error-cost vector. Sensitivity analysis over the vector — the honest way to handle a subjective calibration.
- **Disagreement review:** all Jev-vs-rules disagreements and all Jev-vs-ground-truth errors are catalogued with their audit trails, then binned (extraction miss / decision miss / guide-clause confusion / ambiguity-legitimate). This is the most presentation-worthy artifact: *where* the decision model wins and loses, clause by clause.
- **Segment lift:** performance on routine vs. complex vs. ambiguous. The headline claim the experiment can support: what fraction of routine submissions are safely automatable, at what residual error rate, with what referral burden.
- **Illustrative-not-powered disclaimer** on all conclusions, always. 60+20 submissions cannot establish production readiness; they establish a method and directional findings.

### 6.2 Statistical honesty

Paired comparisons (same submissions under Jev and rules) with McNemar-style paired tests where the discordant-pair counts permit; otherwise interval overlap is reported descriptively. Stability analysis from repeated runs distinguishes decision noise from decision error.

### 6.3 Reports — underwriting-committee format

One Quarto-generated report per run, auto-built from manifests + caches, structured like an underwriting-committee submission: corpus and guide versions, configuration, matrices, intervals, disagreement catalogue (with guide citations), stability results, and an optional French summary. Reproducible end to end: `python runner.py --task property_triage_v01 && quarto render docs/`.

---

## 7. Milestones and time boxes

| Milestone | Deliverable | Rough effort |
|---|---|---|
| **M0. Dry run** | Jev 1.14.0 API assumptions verified; 3-submission end-to-end skeleton with caching | 1–2 evenings |
| **M1. Guide** | NorthStar underwriting guide + rules table + guide-consistency tests green | 2 evenings |
| **M2. Corpus** | Generator + validation suite passing; 60-submission corpus + 20 held-out, ground truth traced to guide clauses | 2–3 evenings |
| **M3. Baseline** | Guide-driven rules engine + pytest green; baseline confusion matrix on corpus | 1–2 evenings |
| **M4. Jev runs** | Full corpus run (budget-capped, cached), k=5 stability subsample, ablations | 2–3 evenings |
| **M5. Evaluation** | Metrics, intervals, reason-code fidelity, disagreement catalogue, report | 2 evenings |
| **M6. Write-up** | Final report: method, results, limitations, scaling roadmap | 1–2 evenings |

~13–16 evenings to v0.1. If any milestone slips materially, cut ablations before cutting evaluation.

**Explicitly deferred** (do not start in v0.1): Experiments 2–4 from the original plan, referral-priority scoring within Refer, PDF/document-image rendering, pricing tasks, additional lines of business, the guide-amendment (v2) robustness experiment, and all tool/subscription comparisons (kept as personal shopping notes, not lab plan content).

---

## 8. Scaling roadmap (the framework argument)

Once validated, the rig absorbs new tasks by registering new task directories (spec triplets + guide):

- **Referral prioritization** — keep the Task Definition; add a `Score` stage ranking the Refer queue (Scorer Config gains a ranking metric such as nDCG or top-k precision).
- **Renewal/policy-check triage** — new Corpus Spec (existing-policy documents + dec-page mismatches); same decision machinery.
- **Pricing indication support** — new Scorer Config entirely (numeric tolerances, on-level vs. dislocation weighting); the Task Definition becomes *assistive* rather than *decisive*: output is a draft indication plus rationale, evaluated by actuarial accuracy standards, with human-in-the-loop framing baked in.
- **Guide-amendment robustness** — re-score the same corpus under `guide_v02` to measure how decisions shift with appetite changes; directly relevant to real carriers, whose guides change constantly and whose decision tooling must follow.
- **Field-level extraction benchmark** — decompose Step 1 into its own measured task when document realism (PDFs) arrives.

The pitch for this roadmap inside a workplace presentation: the deliverable is not a triage demo but an **evaluation capability** — the harness that lets the organization test any decision-model claim (vendor or in-house) against its own documented appetite before believing it.

---

## 9. Risks and honest caveats

| Risk | Mitigation |
|---|---|
| Jev API differs from assumptions | M0 dry run resolves this before any build |
| Guide too elaborate to encode | Rules table is deliberately small (~10–15 rules); guide prose stays 2–3 pages |
| Small-corpus overreach | Interval estimates everywhere; "illustrative" framing pre-committed |
| Memory pressure on 32 GB | Fallback small model; decoupled runs; overnight batching |
| API cost runaway | Hard caps + dry-run mode from first commit |
| Overfitting prompts to the corpus | Held-out set touched once per model version; twins measure generalization within the corpus |
| Reason-code hallucination (plausible citations, wrong clauses) | Reason-code fidelity scored explicitly against ground-truth rule ids |
| Scope creep | Milestone table with deferrals written down; nothing deferred silently resumed |
| Employer/IP entanglement | Personal repo, private, zero proprietary data; NorthStar guide written from scratch, clearly fictional; disclosed as personal work |

Synthetic data with planted signal also means favorable results are partly by construction — the honest claim is about *relative* performance and *failure localization*, never absolute production accuracy. The report states this limitation explicitly.

---

*Plan version: v0.2. Changes from v0.1: submissions are evaluated against a documented (fictional) Canadian carrier underwriting guide with qualification criteria and a delegation-of-authority grid, rather than bare threshold rules; documentation conventions added for Canadian P&C audiences; repository renamed and restructured to be task-agnostic with tasks registered under `specs/tasks/`. Supersedes the original 20-section POC outline. Grounded in the conversation's research review: arXiv 2506.18942 (GenAI actuarial case studies), CAS "Leveraging LLMs for Unstructured Claims Data Analysis", arXiv 2602.00456 (Underwrite benchmark), Variance GAN-synthesized ratemaking paper, GFT synthetic insurance data generator, AWS underwriting-agent sample, IAA-AITF Actuarial-AI-Case-Studies; Canadian governance context per OSFI Guideline E-23 (Model Risk Management, effective May 1, 2027) and AMF AI/model-risk guidance (verify current instrument details before external citation).*