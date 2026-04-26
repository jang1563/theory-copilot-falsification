# Lacuna — Long-Horizon HPC Discovery Session
**Purpose:** Run the full Lacuna falsification pipeline across as many datasets and
diseases as possible in one continuous session. Each experiment completes and
immediately seeds the next. This session should run until explicitly stopped.

**Repo:** `lacuna-falsification/`  
**Commit prefix:** `[F]` for all commits in this session  
**Gate:** pre-registered, do NOT modify `src/lacuna/falsification.py`

---

## What this session is building

The central submission claim is:

> "Lacuna applies identical pre-registered falsification thresholds to any
> disease dataset. It finds compound survivors when the biology requires
> multi-gene measurement, and correctly refuses when a single gene dominates."

To make this claim maximal, this session runs the pipeline on every viable
TCGA cancer and task combination, building a cross-task matrix:

| Status | Cancer | Task | Panel | Result |
|---|---|---|---|---|
| ✅ DONE | KIRC | Tumor vs Normal | 11-gene | 0/33 (CA9 saturates) |
| ✅ DONE | KIRC | Stage I-II vs III-IV | 11-gene | 0/34 (CUBN ceiling) |
| ✅ DONE | KIRC | 5-yr Survival | 11-gene | 0/36 (CUBN ceiling) |
| ✅ DONE | KIRC | Metastasis M0 vs M1 | 45-gene | **9/30 SURVIVORS** |
| ✅ DONE | LUAD | Tumor vs Normal | 23-gene | 0/4 (SFTPC=0.998) |
| ✅ DONE | BRCA | Tumor vs Normal | 31-gene | 0/7 (single-gene ceiling) |
| ✅ DONE | ccRCC | Metastasis (CPTAC-3, external) | 2-gene | FAIL (power n_M1=20) |
| ✅ DONE | ccRCC | PFS survival (IMmotion150) | 2-gene | PASS (3/3 pre-reg) |
| 🔲 TODO | KIRC | Stage I-II vs III-IV | **45-gene** | ← Track A |
| 🔲 TODO | STAD | Metastasis M0 vs M1 | 35-gene | ← Track B |
| 🔲 TODO | BRCA | PAM50 LumA vs Basal | 35-gene | ← Track C |
| 🔲 TODO | LIHC | Tumor vs Normal | 30-gene | ← Track D |
| 🔲 TODO | COAD | MSI vs MSS | 30-gene | ← Track E |
| 🔲 TODO | PRAD | Gleason high vs low | 25-gene | ← Track F |
| 🔲 TODO | THCA | Papillary vs Follicular | 25-gene | ← Track G |
| 🔲 TODO | KIRC | Metastasis — new Opus families | 45-gene | ← Track H |
| 🔲 TODO | LGG | IDH-mutant vs IDH-wt | 30-gene | ← Track I |

At session end, every row gets a result (survivors / gate verdict / honest caveat).
The cross-task matrix is the deliverable.

---

## Setup (run once at session start)

```bash
cd /path/to/lacuna-falsification   # adjust to your HPC path
source .venv/bin/activate

# Verify gate
python -c "from lacuna.falsification import passes_falsification; print('gate OK')"

# Verify Opus API + confirm propose_laws signature
python -c "
import sys; sys.path.insert(0,'src')
from lacuna.opus_client import OpusClient
import inspect
c = OpusClient()
print('Opus client OK')
print('propose_laws sig:', inspect.signature(c.propose_laws))
"

# Create all result directories
mkdir -p results/track_a_task_landscape/{stage_expanded,stad_metastasis,brca_pam50,lihc,coad_msi,prad_gleason,thca_histology,kirc_metastasis_v2,gbm_idh}

# Check cached downloads
ls .tmp_geo/gdc/*.tsv.gz 2>/dev/null | xargs -I{} basename {} 2>/dev/null
```

> **API signature note (verified from source):**
> `OpusClient.propose_laws(dataset_card, features, context="")`
>
> `falsification_sweep.py` gate args:
> `--n-permutations N  --n-resamples N  --n-decoys N`
>
> Both verified from `src/lacuna/opus_client.py` and `src/falsification_sweep.py`.
> Do NOT use `--n-perm`, `--n-boot`, `--n-decoy` — those do not exist.

---

## Session loop — run each track in sequence

### TRACK A — KIRC Stage I-II vs III-IV (45-gene panel)
**Why first:** data is already built, lowest friction, ~50% chance of finding survivors.  
**Hypothesis:** proliferation markers (TOP2A, MKI67) added by the 45-gene panel may let the
compound law clear `delta_baseline > 0.05` where the 11-gene panel (CUBN=0.610 ceiling) failed.

```bash
# Step 1: Verify stage CSV exists
python -c "
import pandas as pd
df = pd.read_csv('data/kirc_stage.csv')
print(df.label.value_counts())
print(f'n={len(df)}, genes available:', [c for c in df.columns if c not in {'sample_id','label','stage'}][:5])
"
# If FileNotFoundError: python data/build_tcga_kirc_stage.py
```

**Save as `run_track_a_proposer.py` and run:**
```python
import json, sys
sys.path.insert(0, 'src')
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()

# 45-gene panel — same as kirc_metastasis_expanded (verified: no duplicates)
genes_45 = [
    "CA9","VEGFA","LDHA","NDUFA4L2","SLC2A1","ENO2","AGXT","ALB","CUBN",
    "PTGER3","SLC12A3","ACTB","GAPDH","RPL13A","MKI67","TOP2A","EPAS1",
    "CDK1","CCNB1","PCNA","MCM2","ANGPTL4","BHLHE40","DDIT4","PGK1",
    "HK2","PKM","ALDOA","VIM","FN1","CDH2","TWIST1","SNAI1",
    "ZEB1","MMP2","MMP9","LRP2","SLC22A8","PLIN2","AQP1","UMOD",
    "HAVCR1","ATP6AP2",
]

df = pd.read_csv("data/kirc_stage.csv")
n_pos = int((df.label == "disease").sum())
n_neg = int((df.label == "control").sum())

dataset_card = {
    "cohort": "TCGA-KIRC",
    "task": "Stage I-II (control) vs Stage III-IV (disease)",
    "n_samples": len(df), "n_positive": n_pos, "n_negative": n_neg,
    "panel": "45-gene HIF/proliferation/tubule/EMT/housekeeping",
    "known_11gene_ceiling": "CUBN=0.610 (tubule-loss marker) — 0/34 survivors on 11-gene panel",
    "existing_metastasis_survivors": ["TOP2A - EPAS1 (AUROC 0.726)", "MKI67 - EPAS1 (AUROC 0.708)"],
}

context = (
    "Advanced-stage KIRC (III-IV) shows: higher tumor bulk/invasion, "
    "sarcomatoid dedifferentiation, elevated proliferation index (TOP2A/MKI67). "
    "Stage I-II ~ ccA (HIF-2alpha-driven, well-differentiated). "
    "Stage III-IV ~ ccB (proliferating, losing HIF-2alpha dominance). "
    "Propose 5 law families. Include at least one negative control "
    "(housekeeping gene contrast that should fail). "
    "For each family include: initial_guess (gene-name equation), "
    "expected_behavior, and the skeptic_test that would kill it before fitting."
)

result = c.propose_laws(dataset_card=dataset_card, features=genes_45, context=context)
with open("results/track_a_task_landscape/stage_expanded/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("Proposals saved. Families:", len(result.get("families", [])))
print(json.dumps(result.get("families", [])[:2], indent=2))
```

```bash
python run_track_a_proposer.py

# PySR sweep
python src/pysr_sweep.py \
  --data data/kirc_stage.csv \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3,ACTB,GAPDH,RPL13A,MKI67,TOP2A,EPAS1,CDK1,CCNB1,PCNA,MCM2,ANGPTL4,BHLHE40,DDIT4,PGK1,HK2,PKM,ALDOA,VIM,FN1,CDH2,TWIST1,SNAI1,ZEB1,MMP2,MMP9,LRP2,SLC22A8,PLIN2,AQP1,UMOD,HAVCR1,ATP6AP2 \
  --proposals results/track_a_task_landscape/stage_expanded/opus_proposals.json \
  --n-populations 30 --population-size 50 --iterations 2000 --maxsize 20 \
  --seeds 1 7 13 42 123 --n-jobs 8 \
  --output results/track_a_task_landscape/stage_expanded/pysr_candidates.json

# Gate  (correct arg names: --n-permutations, --n-resamples, --n-decoys)
python src/falsification_sweep.py \
  --data data/kirc_stage.csv \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3,ACTB,GAPDH,RPL13A,MKI67,TOP2A,EPAS1,CDK1,CCNB1,PCNA,MCM2,ANGPTL4,BHLHE40,DDIT4,PGK1,HK2,PKM,ALDOA,VIM,FN1,CDH2,TWIST1,SNAI1,ZEB1,MMP2,MMP9,LRP2,SLC22A8,PLIN2,AQP1,UMOD,HAVCR1,ATP6AP2 \
  --candidates results/track_a_task_landscape/stage_expanded/pysr_candidates.json \
  --output results/track_a_task_landscape/stage_expanded/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK B — STAD Gastric Metastasis M0 vs M1

**Hypothesis:** Diffuse-type STAD (CDH1-low, MKI67-high) creates a `MKI67 - CDH1` law
analogous to `TOP2A - EPAS1` in KIRC. Power warning: n_M1 ≈ 30 → ci_lower gate may fail.

```bash
python3 << 'PYEOF'
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd

