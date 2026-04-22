# Session Coordination Contract

**Last updated:** 2026-04-22
**Status:** active during the hackathon submission window (2026-04-22 → 2026-04-26)

This project is edited in parallel by two long-running Claude sessions sharing
one git working tree. This file is the coordination contract. Do not skip.

---

## Lane assignment

| Lane | Codename | Owns (exclusive write) | Primary scope |
|---|---|---|---|
| **L1** | Engineering | `src/**/*.py`, `tests/**/*.py`, `config/law_proposals.json`, `data/**`, `results/**`, `Makefile`, `.audit-patterns`, `.gitignore`, `.env.example`, HPC compute (`cayuga-login1`, `phobos`) | Code, tests, HPC compute, derived artifacts |
| **L2** | Narrative | `README.md`, `docs/**/*.md`, `prompts/**/*.md`, `STATUS.md`, `CLAUDE.md`, `AGENTS.md`, submission form, Loom script | Judge-facing narrative, dashboards, writing |
| **Shared** | — | `pyproject.toml`, `.gitignore` (low-frequency), `SESSION_COORDINATION.md` (this file) | Either lane may edit, but only with the other lane's acknowledged pull |

## Hard rules

1. **Always `git pull --rebase origin main`** before starting a work block.
   If the rebase fails, resolve conflicts locally; do not `git push --force`.
2. **Commit and push within one hour** of starting a work block.
   Long-lived uncommitted diffs invite merge conflicts across sessions.
3. **Commit message prefix**: `[L1]` or `[L2]` so the other lane can triage
   git log at a glance.
4. **Owner-only writes** for exclusive files. If you need a change in the
   other lane's files, open a `HANDOFF_<lane>.md` note at repo root (that
   file is gitignored; reviewed by the owner before being acted on).
5. **Never amend a pushed commit**. Add a new commit instead.
6. **`make audit` must pass before any push**. The compliance check runs
   a pattern match against tracked files and rejects any institutional
   identifier (see `.audit-patterns`).

## File ownership quick map

```
L1 writes:
  src/theory_copilot/*.py        cli, falsification, opus_client, visualize,
                                 managed_agent_runner, cost_ledger
  src/pysr_sweep.py              PySR sweep driver
  src/falsification_sweep.py     Batch falsification driver
  tests/**/*.py                  Test suite
  config/law_proposals.json      Law family templates (biology-anchored)
  config/datasets.json           Dataset cards
  data/build_*.py                Public-data download scripts
  data/*.csv, data/examples/*    Derived public data
  results/**                     PySR + falsification outputs, RESULTS.md
  Makefile, .audit-patterns      Build + compliance
  .gitignore, .env.example       Environment
L2 writes:
  README.md                      Project landing page
  STATUS.md                      Dashboard + Decision Log + BP tracker
  docs/*.md                      Methodology, why_opus_4_7,
                                 demo_walkthrough, submission_description,
                                 managed_agents_verification,
                                 opus47_api_verification, pysr_setup,
                                 loom_script, null_narrative, leakage_audit
  prompts/*.md                   Opus 4.7 role prompts
```

## Sync points

| When | What |
|---|---|
| Start of session | `git fetch origin && git pull --rebase origin main` |
| After any commit | `git push origin main` |
| If `git status` shows files owned by other lane as modified | Don't touch. Let the owner commit. |
| Before submission push (4/26) | Both lanes pause for 30 min; do a final coordinated `make audit` + `make test`; only then submit |

## Current work queue (2026-04-22)

### L1 Engineering queue

1. **L1.1** — Drift 1 fix: post-process PySR candidate equations to substitute
   `x0..xN` → gene names; run Opus ex-ante laws from `law_proposals.json` as
   a separate candidate set → `results/opus_exante_report.json`.
2. **L1.2** — Biology-anchored PySR rerun (if time): smaller search space,
   `variable_names` honored in output.
3. **L1.3** — Live Opus 4.7 Proposer call on real TCGA-KIRC feature list →
   `artifacts/live_opus_proposer.jsonl`.
4. **L1.4** — Managed Agents Path B live run (Night 2 short) →
   `artifacts/live_managed_agents.jsonl`.
5. **L1.5** — Visualization plots: separation histogram + falsification
   panel → `results/plots/`.
6. **L1.6** — Combined 3-tier `results/COMBINED_REPORT.md`.

### L2 Narrative queue

1. **L2.1** — Document the tier1/tier2 rationale in `docs/methodology.md`
   + `STATUS.md` (Drift 2).
2. **L2.2** — Judge-persona README section (Boris / Lydia / Jason / domain
   expert views).
3. **L2.3** — `docs/null_narrative.md`: defend 0-survivors result.
4. **L2.4** — `docs/loom_script.md`: 90s demo script.
5. **L2.5** — Submission form draft (150 words + supplementary fields).
6. **L2.6** — Refresh `docs/methodology.md` with the real +0.029 ceiling
   finding.
7. **L2.7** — `docs/leakage_audit.md`: train/test split, standardization,
   sample overlap.
8. **L2.8** — STATUS.md dashboard refresh, Decision Log prune of stale
   commit SHAs.

## Drift inventory (for L2)

- **Drift 1** — "PySR candidate equations lost biology anchor": PySR 0.19.4
  on HPC did not honor `variable_names` in equation rendering; candidates
  come back with `x0..xN` and empty `law_family`. L1.1 fixes this.
- **Drift 2** — "tier1/tier2 split not in backup plan": this was a
  deliberate Route 5' 3-tier design (tumor-vs-normal as the saturated
  task, stage as the hard task). Needs documentation, not code change.

## Escape hatch

If either lane thinks the other lane's direction is wrong, the correct move
is to write `HANDOFF_to_<lane>.md` at repo root describing the concern,
and continue own-lane work while waiting for an owner response. Do not
edit the other lane's files unilaterally.
