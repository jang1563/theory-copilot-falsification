# HPC Discovery Experiments — Session Briefing 2026-04-26

## Status as of 2026-04-26 14:00 ET

**Platform generalization COMPLETE** (committed + pushed, commits 7d5f04b–93f4b3c):
- pysr_sweep.py bug fixed: `variable_names` now passed to `fit()` (commit ea6fd0a)
- 4 new tracks run via SLURM job 2812758, `make smoke` + `make audit` pass

**Currently running HPC job**: 2812300 (`lsib-open-data-downstream`) — UNRELATED project, zero overlap
**HPC directories**: `data_driven_discovery/` (main) + `theory_copilot_h1/` (H1 loop)

## What Exists in `results/track_a_task_landscape/` (cross-task matrix: 11 configs)

| Directory | Task | Key Finding | Status |
|-----------|------|-------------|--------|
| `metastasis_expanded/` | KIRC M0 vs M1 | TOP2A−EPAS1 AUROC 0.726 | ✅ **FLAGSHIP** |
| `stage_expanded/` | KIRC Stage I-II vs III-IV (45-gene) | 23/28 survivors, CXCR4/EPAS1 (0.689) | ✅ NEW |
| `lihc/` | LIHC tumor vs normal | 0/26 (ALB saturates ~0.985) | ❌ expected |
| `coad_msi/` | COAD stage I-II vs III-IV | **15/22 survivors** — SLC2A1+PDCD1LG2+VIM−MYC (0.658) | ✅ NEW |
| `gbm_idh/` | LGG Grade II vs III | **2/25 survivors** — log1p(TWIST1×MKI67+VIM)−CDH2/NES (0.840) | ✅ NEW |
| `luad/` | LUAD tumor vs normal | 0 (SFTPC saturates) | ❌ expected |
| `g5_fraction_zero/` | KIRC unseeded PySR | **PENDING** — Julia cold-start blocked | ⚠️ |
| `external_replay/gse53757/` | KIRC stage→secondary | AUROC 0.714 | ✅ |
| `external_replay/immotion150/` | ccRCC survival | 3/3 survival tests pass | ✅ |

## 4 New Discovery Experiments

---

### Experiment 1: TCGA-LIHC Microvascular Invasion (MVI) — PRIORITY 1

**Why high potential:**
- LIHC tumor-vs-normal already failed (ALB saturates). MVI is a *harder, clinically relevant task*.
- AFP single-gene AUROC ~0.61 for MVI — below the delta_baseline threshold.
- EpCAM is a known MVI predictor but compound laws haven't been published.
- Pattern analogy: `EpCAM − CDK1` parallels `TOP2A − EPAS1` (stemness minus proliferation).

**Data:** n≈305 TCGA-LIHC with MVI pathology annotation
- Gene matrix: GDC-Xena STAR_TPM (`TCGA-LIHC.star_tpm.tsv.gz`)
- MVI label: cBioPortal Pan-Cancer Atlas (`lihc_tcga_pan_can_atlas_2018`)

**Gene panel (19 genes):** `TOP2A, MKI67, CDK1, CCNB1, PCNA, EPCAM, SOX9, CD44, VIM, ZEB1, CDH1, CDH2, SNAI1, EPAS1, HIF1A, VEGFA, GPC3, TERT, AFP`

**Script:** `data/build_lihc_mvi.py` → `data/lihc_mvi.csv`
**SLURM:** In `scripts/hpc_new_diseases.sbatch` as `lihc_mvi` experiment
**Results go to:** `results/track_a_task_landscape/lihc_mvi/`

**Pre-registered prediction:** `EPCAM + CDK1` or `EPAS1 + EPCAM` compound AUROC ≥ 0.70, delta_baseline ≥ 0.05 over AFP alone.

---

### Experiment 2: IPF BAL Transcriptomics — PRIORITY 2

**Why high potential:**
- IPF gene discovery hasn't been done (only fabrication audit of trial results).
- SPP1 and CCL20 are known IPF markers but NEVER combined in a compact symbolic law.
- GSE93606 has a clean composite endpoint (death OR FVC >10% decline at 6 months).
- GSE70867 (n=176) for replication.

**Data:**
- GSE93606: 60 IPF + 20 controls, BAL fluid microarray (Affymetrix HTA 2.0), 6-month CEP
- GSE70867: 176 IPF, multi-centre, OS 100/176 died

**Gene panel (17 genes):** `SPP1, CTHRC1, COL1A1, MMP7, CCL18, CCL20, KRT17, KRT5, MUC5B, AGER, SFTPC, CAV1, TGFB1, IL6, CXCL12, ACTA2, PDGFRA`

**Script:** `data/build_ipf_bal.py` → `data/ipf_bal_gse93606.csv`, `data/ipf_bal_gse70867.csv`
**SLURM:** In `scripts/hpc_new_diseases.sbatch` as `ipf_lgrc` experiment
**Results go to:** `results/track_a_task_landscape/ipf_lgrc/`