TMP = Path(".tmp_geo/gdc"); TMP.mkdir(parents=True, exist_ok=True)
EXPR_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-STAD.star_tpm.tsv.gz"
CLIN_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-STAD.clinical.tsv.gz"
expr_p = TMP / "TCGA-STAD.star_tpm.tsv.gz"
clin_p = TMP / "TCGA-STAD.clinical.tsv.gz"
if not expr_p.exists(): urllib.request.urlretrieve(EXPR_URL, expr_p); print("expr downloaded")
if not clin_p.exists(): urllib.request.urlretrieve(CLIN_URL, clin_p); print("clin downloaded")

GENES = {
    "CDH1":"ENSG00000039068","MUC5AC":"ENSG00000215182","CDX2":"ENSG00000165556",
    "CLDN18":"ENSG00000066405","EPCAM":"ENSG00000119888","VIM":"ENSG00000026025",
    "FN1":"ENSG00000115414","TWIST1":"ENSG00000122691","SNAI1":"ENSG00000124216",
    "CDH2":"ENSG00000170558","MKI67":"ENSG00000148773","TOP2A":"ENSG00000131747",
    "CDK1":"ENSG00000170312","CCNB1":"ENSG00000134057","PCNA":"ENSG00000132646",
    "MCM2":"ENSG00000073111","EPAS1":"ENSG00000116016","VEGFA":"ENSG00000112715",
    "CA9":"ENSG00000107159","SLC2A1":"ENSG00000117394","LDHA":"ENSG00000134333",
    "HK2":"ENSG00000159399","ANGPTL4":"ENSG00000167772",
    "ERBB2":"ENSG00000141736","FGFR2":"ENSG00000066468","KRAS":"ENSG00000133703",
    "TP53":"ENSG00000141510","ARID1A":"ENSG00000117713","RHOA":"ENSG00000067560",
    "MMP2":"ENSG00000087245","MMP9":"ENSG00000100985","MMP7":"ENSG00000000971",
    "ACTB":"ENSG00000075624","GAPDH":"ENSG00000111640","RPL13A":"ENSG00000142541",
}
ensembl_map = {v: k for k, v in GENES.items()}

expr = pd.read_csv(expr_p, sep="\t", index_col=0, compression="gzip")
idx_clean = expr.index.str.replace(r"\.\d+$", "", regex=True)
mask = idx_clean.isin(ensembl_map)
expr_sub = expr.loc[mask].copy()
expr_sub.index = idx_clean[mask].map(ensembl_map)
expr_sub = expr_sub.T
expr_sub = np.log1p(expr_sub + 0.001)
expr_sub.index.name = "sample_id"

clin = pd.read_csv(clin_p, sep="\t", low_memory=False)
m_col = next((c for c in clin.columns if "pathologic_m" in c.lower()), None)
if m_col is None:
    raise RuntimeError(f"M-stage column not found. Columns: {list(clin.columns[:20])}")
s_col = "sample" if "sample" in clin.columns else clin.columns[0]
m_df = clin[[s_col, m_col]].dropna(); m_df.columns = ["sample_id", "m_stage"]
m_df["label"] = m_df.m_stage.map(
    lambda v: "disease" if str(v).upper().startswith("M1") else ("control" if str(v).upper() == "M0" else None)
)
m_df = m_df.dropna(subset=["label"])
print("STAD M distribution:", m_df.m_stage.value_counts().to_dict())

tumor = expr_sub[expr_sub.index.str[13:15].isin(["01", "02", "06"])].copy()
tumor.index = tumor.index.str[:15]
m_df["sample_id"] = m_df.sample_id.str[:15]
merged = tumor.join(m_df.set_index("sample_id")[["label", "m_stage"]], how="inner").dropna(subset=["label"])
gene_cols = [c for c in merged.columns if c not in {"label", "m_stage"}]
out = merged[["label", "m_stage"] + gene_cols].reset_index()
out.insert(0, "sample_id", out.pop("sample_id"))
out.to_csv("data/stad_metastasis.csv", index=False)
n1 = (out.label == "disease").sum(); n0 = (out.label == "control").sum()
print(f"Saved data/stad_metastasis.csv: n={len(out)} M1={n1} M0={n0}")
if n1 < 25:
    print("WARNING: n_M1 very low — gate will likely fail on ci_lower (power limitation, honest negative)")
PYEOF
```

> **Note on heredoc:** Using `<< 'PYEOF'` (single-quoted) prevents bash from expanding `$` inside the Python code. This is the safe pattern for multi-line Python in bash.

**Proposer:**
```python
# run_track_b_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()
df = pd.read_csv("data/stad_metastasis.csv")
n1 = int((df.label == "disease").sum()); n0 = int((df.label == "control").sum())

dataset_card = {
    "cohort": "TCGA-STAD", "task": "M0 (control) vs M1 (disease) gastric metastasis",
    "n_positive": n1, "n_negative": n0,
    "panel": "35-gene Lauren/proliferation/HIF/EMT/oncogene",
}
context = (
    "Diffuse-type STAD: CDH1-low, RHOA-mutant, MKI67-high -> peritoneal spread (M1). "
    "Intestinal-type STAD: CDX2-high, CLDN18-high, lower M1. "
    "Expected law: MKI67 - CDH1 or TOP2A - CDH1 (proliferation vs E-cadherin). "
    "This is the ccA/ccB analog for gastric cancer. "
    "HONEST CAVEAT: n_M1 may be ~30, power may be marginal for ci_lower > 0.60. "
    "Propose 5 law families. Include at least one negative control. "
    "For each: initial_guess (equation string), expected_behavior, skeptic_test."
)
genes = ["CDH1","MUC5AC","CDX2","CLDN18","EPCAM","VIM","FN1","TWIST1","SNAI1","CDH2",
         "MKI67","TOP2A","CDK1","CCNB1","PCNA","MCM2","EPAS1","VEGFA","CA9","SLC2A1",
         "LDHA","HK2","ANGPTL4","ERBB2","FGFR2","KRAS","TP53","ARID1A","RHOA",
         "MMP2","MMP9","MMP7","ACTB","GAPDH","RPL13A"]

