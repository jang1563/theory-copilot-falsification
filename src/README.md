# src/ — Script Map

## Core package

[`lacuna/`](lacuna/) — installable library (`pip install -e .`). Entry points:

| Module | Role |
|---|---|
| `lacuna/falsification.py` | 5-test statistical gate (deterministic Python) |
| `lacuna/opus_client.py` | Opus 4.7 streaming wrapper + JSON-fence-tolerant parser |
| `lacuna/managed_agent_runner.py` | Path B / A / C Managed Agents + Routines driver |
| `lacuna/cli.py` | `lacuna compare`, `replay`, `loop` commands |
| `lacuna/data_loader.py` | DatasetCard abstraction |
| `lacuna/routines_client.py` | Claude Code Routines `/fire` HTTP client |

## Pipeline scripts (main entry points)

| Script | Purpose |
|---|---|
| `pysr_sweep.py` | PySR symbolic regression with law-family injection |
| `falsification_sweep.py` | Batch falsification runner + BH-FDR |
| `make_plots.py` | Reproduce all flagship + rejection-landscape figures |
| `plot_track_a.py` | Track A task-landscape plots |
| `preregistration.py` | Emit / validate / audit pre-registration YAMLs |
| `render_rejection_log.py` | Build `results/rejection_log.html` |
| `mcp_biology_validator.py` | MCP biology-validator server (PubMed + GDC tools) |
| `falsification_sr_loop.py` | H1: Opus-steered 10-iteration SR loop (`make h1`) |
| `opus_1m_synthesis.py` | H2: 1M-context synthesis over all rejections (`make h2`) |
| `parallel_skeptic.py` | Parallel 3-model skeptic consensus (`make skeptic-review`) |

## Experiment scripts — Track A (survivor robustness)

Scripts that produced the PhL-\*, Track A, and rigor-extension evidence committed under `results/`.
Each has a corresponding `SUMMARY.md` in the matching `results/` subdirectory.

| Script | Evidence produced |
|---|---|
| `track_a_survivor_robustness.py` | 6-axis stress test on TOP2A−EPAS1 |
| `track_a_survivor_plots.py` | Survivor robustness figures |
| `track_a_survivor_replay.py` | Cross-cohort replay logic |
| `track_a_external_replay.py` | PhL-1 (SLC22A8 own-kill) + PhL-5/6 (BRCA/GSE53757) |
| `track_a_model_ablation.py` | 180-call cross-model Skeptic ablation (PhL-E2) |
| `track_a_managed_agents_path_a_probe.py` | Path A live-chain probe |
| `track_a_knockoff_sweep.py` | G1 Model-X knockoff v2 |
| `track_a_clinical_utility.py` | I3 clinical utility (Cohen's d, NNS) |
| `track_a_rashomon_set.py` | I2 Rashomon enumeration (990 two-gene pairs) |
| `track_a_information_theory.py` | I4 mutual information compactness |
| `track_a_live_opus_smoke.py` | Quick live-Opus sanity check |
| `track_a_brca_run.py` | TCGA-BRCA cross-cancer negative control |

## Experiment scripts — Track B (gate robustness)

| Script | Evidence produced |
|---|---|
| `track_b_permutation_stability.py` | Bootstrap seed variance on reject verdicts |
| `track_b_bootstrap_variance.py` | Bootstrap variance across cohort sizes |
| `track_b_cohort_size.py` | Cohort-size subsample stress test |
| `track_b_scaling_ablation.py` | Feature scaling sensitivity |
| `track_b_baseline_ablation.py` | Baseline threshold grid |
| `track_b_plots.py` | Track B figures |

## Experiment scripts — Rigor extensions (Phase G / I)

| Script | Evidence produced |
|---|---|
| `g1_knockoffs.py` | G1 Model-X knockoff (original single-run) |
| `g2_auprc_analysis.py` | G2 AUPRC + Brier + calibration reporting |
| `g3_adjusted_cox.py` | G3 covariate-adjusted Cox |
| `g4_anchor_regression.py` | G4 anchor regression cross-cohort stability |
| `g5_pysr_fraction_zero.py` | G5 PySR fraction-zero fraction analysis |
| `g6_calibration_4_6_vs_4_7.py` | G6 Opus 4.6 vs 4.7 calibration comparison |
| `i4_information_theory.py` | I4 mutual information (rigor extension version) |
| `rashomon_analysis.py` | Rashomon set analysis helper |

## Experiment scripts — Phase L capability probes (Managed Agents live evidence)

Each `phlN_*.py` script generated the `results/live_evidence/phlN_*/` artefact.
Run with a live `ANTHROPIC_API_KEY` to reproduce; the committed SUMMARY.md files are the
reviewed evidence.

| Script | PhL artefact |
|---|---|
| `phl1_slc22a8_cross_cohort.py` | PhL-1: own-kill — SLC22A8 extension fails IMmotion150 |
| `phl3_memory_smoke.py` | PhL-3: Memory public-beta smoke (day-of integration) |
| `phl4_persist_replay_smoke.py` | PhL-4: session event-log persist + replay |
| `phl5_phl6_generalization_probes.py` | PhL-5/6: BRCA + GSE53757 generalization |
| `phl7_compound_orchestrator.py` | PhL-7: MCP + Memory + gate in one session |
| `phl8_routine_fire_live.py` | PhL-8: Routines `/fire` live (HTTP 200) |
| `phl9_path_a_live_chain.py` | PhL-9: Path A sequential 3-session chain |
| `phl9v2_path_a_real_data.py` | PhL-9v2: Path A on real TCGA-KIRC via file mount |
| `phl10_memory_chain_extended.py` | PhL-10: Memory chain 3→5 lessons |
| `phl11_adversarial_critique.py` | PhL-11: Opus vs Sonnet adversarial 3-turn |
| `phl12_memory_chain_deepen.py` | PhL-12: Memory chain deepened to 8 lessons |
| `phl13_memorization_audit.py` | PhL-13: 0/10 zero-shot TOP2A−EPAS1 retrieval |
| `phl14_llm_sr_10iter.py` | PhL-14: 18/18 post-seed proposals rejected |
| `phl15_adaptive_thinking_ablation.py` | PhL-15: thinking-mode confound resolved |
| `phl16_proposer_quality.py` | PhL-16: 0/48 gated proposals pass |
| `phl17_stance_decay_7turn.py` | PhL-17: 7-turn adversarial stance decay |
| `phl18_prereg_writing_quality.py` | PhL-18: pre-registration YAML writing |
| `phl19_interpreter_depth.py` | PhL-19: Interpreter 100% vs Sonnet 0% |

## Other experiment scripts

| Script | Purpose |
|---|---|
| `phf3_immotion150_replay.py` | PhF-3: IMmotion150 pre-registered survival replay |
| `phi2_thinking_artefact.py` | PhΦ-2: thinking artefact probe |
| `phi3_labbench_reproduce.py` | PhΦ-3: LabBench reproduction |
| `phk_events_list_thinking_probe.py` | PhK: events.list thinking probe |
| `build_exante_candidates.py` | Build ex-ante candidate set for PhI-1 |
| `gate_sensitivity.py` | Gate threshold sensitivity sweep |
| `rename_candidates.py` | Candidate rename utility |