**Pre-registered prediction:** `SPP1 − CCL20` or `CTHRC1 − AGER` compound AUROC ≥ 0.70, delta_baseline ≥ 0.05 over SPP1 alone.

**Note on metadata parsing:** GEO series matrices vary in how phenotypes are encoded. Run `build_ipf_bal.py` locally first and inspect output to verify label counts before HPC submission. If composite endpoint isn't in `characteristics_ch1`, check the `supplementary_file` links in GEO.

---

### Experiment 3: TCGA-PAAD Overall Survival — PRIORITY 3

**Why high potential:**
- KRAS is 90% mutated → useless for stratification.
- SMAD4 loss alone AUROC ~0.60.
- GATA6 (classical) × CDK1 (proliferation) compound: biologically justified (CDK4/6 inhibition acts differently in SMAD4-WT vs mutant), not previously formalized as a compact law.

**Data:** TCGA-PAAD n=150 pure PDAC, OS dichotomised at median (~20 months)
- Gene matrix: GDC-Xena STAR_TPM (`TCGA-PAAD.star_tpm.tsv.gz`)
- Survival: cBioPortal Pan-Cancer Atlas (`paad_tcga_pan_can_atlas_2018`)

**Gene panel (19 genes):** `GATA6, KRT17, KRT7, CDK1, CCNB1, CDK4, MKI67, TOP2A, SMAD4, TGFB1, CDKN2A, VIM, CDH2, ACTA2, FAP, CD8A, FOXP3, LDHA, SLC2A1`

**Script:** `data/build_tcga_paad.py` → `data/paad_survival.csv`
**SLURM:** In `scripts/hpc_new_diseases.sbatch` as `paad_survival` experiment
**Results go to:** `results/track_a_task_landscape/paad_survival/`

**Pre-registered prediction:** `GATA6 − VIM` or `SMAD4 × CCNB1` compound AUROC ≥ 0.68, delta_baseline ≥ 0.05 over GATA6 alone. Failure mode: subtype signal (GATA6 alone already ~0.65) dominates, no compound advantage.

---

### Experiment 4: DIPG OpenPedCan — PRIORITY 4 (Largest potential, most compute)

**Why high potential:**
- H3K27M is universal → useless within-mutant stratification.
- OPC-AC metabolic axis (cholesterol/OXPHOS) = mechanistically validated new dimension.
- ID1 + ID2 ACVR1→BMP axis confirmed in GSE125627 (prior work, log2FC +2.94/+1.63).
- If `OLIG2 − UQCRC1` survives → clinically actionable (OPC-like = statin-sensitive).

**Data:** OpenPedCan v15 public S3, ~220 DMG-H3K27M, OS median ~10 months
- Primary: `s3://d3b-openaccess-us-east-1-prd-pbta/open-targets/v15/` (no auth)
- Fallback: GEO GSE115397 (42 samples) or GSE101108 (34 samples)

**Gene panel (23 genes):** `OLIG2, SOX10, PDGFRA, HMGCR, LDLR, SQLE, CD44, VIM, GFAP, ID1, ID2, ID3, UQCRC1, COX4I1, NDUFB8, EZH2, SUZ12, CDK4, CDK6, CCND1, CDKN2A, MKI67, TOP2A`

**Script:** `data/build_dipg_openpecan.py` → `data/dipg_openpecan.csv`
**SLURM:** In `scripts/hpc_new_diseases.sbatch` as `dipg` experiment
**Results go to:** `results/track_a_task_landscape/dipg/`

**Note on data access:** OpenPedCan FPKM matrix is ~4GB. If the auto-download fails (S3 connectivity), use the GEO fallback or download manually:
```bash
aws s3 cp s3://d3b-openaccess-us-east-1-prd-pbta/open-targets/v15/ . \
  --recursive --no-sign-request \
  --include "*.tsv.gz" --include "histologies.tsv"
```

**Gate caveat:** n=220 is adequate but bootstrap CI lower threshold (0.60) may be tight if AUROC signal is modest. If ci_lower fails, check if ACVR1 co-mutation status is available as a covariate (would strengthen the delta_confound test).

---

### BONUS: G5 Unseeded PySR on KIRC (Already scripted)

**Why:** Proves TOP2A−EPAS1 emerges from data alone (no Opus seeding).
**Script:** `src/g5_pysr_fraction_zero.py` (already exists)
**Prerequisite:** Julia must be pre-warmed (`interactive_julia_compile.sh` on login node first)
**Expected:** HIGH confidence TOP2A/EPAS1 axis re-emerges (AUROC gradient is strong at +0.069).

---

## HPC Setup Instructions

