# IPF Rescue Engine — Results Summary

**Run dir:** `runs/2026-04-25_ipf_run01`
**Pre-reg SHA:** `88eaca342b5f7fcf9dd9210a7a6e4721053826c4` (locked before any engine run)
**Engine:** Opus 4.7 adaptive thinking + xhigh effort, 4-role sequential pipeline (LOCAL, 2026-04-25)

## Verdict distribution

- **RESCUE_SUPPORTED**: 1 of 5
- **MIXED**: 0 of 5
- **INSUFFICIENT_EVIDENCE**: 4 of 5
- **MISSING**: 0 of 5

## Ranked by aggregate score

| # | Candidate | Verdict | Score | Perrin | Mech | Strat | Clin | Feas | Rescue class | Passes gate |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 05_DandQ_telomere_short_IPF | RESCUE_SUPPORTED | 12 | 2 | 2 | 3 | 3 | 2 | stratification | True |
| 2 | 04_tralokinumab_CCL18_Th2_IPF | INSUFFICIENT_EVIDENCE | 7 | 1 | 0 | 1 | 3 | 2 | biomarker_enrichment | True |
| 3 | 01_pamrevlumab_CTGF_strat | INSUFFICIENT_EVIDENCE | 6 | 1 | 1 | 0 | 3 | 1 | biomarker_enrichment | False |
| 4 | 02_bexotegrast_avb6PET_strat | INSUFFICIENT_EVIDENCE | 4 | 1 | 1 | 0 | 1 | 1 | biomarker_enrichment | True |
| 5 | 03_simtuzumab_LOXL2_AEIPF | INSUFFICIENT_EVIDENCE | 4 | 0 | 0 | 1 | 2 | 1 | wrong_endpoint | True |

## Novel insights per candidate

### 05_DandQ_telomere_short_IPF — RESCUE_SUPPORTED (12/15)
- **Rescue class:** stratification
- **Advocate claim:** Dasatinib+quercetin is a candidate for a rescue trial in telomere-short / SASP-high IPF, where alveolar-epithelial senescence burden is gene
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The Unity Biotechnology liquidation (Sept 2025) terminating UBX1325 leaves D+Q without a next-generation senolytic successor in IPF translation just as Farr 2024 (Nat Med) provides the first prospecti

### 04_tralokinumab_CCL18_Th2_IPF — INSUFFICIENT_EVIDENCE (7/15)
- **Rescue class:** biomarker_enrichment
- **Advocate claim:** RAINIER's null in unselected IPF does not falsify IL-13 blockade in the CCL18-high/Th2-high endotype (~20% of IPF), where post-2020 single-c
- **Weakest axis:** mechanism_concordance
- **Novel insight:** The advocate's central premise that 'no IPF IL-13 trial prespecified a Th2 stratifier' is empirically false: RAINIER itself prespecified a periostin (canonical IL-13-induced epithelial Th2 marker) sub

### 01_pamrevlumab_CTGF_strat — INSUFFICIENT_EVIDENCE (6/15)
- **Rescue class:** biomarker_enrichment
- **Advocate claim:** ZEPHYRUS-1 failed because unselected enrollment diluted a CTGF-high responsive subset; serum CTGF or CCN2 IHC stratification identifies the 
- **Weakest axis:** stratifier_specificity
- **Novel insight:** The 2025 unselected-on-SOC benchmarks (nerandomilast +67-81 mL, rentosertib +98 mL) have collapsed the differential value of any biomarker-enriched anti-CTGF retrial: even if a CTGF-high responder sub

### 02_bexotegrast_avb6PET_strat — INSUFFICIENT_EVIDENCE (4/15)
- **Rescue class:** biomarker_enrichment
- **Advocate claim:** BEACON-IPF failed because it enrolled αvβ6-PET-unselected IPF; the ~25-35% PET-high subset carries the active TGF-β liberation phenotype tha
- **Weakest axis:** stratifier_specificity
- **Novel insight:** The discordance pattern here — positive PET-PD target engagement coexisting with clinical futility plus mortality imbalance — is itself diagnostic: it argues that αvβ6 blockade in active fibrotic nich

### 03_simtuzumab_LOXL2_AEIPF — INSUFFICIENT_EVIDENCE (4/15)
- **Rescue class:** wrong_endpoint
- **Advocate claim:** In serum-LOXL2-high IPF (~top tertile), simtuzumab is a candidate for a rescue trial using AE-IPF rate at 52 weeks as primary endpoint, wher
- **Weakest axis:** mechanism_concordance
- **Novel insight:** The rescue's 'never-tested-in-LOXL2-high' narrative is itself falsified by the originating trial — Raghu 2017 already pre-specified LOXL2-stratified co-primary endpoints with the highest-tertile arm t


## Engine resource totals
- Total input tokens: 3,353,500
- Total output tokens: 106,326
- Approximate cost (Opus 4.7 at $15/$75 per Mtok): $58.28