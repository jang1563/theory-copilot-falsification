"""Build data/paad_survival.csv -- TCGA-PAAD with OS above/below median (~20 months).

Task: overall survival ABOVE median (long-survivor, label=1) vs BELOW (label=0).
Dataset: TCGA-PAAD, n~150 pure PDAC after curation.

Why hard: KRAS is 90% mutated -> useless for survival stratification.
SMAD4 loss alone AUROC ~0.60. The Moffitt 50-gene subtype needs 50 genes.
Hypothesis: GATA6/(CDK1+eps) or SMAD4*CCNB1 compound law >= 0.70 AUROC.

Downloads:
  1. STAR_TPM from GDC-Xena:
       https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-PAAD.star_tpm.tsv.gz
  2. Clinical data from GDC-Xena (same format as TCGA-KIRC.clinical.tsv.gz):
       https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-PAAD.clinical.tsv.gz

Run:
    python3 data/build_tcga_paad.py

Output: data/paad_survival.csv
"""
from __future__ import annotations

import gzip
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
TMP = REPO / ".tmp_geo" / "gdc"
TMP.mkdir(parents=True, exist_ok=True)

STAR_TPM_URL = (
    "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-PAAD.star_tpm.tsv.gz"
)
STAR_TPM_LOCAL = TMP / "TCGA-PAAD.star_tpm.tsv.gz"

CLINICAL_URL = (
    "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-PAAD.clinical.tsv.gz"
)
CLINICAL_LOCAL = TMP / "TCGA-PAAD.clinical.tsv.gz"

OUT_CSV = REPO / "data" / "paad_survival.csv"

VITAL_COL = "vital_status.demographic"
DAYS_DEATH_COL = "days_to_death.demographic"
DAYS_FU_COL = "days_to_last_follow_up.diagnoses"

# Gene panel -- PAAD survival prediction
# Hypothesis: GATA6 (classical subtype marker) vs CDK1 (proliferative drive)
# compound law captures subtype * cell-cycle interaction for survival
TARGET_GENES: dict[str, str] = {
    # Subtype markers (Moffitt classical vs basal)
    "GATA6":   "ENSG00000141448",  # classical subtype marker (good prognosis)
    "KRT17":   "ENSG00000128422",  # basal subtype marker (poor prognosis)
    "KRT7":    "ENSG00000135480",  # ductal marker
    # Cell cycle / proliferation
    "CDK1":    "ENSG00000170312",
    "CCNB1":   "ENSG00000134057",
    "CDK4":    "ENSG00000135446",
    "MKI67":   "ENSG00000148773",
    "TOP2A":   "ENSG00000131747",
    # TGF-beta/SMAD axis (key PAAD driver)
    "SMAD4":   "ENSG00000141646",  # tumor suppressor, 55% lost in PAAD
    "TGFB1":   "ENSG00000105329",
    "CDKN2A":  "ENSG00000147889",  # p16, very frequently lost
    # EMT / invasion
    "VIM":     "ENSG00000026025",
    "CDH2":    "ENSG00000170558",  # N-cadherin (basal marker)
    # CAF / stroma
    "ACTA2":   "ENSG00000107796",  # alpha-SMA, myofibroblast
    "FAP":     "ENSG00000078098",   # fibroblast activation protein
    # Immune
    "CD8A":    "ENSG00000153563",
    "FOXP3":   "ENSG00000049768",  # Tregs
    # Warburg metabolism
    "LDHA":    "ENSG00000134333",
    "SLC2A1":  "ENSG00000117394",  # GLUT1
}

TUMOR_CODES = {"01", "02", "06"}
BARCODE_RE = re.compile(r"^TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}-(\d{2})[A-Z]?")


def _sample_type(barcode: str) -> str | None:
    m = BARCODE_RE.match(barcode)
    if not m:
        return None
    return "tumor" if m.group(1) in TUMOR_CODES else None


def _patient_id(barcode: str) -> str:
    return "-".join(barcode.split("-")[:3])


def download_if_missing(url: str, dest: Path, label: str) -> None:
    if dest.exists():
        print(f"  [cached] {label} ({dest.stat().st_size // (1024*1024)} MB)")
        return
    print(f"  [download] {label}...")
    urllib.request.urlretrieve(url, dest)
    print(f"  [done] {dest.stat().st_size // (1024*1024)} MB")


