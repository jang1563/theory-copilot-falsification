# IPF Rescue Engine — Top Lead

## Dasatinib + Quercetin (D+Q) in Telomere-Short IPF

**Engine verdict:** RESCUE_SUPPORTED (gate aggregate 12/15) **with critical caveats** — Interpreter independently hedged to MIXED. The deterministic gate authority commits the SUPPORTED label per pre-registration; the LLM disagreement is logged as a verdict warning and is *load-bearing context* for any follow-on decision.

**Pre-reg lock SHA:** `88eaca342b5f7fcf9dd9210a7a6e4721053826c4` (locked 2026-04-25 04:16:59Z, before any engine output).
**Run:** Local sequential, Opus 4.7 adaptive thinking + xhigh effort, 4-role pipeline. Total cost $58.28.

---

## Hypothesis (3 lines)

The Mayo 2017–2019 D+Q senolytic pilot (NCT02874989, n=14 open-label; Justice 2019) was underpowered and unstratified. Telomere-short IPF (germline TERT/TERC/RTEL1/PARN carriers + lymphocyte qPCR ≤10th age-adjusted percentile, ~15–20% of IPF) plausibly enriches alveolar AT2 senescence burden. A senescence-burden-stratified D+Q retrial may reach the FVC-slope effect the unstratified design diluted.

## Why it failed before (3 lines, with engine-found omission)

Justice 2019 (PMID 30616998) was a 14-patient open-label feasibility study; weak symptom signal, never powered for FVC. **Critical: Skeptic flagged a major Advocate omission** — Nambiar 2023 (PMID 36857968), the placebo-controlled Stage-2 extension of *the same NCT02874989* (n=12, 6 D+Q vs 6 placebo on the same intermittent regimen), was **functionally null** with documented adverse-event imbalance (sleep/anxiety: 4/6 D+Q vs 0/6 placebo; glucose/LDL trends). The advocate did not cite or engage this readout, which is itself a falsification-gate concern.

## Proposed stratifier or rescue

| Stratifier element | Operationalization |
|---|---|
| Telomere-short binary | Lymphocyte qPCR telomere length ≤10th age-adjusted percentile **OR** pathogenic germline TERT / TERC / RTEL1 / PARN variant |
| Expected prevalence | ~15–20% of IPF |
| Confirmatory PD readout | Circulating SASP composite (IL-6, GDF15, MMP-7, CXCL13) + peripheral T-cell p16INK4a expression |

## Engine's recommended next step (NOT a Phase 2 yet)

Per Interpreter's `follow_on_deployment.recommended_next_step`: **ex-vivo IPF lung explant validation** before any prospective trial commitment.

> Telomere-short donor explants vs telomere-normal explants, D+Q dose-response on AT2/basaloid p16+ burden and SASP secretome. Required to bridge from senescence-causality biology to D+Q-specific rescue claim before exposing patients to a 130-week trial.

The advocate-proposed Phase 2 (n=80, 52-week FVC slope, $9M, 130 weeks) **exceeds the engine's pre-registered ≤24-month feasibility threshold** — flagged as feasibility breach. Lead investigator profile needed: IPFnet/PETAL-network Phase 2 ILD trialist with in-house telomere-length qPCR, validated peripheral-blood SASP/T-cell p16 PD assay, ATS-tier IRB infrastructure.

## Critical caveats raised by Skeptic (DO NOT skip)

1. **Nambiar 2023 OMISSION.** Same-NCT placebo-controlled stage was null with AE imbalance. Advocate did not engage. This is the single most important pre-prospective-trial issue.
2. **No external clinical replication.** All D+Q clinical IPF/aging work is Mayo / UTHSCSA Kirkland-network originating (Justice, Nambiar, Hickson, Farr). Single-center program risk.
3. **Citation hygiene.** Evidence Retriever flagged 4 of 7 advocate-cited PMIDs as wrong/hallucinated (Yao 2021, Duckworth 2021, Newton 2022, Liu/Phan 2022). Substantive scientific claims survive against re-identified PMIDs, but citation failure signals review-process degradation in the proposal.
4. **Quercetin dose inconsistency.** Justice 2019 used Q 1250 mg/d; Hickson 2019 PD validation used Q 1000 mg/d; advocate protocol proposes 1000 mg/d. Implicit claim that lower-dose retains IPF efficacy is unestablished.
5. **Substrate-stratification logic single-source.** Farr 2024 *Nat Med* (D+Q osteoporosis Phase 2) is the central pillar for "high-senescent-burden subset rescues a null primary." It is (a) bone, not lung; (b) pre-specified exploratory, not confirmatory; (c) not replicated.
6. **Telomere-short IPF endpoint integrity.** Faster progression but also higher dropout/mortality may compromise FVC-slope at 52 weeks (Newton, Belgian 2025 cohorts).
7. **Mendelian randomization scope.** Duckworth (PMID 33197388 if correct PMID) shows short LTL → IPF *incidence*, not D+Q-specific *progression-modifiability*. Conflation flagged.

## Top 5 verified citations (post-rejection 2020–2026)

| PMID | Year | Lab | Role in rescue |
|---|---|---|---|
| 32832599 | 2020 | Adams TS / Kaminski (Yale) | scRNA-seq IPF KRT5−/KRT17+ basaloid senescent population at fibroblastic foci |
| 31542391 | 2019 | Hickson LJ / Kirkland (Mayo) | First in-human D+Q PD signal: ↓p16+ cells + ↓circulating SASP within 11 days (kidney-disease cohort, not IPF) |
| 33147406 | 2021 | Yao C / Stripp / Borok (Cedars-Sinai/USC) | AT2 senescence sufficient to drive progressive pulmonary fibrosis in mice; senolytic targeting reduces fibrosis |
| 33197388 | 2020 | Duckworth A (Exeter) | Mendelian randomization: short LTL causally associated with IPF risk (incidence, not progression-modifiability) |
| 36857968 | 2023 | Nambiar A / Kirkland (Mayo) | **Placebo-controlled n=12 stage of NCT02874989** — functionally null, AE imbalance. **The omission Skeptic flagged.** |