### 1. Sync new data build scripts to HPC
```bash
rsync -avz \
  data/build_lihc_mvi.py \
  data/build_ipf_bal.py \
  data/build_tcga_paad.py \
  data/build_dipg_openpecan.py \
  [HPC_LOGIN_NODE]:${HPC_PROJECT_DIR}/data_driven_discovery/data/

rsync -avz \
  scripts/hpc_new_diseases.sbatch \
  [HPC_LOGIN_NODE]:${HPC_PROJECT_DIR}/data_driven_discovery/scripts/
```

### 2. Submit the job
```bash
ssh [HPC_LOGIN_NODE]
cd ${HPC_PROJECT_DIR}/data_driven_discovery
sbatch scripts/hpc_new_diseases.sbatch
```

### 3. Monitor
```bash
squeue -u $USER
tail -f logs/lacuna_falsification_<JOBID>.out
```

### 4. Sync results back
```bash
rsync -avz \
  [HPC_LOGIN_NODE]:${HPC_PROJECT_DIR}/data_driven_discovery/results/track_a_task_landscape/ \
  ./results/track_a_task_landscape/ \
  --include="*.json" --include="*.log" --include="SUMMARY*" \
  --include="*/" --exclude="*"
```

---

## Analysis Pipeline (after results land)

For each experiment that has survivors, run:

```bash
# 1. Check what survived
python3 -c "
import json, glob
for f in glob.glob('results/track_a_task_landscape/*/falsification_report.json'):
    data = json.load(open(f))
    if isinstance(data, list):
        s = [r for r in data if r.get('passes')]
        print(f'{f}: {len(data)} candidates, {len(s)} survivors')
"

# 2. Get Opus interpretation of survivors (requires API key)
python3 src/falsification_sweep.py --interpret-survivors \
    --report results/track_a_task_landscape/lihc_mvi/falsification_report.json

# 3. Cross-disease summary
python3 src/plot_track_a.py  # updates results/track_a_task_landscape/SUMMARY.md
```

---

## Key Scientific Hypotheses (pre-registered before running)

| Disease | Hypothesis | Pre-registered form |
|---------|-----------|---------------------|
| LIHC-MVI | Stemness × proliferation compound | `EPCAM + CDK1` or `EPCAM − TOP2A` |
| IPF-BAL | Fibrotic macrophage minus epithelial | `SPP1 − CCL20` or `CTHRC1 − AGER` |
| PAAD | Classical subtype over proliferation | `GATA6/(CDK1+ε)` or `GATA6 − VIM` |
| DIPG | OPC metabolic minus OXPHOS | `OLIG2 − UQCRC1` or `ID1 + ID2 − COX4I1` |

---

## What to Report (Honest Outcomes)

| Outcome | How to report |
|---------|--------------|
| Survivor with Δbase ≥ 0.05 | "New compact law discovered; Opus interpretation to follow" |
| 0 survivors, single-gene saturates | "Task confirmed biology-saturated by single gene; compound search ruled out" |
| 0 survivors, ci_lower fails | "Signal present but insufficient n for bootstrap confidence; document n and CI" |
| IPF metadata parsing fails | "GEO metadata non-standard; document what characteristics_ch1 contains; reformat manually" |
| DIPG S3 access fails | "OpenPedCan S3 unreachable; GEO fallback GSE115397 n=42 attempted" |

---

## Overlap Check (Confirmed clean as of 2026-04-26 13:00)

- **Currently running job 2812300 (`lsib-open-data-downstream`)**: Unrelated project, different directories
- **All Lacuna SLURM jobs** last ran April 22-23 (job 2812758). All COMPLETED.
- **New job** targets new result directories: `lihc_mvi/`, `ipf_lgrc/`, `paad_survival/`, `dipg/`
- **No file conflicts** with existing: `lihc/` (different task), `coad_msi/`, `gbm_idh/`, etc.
- **g5 bonus**: writes to `g5_fraction_zero/fraction_zero_comparison.json` (idempotent overwrite)

---

## Background Science (Reference)

| Finding | Source |
|---------|--------|
| TOP2A−EPAS1 = ccA/ccB axis | Brannon 2010 PMID:20871783 |
| COAD SLC2A1+PD-L2 in advanced stage | TCGA COAD analysis (this repo, Apr 26) |
| LGG TWIST1×MKI67 grade compound | TCGA LGG analysis (this repo, Apr 26) |
| LIHC MVI — AFP insufficient (AUC 0.61) | PMC8675478 |
| IPF SPP1/CCL20 in BAL | PMC10941445 |
| PAAD GATA6 classical subtype | PMID 37823514 |
| DIPG OPC/AC axis | Nat Comm 2024 (s41467-024-52973-4) |
| DIPG ID1/ID2 ACVR1→BMP confirmed | GSE125627 (this repo, prior work) |
| LLM-SR seeded vs unseeded 257× improvement | arXiv 2404.18400 (ICLR 2025 Oral) |
