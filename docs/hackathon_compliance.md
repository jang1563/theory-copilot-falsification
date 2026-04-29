# Hackathon Origin and Compliance Notes

Lacuna was originally built for the *Built with Opus 4.7* Hackathon in April
2026. This page preserves the hackathon-specific provenance and submission
notes so the main README can read as a scientific research package.

## Code Provenance

Every commit in `git log` has a timestamp from 2026-04-22 04:01 ET or later
(the earliest commit in the repository). All code in the submitted tree was
written during the hackathon.

Pre-hackathon scaffold files are explicitly excluded via `.gitignore` and are
not part of the public submission:

- `src/lacuna/contracts.py`
- `src/lacuna/qc.py`
- `src/lacuna/reuse_inventory.py`
- `src/lacuna/reuse_plan.py`
- `src/lacuna/staging.py`
- `src/lacuna/workflow_data.py`
- matching pre-hackathon config, docs, and tests

The hackathon-built code is the artifact; no pre-existing project serves as
underlying infrastructure in the git-lex sense.

## Managed Agents Features

Per Anthropic's 2026-04-23 response to the Agent Teams waitlist request,
research-preview features were disabled for hackathon participants to keep
evaluation fair.

The hackathon submission used public-beta features only:

- Path B: single agent + `agent_toolset_20260401`
- Path A: sequential chain of three Path B sessions
- Path C: Claude Code Routines `/fire` HTTP client

The orchestrator-with-`callable_agents` code path exists in
`_run_path_a_callable_agents` as an architectural reference, guarded by an env
flag that was not set during the submitted run.

## Data Access

Every dataset used in the pipeline is publicly accessible without
authentication or email registration.

| Dataset | Source | Access |
|---|---|---|
| TCGA-KIRC (STAR TPM + clinical) | GDC open access | `data/build_tcga_kirc*.py` |
| GSE40435, GSE53757 | NCBI GEO | `data/build_gse*.py` |
| IMmotion150 Phase 2 | cBioPortal REST API (`rcc_iatlas_immotion150_2018`) | `data/build_immotion150.py` |
| CPTAC-3 ccRCC proteogenomic | PDC GraphQL + cBioPortal mirror | `data/build_cptac3_ccrcc.py` |
| TCGA-BRCA, TCGA-LUAD | GDC open access | `data/build_tcga_brca.py`, `build_tcga_luad.py` |

No dataset used for the public artifacts requires an institutional-email
login, dbGaP controlled-access application, or any other gate that would fail
the hackathon Q&A test: "this isn't accessible to everyone."

Published-research knowledge cited in prompts is open-access per PubMed, arXiv,
or DOI-linked source pages.

## Repository Visibility

The repository was public during the judging window:

`https://github.com/jang1563/lacuna-falsification`

License:

- code: MIT
- data artifacts: CC-BY-4.0