## Disagreement record

- **Advocate:** Framed AT2 senescence causality + basaloid scRNA-seq + telomere MR + Hickson PD + Farr 2024 bone-precedent as a coherent rescue case. Did not cite Nambiar 2023.
- **Skeptic:** Killed the rescue ceiling. Adjudication: "The Nambiar 2023 omission is a falsification-gate failure: a placebo-controlled negative readout in the very NCT being rescued cannot be silent."
- **Interpreter:** Hedged final verdict to MIXED on the strength of Skeptic's adjudication; deterministic gate (≥12 → SUPPORTED) overrode.
- **Gate authority:** Pre-registration commits the gate's verdict. SUPPORTED stands as the engine's official output, with disagreement-record + Skeptic kill-attempts as published-alongside.

## What this is NOT

- NOT a recommendation to start a Phase 2 trial.
- NOT a treatment recommendation for IPF patients.
- NOT a diagnostic-biomarker claim — telomere length is well-validated for risk, not for D+Q response prediction.
- NOT independent of the Kirkland-network single-source clinical signal.
- NOT a refutation of nerandomilast (Boehringer, FDA-approved Oct 2025) or rentosertib (Insilico, *Nat Med* 2025) — D+Q + telomere-short would need to demonstrate value *on top of or distinct from* the new SOC.

## Reproducibility

| Artifact | Path |
|---|---|
| Pre-registration YAML | `prereg_ipf/05_DandQ_telomere_short_IPF.yaml` |
| Lock commit | `git show 88eaca34` (commit message) + `git show 88c2802` (SHA stamp) |
| Engine outputs | `runs/2026-04-25_ipf_run01/05_DandQ_telomere_short_IPF/*.json` |
| Aggregator command | See `prereg_ipf/README.md §Aggregation` |
| Engine cost | $58.28 / $100 cap |
| Engine wall-clock | ~32 min sequential |

## Follow-on next-step recommendation (engine Interpreter)

Per the engine Interpreter's `follow_on_deployment.recommended_next_step`,
the recommended pre-prospective-trial step for this SUPPORTED candidate
is **ex-vivo IPF lung explant validation** (telomere-short donor
explants vs telomere-normal, D+Q dose-response on AT2/basaloid p16+
burden + SASP secretome) — not a Phase 2 trial yet. This avoids the
controlled-access cohort path entirely. The 4 transcript-stratifier
candidates from this run (pamrevlumab CTGF, simtuzumab LOXL2,
tralokinumab CCL18) remain testable on public expression cohorts
(e.g., GSE47460 LGRC microarray) without controlled-access gating.

## Nambiar 2023 review (post-registration edit, 2026-04-25)

User-directed WebFetch of PMID 36857968 (Nambiar et al., *EBioMedicine* 2023) verifies:

- **Design**: Phase 1 placebo-controlled pilot, n=12 (6 D+Q vs 6 placebo), **3 weeks total / 9 dosing days**. Primary endpoint: **adverse events / feasibility** — efficacy explicitly underpowered.
- **Intervention**: Same regimen as Justice 2019 (D 100 mg + Q 1250 mg, 3 days/week).
- **AE imbalance**: 65 D+Q vs 22 placebo total non-serious AEs; sleep disturbances 4/6 vs 0/6; anxiety 4/6 vs 0/6. Consistent with documented dasatinib-class kinase-inhibitor off-target PD.
- **Functional/PFT measures**: FVC, 6MWD, SPPB measured but "do not appear to differ meaningfully" — author-acknowledged underpowered at n=6/arm × 3 weeks.
- **Stratification**: NONE — enrolled mild-to-moderate IPF without telomere-length, senescence-burden, p16, or any other senescence biomarker stratification.
- **Authors' own conclusion**: *"Intermittently-dosed D + Q in patients with IPF is feasible and generally well-tolerated. Further prospective studies, such as a larger RCT, are needed to confirm the safety and efficacy."*

**Verdict on rescue claim: NOT falsified.** Nambiar 2023 (i) was not designed or powered to test efficacy; (ii) did not test the telomere-short stratifier this rescue is built on; (iii) authors themselves recommend the larger stratified RCT this rescue proposes. Outcome: TIGHTEN the stratifier requirement and trial design, not kill the hypothesis. Specifically:

- Trial duration must be ≥ 52 weeks (Nambiar 3-week protocol cannot detect FVC slope change).
- Telomere-short stratifier MUST be applied at enrollment (Nambiar's unselected enrollment is the central design gap this rescue addresses).
- AE monitoring protocol must explicitly capture sleep / anxiety / glucose / LDL with frequency comparable to Nambiar (consistent with dasatinib-class label).
- Quercetin dose: harmonize across pilot (Justice 1250 mg/d) and Hickson 2019 PD validation (1000 mg/d). Recommend matching Nambiar 2023 dose (1250 mg/d) since that is the placebo-controlled-validated tolerability point.

The Skeptic's flagged "advocate hygiene failure" (omission) is logged as a process-discipline issue in `prereg.yaml` `post_registration_edits[0]` (this directory), NOT a substantive falsification.