result = c.propose_laws(dataset_card=dataset_card, features=genes, context=context)
with open("results/track_a_task_landscape/stad_metastasis/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("STAD proposals saved. Families:", len(result.get("families", [])))
```

```bash
python run_track_b_proposer.py

python src/pysr_sweep.py \
  --data data/stad_metastasis.csv \
  --genes CDH1,MUC5AC,CDX2,CLDN18,EPCAM,VIM,FN1,TWIST1,SNAI1,CDH2,MKI67,TOP2A,CDK1,CCNB1,PCNA,MCM2,EPAS1,VEGFA,CA9,SLC2A1,LDHA,HK2,ANGPTL4,ERBB2,FGFR2,KRAS,TP53,ARID1A,RHOA,MMP2,MMP9,MMP7,ACTB,GAPDH,RPL13A \
  --proposals results/track_a_task_landscape/stad_metastasis/opus_proposals.json \
  --n-populations 20 --population-size 50 --iterations 2000 --maxsize 12 \
  --seeds 1 7 13 42 123 --n-jobs 8 \
  --output results/track_a_task_landscape/stad_metastasis/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/stad_metastasis.csv \
  --genes CDH1,MUC5AC,CDX2,CLDN18,EPCAM,VIM,FN1,TWIST1,SNAI1,CDH2,MKI67,TOP2A,CDK1,CCNB1,PCNA,MCM2,EPAS1,VEGFA,CA9,SLC2A1,LDHA,HK2,ANGPTL4,ERBB2,FGFR2,KRAS,TP53,ARID1A,RHOA,MMP2,MMP9,MMP7,ACTB,GAPDH,RPL13A \
  --candidates results/track_a_task_landscape/stad_metastasis/pysr_candidates.json \
  --output results/track_a_task_landscape/stad_metastasis/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK C — BRCA PAM50 (Luminal A vs Basal-like)

**Hypothesis:** `MKI67 - ESR1` is the breast cancer ccA/ccB analog — but ESR1 alone may
achieve AUROC > 0.95, saturating the task. The gate will report honestly either way.

> **PAM50 column note:** In GDC-Xena, TCGA-BRCA PAM50 is usually in `paper_BRCA_Subtype_PAM50`
> inside the clinical TSV. If not found, check the phenotype TSV separately.

```bash
python3 << 'PYEOF'
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

TMP = Path(".tmp_geo/gdc"); TMP.mkdir(parents=True, exist_ok=True)
EXPR_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-BRCA.star_tpm.tsv.gz"
CLIN_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-BRCA.clinical.tsv.gz"
expr_p = TMP / "TCGA-BRCA.star_tpm.tsv.gz"
clin_p = TMP / "TCGA-BRCA.clinical.tsv.gz"
if not expr_p.exists(): urllib.request.urlretrieve(EXPR_URL, expr_p); print("expr downloaded")
if not clin_p.exists(): urllib.request.urlretrieve(CLIN_URL, clin_p); print("clin downloaded")

GENES = {
    "ESR1":"ENSG00000091831","PGR":"ENSG00000082175","FOXA1":"ENSG00000129514",
    "GATA3":"ENSG00000107485","XBP1":"ENSG00000100219","TFF1":"ENSG00000160182",
    "ERBB2":"ENSG00000141736","GRB7":"ENSG00000141738","EGFR":"ENSG00000146648",
    "KRT5":"ENSG00000186081","KRT14":"ENSG00000186555","KRT17":"ENSG00000128422",
    "KRT6A":"ENSG00000171401","LAMC2":"ENSG00000058085",
    "MKI67":"ENSG00000148773","TOP2A":"ENSG00000131747","CDK1":"ENSG00000170312",
    "CCNB1":"ENSG00000134057","PCNA":"ENSG00000132646","MCM2":"ENSG00000073111",
    "BIRC5":"ENSG00000089685","UBE2C":"ENSG00000175063","CCNE1":"ENSG00000105173",
    "MLPH":"ENSG00000109814","BCL2":"ENSG00000171791","SLC39A6":"ENSG00000141458",
    "VIM":"ENSG00000026025","FN1":"ENSG00000115414","CDH1":"ENSG00000039068",
    "VEGFA":"ENSG00000112715","EPAS1":"ENSG00000116016",
    "ACTB":"ENSG00000075624","GAPDH":"ENSG00000111640","RPL13A":"ENSG00000142541",
}
ensembl_map = {v: k for k, v in GENES.items()}

expr = pd.read_csv(expr_p, sep="\t", index_col=0, compression="gzip")
idx_clean = expr.index.str.replace(r"\.\d+$", "", regex=True)
mask = idx_clean.isin(ensembl_map)
expr_sub = expr.loc[mask].copy()
expr_sub.index = idx_clean[mask].map(ensembl_map)
expr_sub = expr_sub.T
expr_sub = np.log1p(expr_sub + 0.001)
expr_sub.index.name = "sample_id"

clin = pd.read_csv(clin_p, sep="\t", low_memory=False)
# Try known column names in priority order
pam50_col = None
for candidate in ["paper_BRCA_Subtype_PAM50", "PAM50", "pam50_call_from_pam50centroid",
                   "BRCA_Subtype_PAM50"]:
    if candidate in clin.columns:
        pam50_col = candidate; break
if pam50_col is None:
    pam50_col = next((c for c in clin.columns if "pam50" in c.lower()), None)
if pam50_col is None:
    print("PAM50 column not found. Available columns with 'subtype' or 'paper':")
    print([c for c in clin.columns if "subtype" in c.lower() or "paper" in c.lower()][:15])
    raise SystemExit("Hardcode pam50_col from the list above and re-run.")
print(f"PAM50 column: {pam50_col!r}")
print(clin[pam50_col].value_counts().to_dict())

s_col = "sample" if "sample" in clin.columns else clin.columns[0]
pam_df = clin[[s_col, pam50_col]].dropna(); pam_df.columns = ["sample_id", "pam50"]

def _label(v):
    v = str(v).strip()
    if v in ("LumA", "Luminal A", "LuminalA"): return "control"
    if v in ("Basal", "Basal-like", "BasalLike", "Basal-Like"): return "disease"
    return None  # exclude LumB, HER2, Normal-like

pam_df["label"] = pam_df.pam50.map(_label)
pam_df = pam_df.dropna(subset=["label"])
print(f"LumA(control)={(pam_df.label=='control').sum()}  Basal(disease)={(pam_df.label=='disease').sum()}")

tumor = expr_sub[expr_sub.index.str[13:15].isin(["01"])].copy()
tumor.index = tumor.index.str[:15]
pam_df["sample_id"] = pam_df.sample_id.str[:15]
merged = tumor.join(pam_df.set_index("sample_id")[["label","pam50"]], how="inner").dropna(subset=["label"])
gene_cols = [c for c in merged.columns if c not in {"label", "pam50"}]
out = merged[["label", "pam50"] + gene_cols].reset_index()
out.insert(0, "sample_id", out.pop("sample_id"))
out.to_csv("data/brca_pam50.csv", index=False)
print(f"Saved data/brca_pam50.csv: n={len(out)}")

# Single-gene ceiling check — if ESR1 > 0.95, task is saturated
y = (out.label == "disease").astype(int).values
for g in ["ESR1", "MKI67", "KRT5", "TOP2A", "FOXA1", "PGR", "KRT14"]:
    if g in out.columns:
        auc = roc_auc_score(y, out[g].values)
        print(f"  {g}: sign-inv AUROC = {max(auc, 1-auc):.4f}")
print("If ESR1 > 0.95 → task is saturated; gate will refuse with delta_baseline fail (honest result).")
PYEOF
```

**Proposer:**
```python
# run_track_c_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()
df = pd.read_csv("data/brca_pam50.csv")
n1 = int((df.label == "disease").sum()); n0 = int((df.label == "control").sum())

dataset_card = {
    "cohort": "TCGA-BRCA", "task": "PAM50 Luminal A (control) vs Basal-like (disease)",
    "n_positive": n1, "n_negative": n0,
    "panel": "35-gene PAM50-core/proliferation/basal/housekeeping",
}
context = (
    "Direct breast cancer analog of KIRC ccA/ccB axis. "
    "Luminal A = ESR1-high, PGR-high, low proliferation (ccA analog). "
    "Basal-like = KRT5/KRT14-high, MKI67-high, ESR1-low (ccB analog). "
    "Expected law: MKI67 - ESR1 or TOP2A - ESR1 (proliferation vs luminal anchor). "
    "HONEST caveat: ESR1 alone may achieve AUROC > 0.95, saturating the task. "
    "If so, delta_baseline > 0.05 is impossible — same as KIRC tumor-vs-normal (CA9=0.965). "
    "Propose 5 law families. Include at least one negative control. "
    "For each: initial_guess, expected_behavior, skeptic_test."
)
genes = ["ESR1","PGR","FOXA1","GATA3","XBP1","TFF1","ERBB2","GRB7","EGFR",
         "KRT5","KRT14","KRT17","KRT6A","LAMC2","MKI67","TOP2A","CDK1","CCNB1",
         "PCNA","MCM2","BIRC5","UBE2C","CCNE1","MLPH","BCL2","SLC39A6",
         "VIM","FN1","CDH1","VEGFA","EPAS1","ACTB","GAPDH","RPL13A"]

result = c.propose_laws(dataset_card=dataset_card, features=genes, context=context)
with open("results/track_a_task_landscape/brca_pam50/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("BRCA-PAM50 proposals saved. Families:", len(result.get("families", [])))
```

```bash
python run_track_c_proposer.py

python src/pysr_sweep.py \
  --data data/brca_pam50.csv \
  --genes ESR1,PGR,FOXA1,GATA3,XBP1,TFF1,ERBB2,GRB7,EGFR,KRT5,KRT14,KRT17,KRT6A,LAMC2,MKI67,TOP2A,CDK1,CCNB1,PCNA,MCM2,BIRC5,UBE2C,CCNE1,MLPH,BCL2,SLC39A6,VIM,FN1,CDH1,VEGFA,EPAS1,ACTB,GAPDH,RPL13A \
  --proposals results/track_a_task_landscape/brca_pam50/opus_proposals.json \
  --n-populations 20 --population-size 50 --iterations 1500 --maxsize 15 \
  --seeds 1 7 42 --n-jobs 8 \
  --output results/track_a_task_landscape/brca_pam50/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/brca_pam50.csv \
  --genes ESR1,PGR,FOXA1,GATA3,XBP1,TFF1,ERBB2,GRB7,EGFR,KRT5,KRT14,KRT17,KRT6A,LAMC2,MKI67,TOP2A,CDK1,CCNB1,PCNA,MCM2,BIRC5,UBE2C,CCNE1,MLPH,BCL2,SLC39A6,VIM,FN1,CDH1,VEGFA,EPAS1,ACTB,GAPDH,RPL13A \
  --candidates results/track_a_task_landscape/brca_pam50/pysr_candidates.json \
  --output results/track_a_task_landscape/brca_pam50/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK D — LIHC (Liver) Tumor vs Normal

Liver has multiple normal-tissue markers (ALB, APOA1, TTR) — unlike KIRC/LUAD where
one gene (CA9/SFTPC) dominates, LIHC single-gene ceiling may be lower, giving compound
laws a real chance.

```bash
python3 << 'PYEOF'
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

TMP = Path(".tmp_geo/gdc"); TMP.mkdir(parents=True, exist_ok=True)
EXPR_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-LIHC.star_tpm.tsv.gz"
expr_p = TMP / "TCGA-LIHC.star_tpm.tsv.gz"
if not expr_p.exists(): urllib.request.urlretrieve(EXPR_URL, expr_p); print("LIHC expr downloaded")

GENES = {
    "ALB":"ENSG00000163631","APOA1":"ENSG00000118137","APOB":"ENSG00000084674",
    "TTR":"ENSG00000118271","TF":"ENSG00000091513","GPC3":"ENSG00000081564",
    "AFP":"ENSG00000081051","AHSG":"ENSG00000145414","FGA":"ENSG00000171560",
    "MYC":"ENSG00000136997","CCND1":"ENSG00000110092","CDK4":"ENSG00000135446",
    "VEGFA":"ENSG00000112715","MKI67":"ENSG00000148773","TOP2A":"ENSG00000131747",
    "CDK1":"ENSG00000170312","PCNA":"ENSG00000132646",
    "LDHA":"ENSG00000134333","SLC2A1":"ENSG00000117394","HK2":"ENSG00000159399",
    "TP53":"ENSG00000141510","CTNNB1":"ENSG00000168036",
    "EPAS1":"ENSG00000116016","CA9":"ENSG00000107159","NDUFA4L2":"ENSG00000185633",
    "VIM":"ENSG00000026025","FN1":"ENSG00000115414","CDH1":"ENSG00000039068",
    "ACTB":"ENSG00000075624","GAPDH":"ENSG00000111640","RPL13A":"ENSG00000142541",
}
ensembl_map = {v: k for k, v in GENES.items()}

expr = pd.read_csv(expr_p, sep="\t", index_col=0, compression="gzip")
idx_clean = expr.index.str.replace(r"\.\d+$", "", regex=True)
mask = idx_clean.isin(ensembl_map)
expr_sub = expr.loc[mask].copy()
expr_sub.index = idx_clean[mask].map(ensembl_map)
expr_sub = expr_sub.T
expr_sub = np.log1p(expr_sub + 0.001)
expr_sub.index.name = "sample_id"

tumor_mask = expr_sub.index.str[13:15].isin(["01", "02", "06"])
normal_mask = expr_sub.index.str[13:15].isin(["11"])
df_t = expr_sub[tumor_mask].copy(); df_t["label"] = "disease"
df_n = expr_sub[normal_mask].copy(); df_n["label"] = "control"
out = pd.concat([df_t, df_n]).reset_index()
out.insert(0, "sample_id", out.pop("sample_id"))
out.to_csv("data/lihc_tumor_normal.csv", index=False)
n_t = (out.label == "disease").sum(); n_n = (out.label == "control").sum()
print(f"LIHC n={len(out)} tumor={n_t} normal={n_n}")

# Single-gene ceiling
y = (out.label == "disease").astype(int).values
for g in ["ALB", "AFP", "GPC3", "MKI67", "TOP2A", "EPAS1", "TTR"]:
    if g in out.columns:
        auc = roc_auc_score(y, out[g].values)
        print(f"  {g}: sign-inv AUROC = {max(auc, 1-auc):.4f}")
PYEOF

mkdir -p results/track_a_task_landscape/lihc/
```

**Proposer:**
```python
# run_track_d_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()
df = pd.read_csv("data/lihc_tumor_normal.csv")

dataset_card = {
    "cohort": "TCGA-LIHC", "task": "Tumor vs Normal hepatocellular carcinoma",
    "n_samples": len(df), "n_positive": int((df.label=="disease").sum()),
}
context = (
    "HCC biology: Warburg metabolism (HK2/LDHA high in tumor), "
    "loss of hepatocyte differentiation markers (ALB/APOA1/TTR low in tumor), "
    "GPC3 oncofetal antigen (high in HCC), MYC amplification, VEGFA hypoxia. "
    "IMPORTANT: liver has MULTIPLE normal-tissue markers — single-gene ceiling may be "
    "lower than KIRC/LUAD, so compound laws have a better chance. "
    "Expected: MKI67 + HK2 - ALB or GPC3 - TTR. "
    "Propose 5 law families. Include at least one negative control. "
    "For each: initial_guess, expected_behavior, skeptic_test."
)
genes = ["ALB","APOA1","APOB","TTR","TF","GPC3","AFP","AHSG","FGA",
         "MYC","CCND1","CDK4","VEGFA","MKI67","TOP2A","CDK1","PCNA",
         "LDHA","SLC2A1","HK2","TP53","CTNNB1",
         "EPAS1","CA9","NDUFA4L2","VIM","FN1","CDH1","ACTB","GAPDH","RPL13A"]

result = c.propose_laws(dataset_card=dataset_card, features=genes, context=context)
with open("results/track_a_task_landscape/lihc/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("LIHC proposals saved. Families:", len(result.get("families", [])))
```

```bash
python run_track_d_proposer.py

python src/pysr_sweep.py \
  --data data/lihc_tumor_normal.csv \
  --genes ALB,APOA1,APOB,TTR,TF,GPC3,AFP,AHSG,FGA,MYC,CCND1,CDK4,VEGFA,MKI67,TOP2A,CDK1,PCNA,LDHA,SLC2A1,HK2,TP53,CTNNB1,EPAS1,CA9,NDUFA4L2,VIM,FN1,CDH1,ACTB,GAPDH,RPL13A \
  --proposals results/track_a_task_landscape/lihc/opus_proposals.json \
  --n-populations 20 --population-size 50 --iterations 1500 --maxsize 15 \
  --seeds 1 7 42 --n-jobs 8 \
  --output results/track_a_task_landscape/lihc/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/lihc_tumor_normal.csv \
  --genes ALB,APOA1,APOB,TTR,TF,GPC3,AFP,AHSG,FGA,MYC,CCND1,CDK4,VEGFA,MKI67,TOP2A,CDK1,PCNA,LDHA,SLC2A1,HK2,TP53,CTNNB1,EPAS1,CA9,NDUFA4L2,VIM,FN1,CDH1,ACTB,GAPDH,RPL13A \
  --candidates results/track_a_task_landscape/lihc/pysr_candidates.json \
  --output results/track_a_task_landscape/lihc/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK E — COAD MSI vs MSS (Colorectal)

MSI-H has immune infiltration (CD8A-high) AND CDX2-high epithelial program AND low ZEB1.
Multi-gene biology is guaranteed — not saturated by a single gene.

```bash
python3 << 'PYEOF'
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd

TMP = Path(".tmp_geo/gdc"); TMP.mkdir(parents=True, exist_ok=True)
EXPR_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-COAD.star_tpm.tsv.gz"
CLIN_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-COAD.clinical.tsv.gz"
expr_p = TMP / "TCGA-COAD.star_tpm.tsv.gz"
clin_p = TMP / "TCGA-COAD.clinical.tsv.gz"
if not expr_p.exists(): urllib.request.urlretrieve(EXPR_URL, expr_p); print("downloaded")
if not clin_p.exists(): urllib.request.urlretrieve(CLIN_URL, clin_p); print("downloaded")

GENES = {
    "MLH1":"ENSG00000076242","MSH2":"ENSG00000095002","MSH6":"ENSG00000116062",
    "PMS2":"ENSG00000122512","EPCAM":"ENSG00000119888",
    "CD8A":"ENSG00000153563","CD274":"ENSG00000120217","PDCD1LG2":"ENSG00000197291",
    "CD4":"ENSG00000010610","FOXP3":"ENSG00000049768",
    "CDX2":"ENSG00000165556","EPHB2":"ENSG00000133216",
    "ZEB1":"ENSG00000148516","VIM":"ENSG00000026025","FN1":"ENSG00000115414",
    "MKI67":"ENSG00000148773","TOP2A":"ENSG00000131747","CDK1":"ENSG00000170312",
    "KRAS":"ENSG00000133703","BRAF":"ENSG00000157764","EGFR":"ENSG00000146648",
    "MYC":"ENSG00000136997","CCND1":"ENSG00000110092",
    "LDHA":"ENSG00000134333","SLC2A1":"ENSG00000117394","HK2":"ENSG00000159399",
    "VEGFA":"ENSG00000112715",
    "ACTB":"ENSG00000075624","GAPDH":"ENSG00000111640","RPL13A":"ENSG00000142541",
}
ensembl_map = {v: k for k, v in GENES.items()}

expr = pd.read_csv(expr_p, sep="\t", index_col=0, compression="gzip")
idx_clean = expr.index.str.replace(r"\.\d+$", "", regex=True)
mask = idx_clean.isin(ensembl_map)
expr_sub = expr.loc[mask].copy()
expr_sub.index = idx_clean[mask].map(ensembl_map)
expr_sub = expr_sub.T
expr_sub = np.log1p(expr_sub + 0.001)
expr_sub.index.name = "sample_id"

tumor = expr_sub[expr_sub.index.str[13:15].isin(["01"])].copy()
tumor.index = tumor.index.str[:15]

clin = pd.read_csv(clin_p, sep="\t", low_memory=False)
msi_col = next((c for c in clin.columns if "msi" in c.lower() or "microsatellite" in c.lower()), None)
if msi_col is None:
    print("MSI column not found. Columns:", [c for c in clin.columns if "status" in c.lower()][:10])
    raise SystemExit("Find MSI column manually")
print(f"MSI column: {msi_col!r}", clin[msi_col].value_counts().to_dict())

s_col = "sample" if "sample" in clin.columns else clin.columns[0]
msi_df = clin[[s_col, msi_col]].dropna(); msi_df.columns = ["sample_id", "msi"]

def _label(v):
    v = str(v).strip().upper()
    if "HIGH" in v or "MSI-H" in v or "MSI_H" in v: return "disease"
    if "STABLE" in v or "MSS" in v or "LOW" in v or "MSI-L" in v: return "control"
    return None

msi_df["label"] = msi_df.msi.map(_label)
msi_df = msi_df.dropna(subset=["label"])
print(f"MSI-H(disease)={(msi_df.label=='disease').sum()}  MSS(control)={(msi_df.label=='control').sum()}")

msi_df["sample_id"] = msi_df.sample_id.str[:15]
merged = tumor.join(msi_df.set_index("sample_id")[["label","msi"]], how="inner").dropna(subset=["label"])
gene_cols = [c for c in merged.columns if c not in {"label", "msi"}]
out = merged[["label","msi"] + gene_cols].reset_index()
out.insert(0, "sample_id", out.pop("sample_id"))
out.to_csv("data/coad_msi.csv", index=False)
print(f"Saved data/coad_msi.csv n={len(out)}")
PYEOF

mkdir -p results/track_a_task_landscape/coad_msi/
```

**Proposer:**
```python
# run_track_e_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()
df = pd.read_csv("data/coad_msi.csv")

dataset_card = {
    "cohort": "TCGA-COAD", "task": "MSS (control) vs MSI-H (disease) colorectal cancer",
    "n_positive": int((df.label=="disease").sum()), "n_negative": int((df.label=="control").sum()),
}
context = (
    "MSI-H: mismatch repair deficiency (MLH1/MSH2/MSH6 loss), high mutational burden, "
    "immune infiltration (CD8A high, PD-L1/CD274 high, FOXP3 high), BRAF V600E common. "
    "MSS: chromosomal instability, KRAS mutation common, immune-cold. "
    "Expected law: CD8A + CDX2 - ZEB1 or MLH1 - VIM. "
    "Multi-gene biology is strong here — task may NOT be saturated by a single gene. "
    "Propose 5 law families. Include at least one negative control. "
    "For each: initial_guess, expected_behavior, skeptic_test."
)
genes = ["MLH1","MSH2","MSH6","PMS2","EPCAM","CD8A","CD274","PDCD1LG2","CD4","FOXP3",
         "CDX2","EPHB2","ZEB1","VIM","FN1","MKI67","TOP2A","CDK1",
         "KRAS","BRAF","EGFR","MYC","CCND1",
         "LDHA","SLC2A1","HK2","VEGFA","ACTB","GAPDH","RPL13A"]

result = c.propose_laws(dataset_card=dataset_card, features=genes, context=context)
with open("results/track_a_task_landscape/coad_msi/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("COAD-MSI proposals saved. Families:", len(result.get("families", [])))
```

```bash
python run_track_e_proposer.py

python src/pysr_sweep.py \
  --data data/coad_msi.csv \
  --genes MLH1,MSH2,MSH6,PMS2,EPCAM,CD8A,CD274,PDCD1LG2,CD4,FOXP3,CDX2,EPHB2,ZEB1,VIM,FN1,MKI67,TOP2A,CDK1,KRAS,BRAF,EGFR,MYC,CCND1,LDHA,SLC2A1,HK2,VEGFA,ACTB,GAPDH,RPL13A \
  --proposals results/track_a_task_landscape/coad_msi/opus_proposals.json \
  --n-populations 20 --population-size 50 --iterations 1500 --maxsize 15 \
  --seeds 1 7 42 --n-jobs 8 \
  --output results/track_a_task_landscape/coad_msi/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/coad_msi.csv \
  --genes MLH1,MSH2,MSH6,PMS2,EPCAM,CD8A,CD274,PDCD1LG2,CD4,FOXP3,CDX2,EPHB2,ZEB1,VIM,FN1,MKI67,TOP2A,CDK1,KRAS,BRAF,EGFR,MYC,CCND1,LDHA,SLC2A1,HK2,VEGFA,ACTB,GAPDH,RPL13A \
  --candidates results/track_a_task_landscape/coad_msi/pysr_candidates.json \
  --output results/track_a_task_landscape/coad_msi/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK F — PRAD Gleason High vs Low

> **Gleason format note:** TCGA-PRAD GDC clinical stores Gleason as primary grade only
> (e.g., `3`, `4`) not as a sum. Check `g_df.gleason.value_counts()` output and adapt
> `_label` logic accordingly if the column holds grade groups (1-5) instead of "X+Y".

```bash
python3 << 'PYEOF'
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd

TMP = Path(".tmp_geo/gdc"); TMP.mkdir(parents=True, exist_ok=True)
EXPR_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-PRAD.star_tpm.tsv.gz"
CLIN_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-PRAD.clinical.tsv.gz"
expr_p = TMP / "TCGA-PRAD.star_tpm.tsv.gz"
clin_p = TMP / "TCGA-PRAD.clinical.tsv.gz"
if not expr_p.exists(): urllib.request.urlretrieve(EXPR_URL, expr_p); print("downloaded")
if not clin_p.exists(): urllib.request.urlretrieve(CLIN_URL, clin_p); print("downloaded")

# NKX3-1 has a hyphen — use safe column name NKX31
GENES = {
    "AR":"ENSG00000169083","KLK3":"ENSG00000142515","KLK2":"ENSG00000167751",
    "FOLH1":"ENSG00000086205","AMACR":"ENSG00000242110","ERG":"ENSG00000157554",
    "ETV1":"ENSG00000006468","MYC":"ENSG00000136997","PTEN":"ENSG00000171862",
    "TMPRSS2":"ENSG00000184012","NKX31":"ENSG00000167034",  # NKX3-1, renamed to safe identifier
    "MKI67":"ENSG00000148773","TOP2A":"ENSG00000131747","CDK1":"ENSG00000170312",
    "CCNB1":"ENSG00000134057","PCNA":"ENSG00000132646",
    "SLC2A1":"ENSG00000117394","LDHA":"ENSG00000134333","VEGFA":"ENSG00000112715",
    "EPAS1":"ENSG00000116016","VIM":"ENSG00000026025","CDH1":"ENSG00000039068",
    "ACTB":"ENSG00000075624","GAPDH":"ENSG00000111640","RPL13A":"ENSG00000142541",
}
ensembl_map = {v: k for k, v in GENES.items()}

expr = pd.read_csv(expr_p, sep="\t", index_col=0, compression="gzip")
idx_clean = expr.index.str.replace(r"\.\d+$", "", regex=True)
mask = idx_clean.isin(ensembl_map)
expr_sub = expr.loc[mask].copy()
expr_sub.index = idx_clean[mask].map(ensembl_map)
expr_sub = expr_sub.T
expr_sub = np.log1p(expr_sub + 0.001)
expr_sub.index.name = "sample_id"
tumor = expr_sub[expr_sub.index.str[13:15].isin(["01"])].copy()
tumor.index = tumor.index.str[:15]

clin = pd.read_csv(clin_p, sep="\t", low_memory=False)
# Find Gleason column
gleason_cols = [c for c in clin.columns if "gleason" in c.lower()]
print(f"Gleason columns found: {gleason_cols}")
if not gleason_cols:
    raise SystemExit("No Gleason column found. Check clin.columns.")
gleason_col = gleason_cols[0]
s_col = "sample" if "sample" in clin.columns else clin.columns[0]
g_df = clin[[s_col, gleason_col]].dropna(); g_df.columns = ["sample_id", "gleason"]
print("Gleason value counts:", g_df.gleason.value_counts().head(10).to_dict())

# Flexible Gleason parser — handles:
# "3+4=7" format → sum
# "3+4" format → sum
# "7" format → direct score
# "3" format (primary grade only) → direct
# Grade group "1"-"5" → map to approx score
def _parse_gleason_score(v):
    v = str(v).strip()
    if "+" in v:
        # "3+4=7" or "3+4" — split on + and take the two primary/secondary values
        parts = v.split("+")
        try:
            primary = int(parts[0].strip())
            # secondary may be "4=7" → take first digit
            secondary_str = parts[1].split("=")[0].strip()
            secondary = int(secondary_str)
            return primary + secondary
        except (ValueError, IndexError):
            return None
    try:
        return int(v)
    except ValueError:
        return None

def _label(v):
    score = _parse_gleason_score(v)
    if score is None: return None
    if score >= 8: return "disease"
    if score <= 6: return "control"
    return None  # Gleason 7 is ambiguous, exclude

g_df["label"] = g_df.gleason.map(_label)
g_df = g_df.dropna(subset=["label"])
print(f"High(>=8)={(g_df.label=='disease').sum()}  Low(<=6)={(g_df.label=='control').sum()}")
if (g_df.label == "disease").sum() < 30:
    print("WARNING: few high-Gleason samples — check gleason_col and _label logic")

g_df["sample_id"] = g_df.sample_id.str[:15]
merged = tumor.join(g_df.set_index("sample_id")[["label","gleason"]], how="inner").dropna(subset=["label"])
gene_cols = [c for c in merged.columns if c not in {"label", "gleason"}]
out = merged[["label","gleason"] + gene_cols].reset_index()
out.insert(0, "sample_id", out.pop("sample_id"))
out.to_csv("data/prad_gleason.csv", index=False)
print(f"Saved data/prad_gleason.csv n={len(out)}")
PYEOF

mkdir -p results/track_a_task_landscape/prad_gleason/
```

**Proposer:**
```python
# run_track_f_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()
df = pd.read_csv("data/prad_gleason.csv")

dataset_card = {
    "cohort": "TCGA-PRAD", "task": "Gleason <=6 (control) vs Gleason >=8 (disease) prostate cancer",
    "n_positive": int((df.label=="disease").sum()), "n_negative": int((df.label=="control").sum()),
}
context = (
    "Prostate cancer grade: Gleason <=6 = well-differentiated, AR-driven, KLK3-high. "
    "Gleason >=8 = aggressive, high proliferation (MKI67/TOP2A), ERG fusion (TMPRSS2-ERG), PTEN loss. "
    "Expected: MKI67 - KLK3 or TOP2A - AR (proliferation vs androgen-differentiation axis). "
    "Same structural analog as TOP2A - EPAS1 in ccRCC (proliferation vs differentiation driver). "
    "Note: gene NKX3-1 is labeled NKX31 (safe identifier, hyphen removed). "
    "Propose 5 law families. Include at least one negative control. "
    "For each: initial_guess, expected_behavior, skeptic_test."
)
genes = ["AR","KLK3","KLK2","FOLH1","AMACR","ERG","ETV1","MYC","PTEN","TMPRSS2","NKX31",
         "MKI67","TOP2A","CDK1","CCNB1","PCNA",
         "SLC2A1","LDHA","VEGFA","EPAS1","VIM","CDH1","ACTB","GAPDH","RPL13A"]

result = c.propose_laws(dataset_card=dataset_card, features=genes, context=context)
with open("results/track_a_task_landscape/prad_gleason/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("PRAD proposals saved. Families:", len(result.get("families", [])))
```

```bash
python run_track_f_proposer.py

python src/pysr_sweep.py \
  --data data/prad_gleason.csv \
  --genes AR,KLK3,KLK2,FOLH1,AMACR,ERG,ETV1,MYC,PTEN,TMPRSS2,NKX31,MKI67,TOP2A,CDK1,CCNB1,PCNA,SLC2A1,LDHA,VEGFA,EPAS1,VIM,CDH1,ACTB,GAPDH,RPL13A \
  --proposals results/track_a_task_landscape/prad_gleason/opus_proposals.json \
  --n-populations 20 --population-size 50 --iterations 1500 --maxsize 15 \
  --seeds 1 7 42 --n-jobs 8 \
  --output results/track_a_task_landscape/prad_gleason/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/prad_gleason.csv \
  --genes AR,KLK3,KLK2,FOLH1,AMACR,ERG,ETV1,MYC,PTEN,TMPRSS2,NKX31,MKI67,TOP2A,CDK1,CCNB1,PCNA,SLC2A1,LDHA,VEGFA,EPAS1,VIM,CDH1,ACTB,GAPDH,RPL13A \
  --candidates results/track_a_task_landscape/prad_gleason/pysr_candidates.json \
  --output results/track_a_task_landscape/prad_gleason/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK G — THCA Papillary vs Follicular

Thyroid subtypes: BRAF/RET-driven papillary (HMGA2-high) vs RAS-driven follicular (PPARG-high).
Note: `NKX2-1` (TTF1) contains a hyphen — stored as `NKX21` (safe identifier).

```bash
python3 << 'PYEOF'
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd

TMP = Path(".tmp_geo/gdc"); TMP.mkdir(parents=True, exist_ok=True)
for url, fname in [
    ("https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-THCA.star_tpm.tsv.gz", "TCGA-THCA.star_tpm.tsv.gz"),
    ("https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-THCA.clinical.tsv.gz", "TCGA-THCA.clinical.tsv.gz"),
]:
    p = TMP / fname
    if not p.exists(): urllib.request.urlretrieve(url, p); print(f"{fname} downloaded")

# NKX2-1 renamed to NKX21 (hyphen is not a valid Python/PySR identifier)
GENES = {
    "HMGA2":"ENSG00000149948","BRAF":"ENSG00000157764","RET":"ENSG00000165731",
    "CITED1":"ENSG00000125931","DDIT3":"ENSG00000175197",
    "PPARG":"ENSG00000132170","PAX8":"ENSG00000125453","FHIT":"ENSG00000189283",
    "TG":"ENSG00000042832","TPO":"ENSG00000115705","TSHR":"ENSG00000165409",
    "NKX21":"ENSG00000136352","FOXE1":"ENSG00000178919",  # NKX2-1/TTF1 renamed
    "MKI67":"ENSG00000148773","TOP2A":"ENSG00000131747","CDK1":"ENSG00000170312",
    "PCNA":"ENSG00000132646",
    "MYC":"ENSG00000136997","VEGFA":"ENSG00000112715","VIM":"ENSG00000026025",
    "CDH1":"ENSG00000039068","FN1":"ENSG00000115414",
    "ACTB":"ENSG00000075624","GAPDH":"ENSG00000111640","RPL13A":"ENSG00000142541",
}
ensembl_map = {v: k for k, v in GENES.items()}

expr = pd.read_csv(TMP / "TCGA-THCA.star_tpm.tsv.gz", sep="\t", index_col=0, compression="gzip")
idx_clean = expr.index.str.replace(r"\.\d+$", "", regex=True)
mask = idx_clean.isin(ensembl_map)
expr_sub = expr.loc[mask].copy()
expr_sub.index = idx_clean[mask].map(ensembl_map)
expr_sub = np.log1p(expr_sub.T + 0.001)
expr_sub.index.name = "sample_id"
tumor = expr_sub[expr_sub.index.str[13:15].isin(["01"])].copy()
tumor.index = tumor.index.str[:15]

clin = pd.read_csv(TMP / "TCGA-THCA.clinical.tsv.gz", sep="\t", low_memory=False)
hist_col = next((c for c in clin.columns if "histolog" in c.lower() or "subtype" in c.lower()), None)
if hist_col is None:
    print("Histology column not found. Candidates:", [c for c in clin.columns if "type" in c.lower()][:10])
    raise SystemExit("Find histology column and hardcode")
print(f"Histology column: {hist_col!r}")
print(clin[hist_col].value_counts().head(10).to_dict())

s_col = "sample" if "sample" in clin.columns else clin.columns[0]
h_df = clin[[s_col, hist_col]].dropna(); h_df.columns = ["sample_id", "histology"]

def _label(v):
    v = str(v).upper()
    if "PAPILLARY" in v: return "disease"
    if "FOLLICULAR" in v: return "control"
    return None

h_df["label"] = h_df.histology.map(_label)
h_df = h_df.dropna(subset=["label"])
print(f"Papillary(disease)={(h_df.label=='disease').sum()}  Follicular(control)={(h_df.label=='control').sum()}")

h_df["sample_id"] = h_df.sample_id.str[:15]
merged = tumor.join(h_df.set_index("sample_id")[["label","histology"]], how="inner").dropna(subset=["label"])
gene_cols = [c for c in merged.columns if c not in {"label", "histology"}]
out = merged[["label","histology"] + gene_cols].reset_index()
out.insert(0, "sample_id", out.pop("sample_id"))
out.to_csv("data/thca_histology.csv", index=False)
print(f"Saved data/thca_histology.csv n={len(out)}")
PYEOF

mkdir -p results/track_a_task_landscape/thca_histology/
```

**Proposer:**
```python
# run_track_g_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()
df = pd.read_csv("data/thca_histology.csv")

dataset_card = {
    "cohort": "TCGA-THCA", "task": "Follicular (control) vs Papillary (disease) thyroid cancer",
    "n_positive": int((df.label=="disease").sum()), "n_negative": int((df.label=="control").sum()),
}
context = (
    "Papillary thyroid cancer: BRAF V600E mutation, RET/PTC fusions, HMGA2 high, "
    "CITED1 high, typical nuclear features (Orphan Annie nuclei). "
    "Follicular thyroid cancer: RAS mutations, PAX8-PPARG fusion, PPARG-high, FHIT low. "
    "Both types share thyroid identity markers (TG, TPO, TSHR, NKX21/TTF1). "
    "Note: NKX2-1 is stored as NKX21 (safe Python identifier — hyphen removed). "
    "Expected law: HMGA2 - PPARG or CITED1 - FHIT. "
    "Propose 5 law families. Include at least one negative control. "
    "For each: initial_guess, expected_behavior, skeptic_test."
)
genes = ["HMGA2","BRAF","RET","CITED1","DDIT3","PPARG","PAX8","FHIT",
         "TG","TPO","TSHR","NKX21","FOXE1",
         "MKI67","TOP2A","CDK1","PCNA",
         "MYC","VEGFA","VIM","CDH1","FN1","ACTB","GAPDH","RPL13A"]

result = c.propose_laws(dataset_card=dataset_card, features=genes, context=context)
with open("results/track_a_task_landscape/thca_histology/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("THCA proposals saved. Families:", len(result.get("families", [])))
```

```bash
python run_track_g_proposer.py

python src/pysr_sweep.py \
  --data data/thca_histology.csv \
  --genes HMGA2,BRAF,RET,CITED1,DDIT3,PPARG,PAX8,FHIT,TG,TPO,TSHR,NKX21,FOXE1,MKI67,TOP2A,CDK1,PCNA,MYC,VEGFA,VIM,CDH1,FN1,ACTB,GAPDH,RPL13A \
  --proposals results/track_a_task_landscape/thca_histology/opus_proposals.json \
  --n-populations 20 --population-size 50 --iterations 1500 --maxsize 15 \
  --seeds 1 7 42 --n-jobs 8 \
  --output results/track_a_task_landscape/thca_histology/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/thca_histology.csv \
  --genes HMGA2,BRAF,RET,CITED1,DDIT3,PPARG,PAX8,FHIT,TG,TPO,TSHR,NKX21,FOXE1,MKI67,TOP2A,CDK1,PCNA,MYC,VEGFA,VIM,CDH1,FN1,ACTB,GAPDH,RPL13A \
  --candidates results/track_a_task_landscape/thca_histology/pysr_candidates.json \
  --output results/track_a_task_landscape/thca_histology/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK H — KIRC Metastasis Round 2 (new Opus law families)

Ask Opus 4.7 to propose NEW families informed by the existing failure history.
Uses the same data and gate as the original run.

```python
# run_track_h_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient

c = OpusClient()

with open("results/track_a_task_landscape/metastasis_expanded/falsification_report.json") as f:
    existing = json.load(f)

failures = [r for r in existing if not r.get("passes_all", False)]
survivors = [r for r in existing if r.get("passes_all", False)]
failure_summary = [
    {"equation": r["equation"], "fail_reasons": r.get("fail_reason",""), "auroc": r.get("law_auc", r.get("auroc"))}
    for r in failures[:20]
]
survivor_equations = [r["equation"] for r in survivors]

dataset_card = {
    "cohort": "TCGA-KIRC",
    "task": "Metastasis M0 vs M1 — ROUND 2, failure-informed proposals",
    "n_positive": 81, "n_negative": 424,
    "panel": "45-gene expanded",
    "existing_survivors": survivor_equations,
    "top_failures": failure_summary[:8],
}
context = (
    "ROUND 2. Existing survivors are: " + json.dumps(survivor_equations) +
    ". ALL encode (proliferation marker) - EPAS1. "
    "The gate REJECTED: " + json.dumps([f['equation'] for f in failure_summary[:8]]) + ". "
    "Propose 5 NEW law families using DIFFERENT genes and biological concepts: "
    "e.g., DNA damage response (BRCA2, ATM), angiogenesis balance (ANGPT2, TEK), "
    "immune evasion (CD274, PDCD1), chromatin remodeling (EZH2, DNMT3A), "
    "metabolic rewiring beyond Warburg. "
    "Do NOT reproduce TOP2A/MKI67/EPAS1 cluster — those are already found. "
    "Include at least one negative control. "
    "For each: initial_guess, expected_behavior, skeptic_test."
)
genes_45 = ["CA9","VEGFA","LDHA","NDUFA4L2","SLC2A1","ENO2","AGXT","ALB","CUBN",
    "PTGER3","SLC12A3","ACTB","GAPDH","RPL13A","MKI67","TOP2A","EPAS1",
    "CDK1","CCNB1","PCNA","MCM2","ANGPTL4","BHLHE40","DDIT4","PGK1",
    "HK2","PKM","ALDOA","VIM","FN1","CDH2","TWIST1","SNAI1",
    "ZEB1","MMP2","MMP9","LRP2","SLC22A8","PLIN2","AQP1","UMOD",
    "HAVCR1","ATP6AP2"]

result = c.propose_laws(dataset_card=dataset_card, features=genes_45, context=context)
with open("results/track_a_task_landscape/kirc_metastasis_v2/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("Round 2 KIRC proposals saved. Families:", len(result.get("families", [])))
print(json.dumps(result.get("families", [])[:2], indent=2))
```

```bash
python run_track_h_proposer.py

python src/pysr_sweep.py \
  --data data/kirc_metastasis_expanded.csv \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3,ACTB,GAPDH,RPL13A,MKI67,TOP2A,EPAS1,CDK1,CCNB1,PCNA,MCM2,ANGPTL4,BHLHE40,DDIT4,PGK1,HK2,PKM,ALDOA,VIM,FN1,CDH2,TWIST1,SNAI1,ZEB1,MMP2,MMP9,LRP2,SLC22A8,PLIN2,AQP1,UMOD,HAVCR1,ATP6AP2 \
  --proposals results/track_a_task_landscape/kirc_metastasis_v2/opus_proposals.json \
  --n-populations 30 --population-size 50 --iterations 2000 --maxsize 20 \
  --seeds 1 7 13 42 123 999 --n-jobs 8 \
  --output results/track_a_task_landscape/kirc_metastasis_v2/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/kirc_metastasis_expanded.csv \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3,ACTB,GAPDH,RPL13A,MKI67,TOP2A,EPAS1,CDK1,CCNB1,PCNA,MCM2,ANGPTL4,BHLHE40,DDIT4,PGK1,HK2,PKM,ALDOA,VIM,FN1,CDH2,TWIST1,SNAI1,ZEB1,MMP2,MMP9,LRP2,SLC22A8,PLIN2,AQP1,UMOD,HAVCR1,ATP6AP2 \
  --candidates results/track_a_task_landscape/kirc_metastasis_v2/pysr_candidates.json \
  --output results/track_a_task_landscape/kirc_metastasis_v2/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

### TRACK I — LGG IDH-mutant vs IDH-wildtype (highest discovery probability)

IDH status in lower-grade glioma is one of the cleanest molecular binary tasks in
oncology. IDH-mutant: 2-HG production, altered Krebs cycle, MGMT methylation, lower
proliferation. IDH-WT: GBM-like, high MKI67/TOP2A, VEGFA-driven angiogenesis.
Well-powered (n > 100 per group), distinct multi-gene biology.

> **NES gene note:** NES (Nestin) Ensembl ID = `ENSG00000132688` (verified).
> ENSG00000152583 is SPARCL1 — a completely different gene.

```bash
python3 << 'PYEOF'
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd

TMP = Path(".tmp_geo/gdc"); TMP.mkdir(parents=True, exist_ok=True)
for url, fname in [
    ("https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-LGG.star_tpm.tsv.gz", "TCGA-LGG.star_tpm.tsv.gz"),
    ("https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-LGG.clinical.tsv.gz", "TCGA-LGG.clinical.tsv.gz"),
]:
    p = TMP / fname
    if not p.exists(): urllib.request.urlretrieve(url, p); print(f"{fname} downloaded")

GENES = {
    "IDH1":"ENSG00000138413","IDH2":"ENSG00000182054",
    "OLIG2":"ENSG00000205927","SOX2":"ENSG00000181449",
    "NES":"ENSG00000132688",  # Nestin — VERIFIED correct Ensembl ID
    "S100B":"ENSG00000160307","GFAP":"ENSG00000131711",
    "CIC":"ENSG00000165078","FUBP1":"ENSG00000162791",
    "MGMT":"ENSG00000170430",
    "LDHA":"ENSG00000134333","HK2":"ENSG00000159399","SLC2A1":"ENSG00000117394",
    "PKM":"ENSG00000067225","MDH2":"ENSG00000146701",
    "EPAS1":"ENSG00000116016","VEGFA":"ENSG00000112715","CA9":"ENSG00000107159",
    "MKI67":"ENSG00000148773","TOP2A":"ENSG00000131747","CDK1":"ENSG00000170312",
    "PCNA":"ENSG00000132646","CCNB1":"ENSG00000134057",
    "VIM":"ENSG00000026025","CDH2":"ENSG00000170558","FN1":"ENSG00000115414",
    "MMP2":"ENSG00000087245","TWIST1":"ENSG00000122691",
    "ACTB":"ENSG00000075624","GAPDH":"ENSG00000111640","RPL13A":"ENSG00000142541",
}
ensembl_map = {v: k for k, v in GENES.items()}

expr = pd.read_csv(TMP / "TCGA-LGG.star_tpm.tsv.gz", sep="\t", index_col=0, compression="gzip")
idx_clean = expr.index.str.replace(r"\.\d+$", "", regex=True)
mask = idx_clean.isin(ensembl_map)
expr_sub = expr.loc[mask].copy()
expr_sub.index = idx_clean[mask].map(ensembl_map)
expr_sub = np.log1p(expr_sub.T + 0.001)
expr_sub.index.name = "sample_id"
tumor = expr_sub[expr_sub.index.str[13:15].isin(["01"])].copy()
tumor.index = tumor.index.str[:15]

clin = pd.read_csv(TMP / "TCGA-LGG.clinical.tsv.gz", sep="\t", low_memory=False)
idh_col = next((c for c in clin.columns if "idh" in c.lower()), None)
if idh_col is None:
    print("IDH column not found. Candidates:", [c for c in clin.columns if "mutation" in c.lower() or "status" in c.lower()][:10])
    raise SystemExit("Find IDH column and hardcode")
print(f"IDH column: {idh_col!r}")
print(clin[idh_col].value_counts().to_dict())

s_col = "sample" if "sample" in clin.columns else clin.columns[0]
idh_df = clin[[s_col, idh_col]].dropna(); idh_df.columns = ["sample_id", "idh"]

def _label(v):
    v = str(v).upper()
    if "MUTANT" in v or v == "MUT": return "disease"
    if "WT" in v or "WILD" in v: return "control"
    return None

idh_df["label"] = idh_df.idh.map(_label)
idh_df = idh_df.dropna(subset=["label"])
print(f"IDH-mutant(disease)={(idh_df.label=='disease').sum()}  IDH-WT(control)={(idh_df.label=='control').sum()}")

idh_df["sample_id"] = idh_df.sample_id.str[:15]
merged = tumor.join(idh_df.set_index("sample_id")[["label","idh"]], how="inner").dropna(subset=["label"])
gene_cols = [c for c in merged.columns if c not in {"label", "idh"}]
out = merged[["label","idh"] + gene_cols].reset_index()
out.insert(0, "sample_id", out.pop("sample_id"))
out.to_csv("data/lgg_idh.csv", index=False)
print(f"Saved data/lgg_idh.csv n={len(out)}")
PYEOF

mkdir -p results/track_a_task_landscape/gbm_idh/
```

**Proposer:**
```python
# run_track_i_proposer.py
import json, sys
sys.path.insert(0, "src")
from lacuna.opus_client import OpusClient
import pandas as pd

c = OpusClient()
df = pd.read_csv("data/lgg_idh.csv")

dataset_card = {
    "cohort": "TCGA-LGG",
    "task": "IDH-wildtype (control) vs IDH-mutant (disease) lower-grade glioma",
    "n_positive": int((df.label=="disease").sum()), "n_negative": int((df.label=="control").sum()),
}
context = (
    "IDH mutation causes 2-HG production, HIF-1alpha inhibition, "
    "altered Krebs cycle (MDH2/PKM reprogrammed), MGMT promoter methylation, CpG island hypermethylation. "
    "IDH-WT glioma (GBM-like): aggressive, high MKI67/TOP2A, VEGFA-driven angiogenesis, NES-high. "
    "IDH-mutant LGG: better differentiated, lower proliferation, OLIG2-high, different metabolic state. "
    "Expected law: MKI67 - OLIG2 or TOP2A - MGMT (proliferative vs differentiation/methylation). "
    "This is a CLEAN binary task with well-powered n (>100 per group). "
    "Propose 5 law families. Include at least one negative control. "
    "For each: initial_guess, expected_behavior, skeptic_test."
)
genes = ["IDH1","IDH2","OLIG2","SOX2","NES","S100B","GFAP","CIC","FUBP1","MGMT",
         "LDHA","HK2","SLC2A1","PKM","MDH2","EPAS1","VEGFA","CA9",
         "MKI67","TOP2A","CDK1","PCNA","CCNB1",
         "VIM","CDH2","FN1","MMP2","TWIST1","ACTB","GAPDH","RPL13A"]

result = c.propose_laws(dataset_card=dataset_card, features=genes, context=context)
with open("results/track_a_task_landscape/gbm_idh/opus_proposals.json", "w") as f:
    json.dump(result, f, indent=2)
print("LGG-IDH proposals saved. Families:", len(result.get("families", [])))
```

```bash
python run_track_i_proposer.py

python src/pysr_sweep.py \
  --data data/lgg_idh.csv \
  --genes IDH1,IDH2,OLIG2,SOX2,NES,S100B,GFAP,CIC,FUBP1,MGMT,LDHA,HK2,SLC2A1,PKM,MDH2,EPAS1,VEGFA,CA9,MKI67,TOP2A,CDK1,PCNA,CCNB1,VIM,CDH2,FN1,MMP2,TWIST1,ACTB,GAPDH,RPL13A \
  --proposals results/track_a_task_landscape/gbm_idh/opus_proposals.json \
  --n-populations 20 --population-size 50 --iterations 1500 --maxsize 15 \
  --seeds 1 7 42 --n-jobs 8 \
  --output results/track_a_task_landscape/gbm_idh/pysr_candidates.json

python src/falsification_sweep.py \
  --data data/lgg_idh.csv \
  --genes IDH1,IDH2,OLIG2,SOX2,NES,S100B,GFAP,CIC,FUBP1,MGMT,LDHA,HK2,SLC2A1,PKM,MDH2,EPAS1,VEGFA,CA9,MKI67,TOP2A,CDK1,PCNA,CCNB1,VIM,CDH2,FN1,MMP2,TWIST1,ACTB,GAPDH,RPL13A \
  --candidates results/track_a_task_landscape/gbm_idh/pysr_candidates.json \
  --output results/track_a_task_landscape/gbm_idh/falsification_report.json \
  --n-permutations 1000 --n-resamples 1000 --n-decoys 100
```

---

## After each track: check result, commit, move on immediately

```bash
# Paste this after each gate run (change TRACK_DIR to actual dir)
TRACK_DIR="stage_expanded"  # change per track
python3 -c "
import json
with open('results/track_a_task_landscape/$TRACK_DIR/falsification_report.json') as f:
    report = json.load(f)
survivors = [r for r in report if r.get('passes_all', False)]
print(f'Track $TRACK_DIR: {len(survivors)}/{len(report)} survivors')
for s in survivors:
    auroc = s.get('law_auc', s.get('auroc', '?'))
    print(f'  PASS: {s[\"equation\"]}  AUROC={auroc:.3f}' if isinstance(auroc, float) else f'  PASS: {s[\"equation\"]}')
if not survivors:
    best = max(report, key=lambda r: r.get('best_single_auroc', r.get('law_auc', r.get('auroc', 0))))
    print(f'  0 survivors. Gate correctly refuses.')
"

make audit   # must print OK
make test    # must pass

git add results/track_a_task_landscape/ data/
git commit -m "[F] Platform: <TRACK_NAME> — <N survivors / gate refuses>

<One-line honest summary: e.g. '0/25 survivors (SFTPC=0.998 saturates)' OR '3/25 PASS: TOP2A-CDH1'>
Gate thresholds unchanged.
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push
# → immediately start next track
```

---

## Cross-task matrix update (run at any point)

```python
# run_matrix_update.py
import json, pathlib, pandas as pd

BASE = pathlib.Path("results/track_a_task_landscape")
tracks = [
    ("metastasis_expanded",  "KIRC",  "Metastasis M0 vs M1 (45-gene)",  "data/kirc_metastasis_expanded.csv", 45),
    ("stage_expanded",       "KIRC",  "Stage I-II vs III-IV (45-gene)", "data/kirc_stage.csv",               45),
    ("luad",                 "LUAD",  "Tumor vs Normal",                 "data/luad_tumor_normal.csv",        23),
    ("brca",                 "BRCA",  "Tumor vs Normal",                 "data/brca_tumor_normal.csv",        31),
    ("brca_pam50",           "BRCA",  "PAM50 LumA vs Basal",            "data/brca_pam50.csv",               35),
    ("stad_metastasis",      "STAD",  "Metastasis M0 vs M1",            "data/stad_metastasis.csv",          35),
    ("lihc",                 "LIHC",  "Tumor vs Normal",                 "data/lihc_tumor_normal.csv",        30),
    ("coad_msi",             "COAD",  "MSI-H vs MSS",                   "data/coad_msi.csv",                 30),
    ("prad_gleason",         "PRAD",  "Gleason <=6 vs >=8",             "data/prad_gleason.csv",             25),
    ("thca_histology",       "THCA",  "Papillary vs Follicular",        "data/thca_histology.csv",           25),
    ("kirc_metastasis_v2",   "KIRC",  "Metastasis v2 (new families)",   "data/kirc_metastasis_expanded.csv", 45),
    ("gbm_idh",              "LGG",   "IDH-mutant vs IDH-WT",           "data/lgg_idh.csv",                  30),
]

rows = []
for dirname, cancer, task, csv_path, panel_n in tracks:
    rp = BASE / dirname / "falsification_report.json"
    if not rp.exists():
        rows.append({"cancer":cancer,"task":task,"panel":f"{panel_n}-gene","n":"—","n_pos":"—","result":"not run"})
        continue
    with open(rp) as f: report = json.load(f)
    n_total = len(report)
    n_surv = sum(1 for r in report if r.get("passes_all", False))
    if n_surv > 0:
        best = max((r for r in report if r.get("passes_all",False)), key=lambda r: r.get("law_auc",r.get("auroc",0)))
        result_str = f"{n_surv}/{n_total} PASS | {best['equation']}"
    else:
        result_str = f"0/{n_total} gate refuses"
    try:
        df = pd.read_csv(csv_path)
        n_pos = (df.label=="disease").sum()
    except: df = None; n_pos = "?"
    rows.append({"cancer":cancer,"task":task,"panel":f"{panel_n}-gene",
                 "n": len(df) if df is not None else "?","n_pos":n_pos,"result":result_str})

df_out = pd.DataFrame(rows)
print(df_out.to_markdown(index=False))
df_out.to_csv("results/track_a_task_landscape/cross_task_matrix.csv", index=False)
```

```bash
python run_matrix_update.py
```

---

## Honest reporting protocol (non-negotiable)

**If 0 survivors:** Gate correctly refuses. Write in SUMMARY:
> "Gate refuses [CANCER] [TASK]: [top gene]=AUROC [X] saturates the task.
> `delta_baseline > 0.05` cannot be cleared by any compound.
> Same behavior as [analogous completed track]. Platform generalization holds."

**If survivors found:** Write:
> "Gate accepts [N]/[M] candidates. Simplest survivor: [equation]
> (AUROC [X], Δbase [Y], ci_lower [Z], perm_p [P]).
> This recapitulates [published biology: cite PMID or describe].
> Law was not seeded — symbolic regression recovered it without guidance."

**Never:** modify gate thresholds, claim "novel" without a citation, cherry-pick results.
The gate's correct behavior (refusing when it should) IS the result, not a failure.

---

## Session termination

When stopping:
1. `python run_matrix_update.py` → generate final cross-task matrix
2. Update `results/track_a_task_landscape/SUMMARY.md` with the matrix
3. `make audit && make test`
4. Final commit: `[F] Platform generalization session: N/9 tracks complete`
5. `git push`

The matrix at session end is the deliverable.
Even 3-4 new tracks substantially strengthen the "any disease" platform claim.