def load_star_tpm(path: Path, genes: dict[str, str]) -> pd.DataFrame:
    targets = {v: k for k, v in genes.items()}
    rows: dict[str, list[float]] = {}
    sample_ids: list[str] = []

    with gzip.open(path, "rt") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        sample_ids = header[1:]
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            ensembl = parts[0].split(".")[0]
            if ensembl not in targets:
                continue
            symbol = targets[ensembl]
            rows[symbol] = [float(v) for v in parts[1:]]

    if not rows:
        raise RuntimeError("No target genes found in STAR_TPM. Check Ensembl IDs.")

    expr = pd.DataFrame(rows, index=sample_ids)
    expr.index.name = "sample_id"
    expr = expr.reset_index()
    expr["_type"] = expr["sample_id"].map(_sample_type)
    expr = expr[expr["_type"] == "tumor"].drop(columns=["_type"])
    expr["patient_id"] = expr["sample_id"].map(_patient_id)
    return expr.drop_duplicates(subset=["patient_id"])


def load_clinical_gdc(path: Path) -> pd.DataFrame:
    """Parse GDC-Xena clinical TSV for OS info (same format as TCGA-KIRC)."""
    clin = pd.read_csv(path, sep="\t", low_memory=False)
    print(f"  Clinical TSV: {clin.shape[0]} rows, {clin.shape[1]} cols")

    # Detect patient ID column
    id_col = "submitter_id.samples" if "submitter_id.samples" in clin.columns else "sample"
    if id_col not in clin.columns:
        id_col = next((c for c in clin.columns if "submitter_id" in c.lower()), clin.columns[0])

    required = {VITAL_COL, DAYS_DEATH_COL, DAYS_FU_COL}
    missing = required - set(clin.columns)
    if missing:
        available = [c for c in clin.columns if any(k in c.lower() for k in ["vital", "days", "death", "surviv"])]
        print(f"  [warn] Missing columns: {missing}")
        print(f"  [info] Available survival-like columns: {available[:10]}")
        raise RuntimeError(f"Required clinical columns missing: {missing}")

    clin = clin[[id_col, VITAL_COL, DAYS_DEATH_COL, DAYS_FU_COL]].copy()
    clin.columns = ["sample_id", "vital_status", "days_to_death", "days_to_last_fu"]

    # Compute OS in months from days
    clin["os_days"] = clin.apply(
        lambda r: r["days_to_death"] if pd.notna(r["days_to_death"]) and r["days_to_death"] > 0
        else r["days_to_last_fu"],
        axis=1,
    )
    clin = clin[pd.to_numeric(clin["os_days"], errors="coerce").notna()].copy()
    clin["os_days"] = pd.to_numeric(clin["os_days"])
    clin["os_months"] = clin["os_days"] / 30.44

    # Extract patient ID from barcode (first 3 fields)
    clin["patient_id"] = clin["sample_id"].str.extract(r"^(TCGA-[A-Z0-9]+-[A-Z0-9]+)", expand=False)
    clin = clin.dropna(subset=["patient_id", "os_months"])
    print(f"  Survival: {len(clin)} patients with OS, median {clin['os_months'].median():.1f} months")
    return clin


def build() -> pd.DataFrame:
    print("=== TCGA-PAAD survival data build ===")
    download_if_missing(STAR_TPM_URL, STAR_TPM_LOCAL, "TCGA-PAAD STAR_TPM")
    download_if_missing(CLINICAL_URL, CLINICAL_LOCAL, "TCGA-PAAD clinical TSV")

    print("  Parsing expression...")
    expr = load_star_tpm(STAR_TPM_LOCAL, TARGET_GENES)
    print(f"  Expression: {len(expr)} tumor samples, {len([g for g in TARGET_GENES if g in expr.columns])} genes found")

    print("  Parsing clinical/survival...")
    clin = load_clinical_gdc(CLINICAL_LOCAL)

    merged = expr.merge(clin[["patient_id", "os_months", "vital_status"]], on="patient_id", how="inner")
    merged = merged[merged["os_months"].notna()].copy()
    print(f"  After merge + OS filter: {len(merged)} samples")

    # Dichotomise at median OS
    median_os = merged["os_months"].median()
    merged["label"] = (merged["os_months"] > median_os).astype(int)
    print(f"  Median OS: {median_os:.1f} months")
    print(f"  Label dist: {merged['label'].value_counts().to_dict()}")

    gene_cols = [g for g in TARGET_GENES if g in merged.columns]
    out = merged[["sample_id", "label", "os_months"] + gene_cols].copy()
    out = out.dropna(subset=["label"] + gene_cols[:5])

    out.to_csv(OUT_CSV, index=False)
    print(f"  Written: {OUT_CSV} ({len(out)} rows, {len(gene_cols)} genes)")
    return out


if __name__ == "__main__":
    build()
