"""Build data/lihc_mvi.csv — TCGA-LIHC with Microvascular Invasion binary label.

Task: microvascular invasion PRESENT (1) vs ABSENT (0), n≈305 with annotation.
Why: AFP single-gene AUROC ~0.61 for MVI — below our gate delta_baseline threshold.
     Compact compound laws (EpCAM+CDK1, EPAS1+EPCAM) are hypothesised to clear it.

Downloads:
  1. STAR_TPM matrix from GDC-Xena S3 (open-tier, no auth):
       https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-LIHC.star_tpm.tsv.gz
  2. Clinical data with MVI from cBioPortal study lihc_tcga_pan_can_atlas_2018:
       https://cbioportal.org/api/studies/lihc_tcga_pan_can_atlas_2018/clinical-data?clinicalDataType=SAMPLE

Run:
    python3 data/build_lihc_mvi.py

Output: data/lihc_mvi.csv
Columns: sample_id, label (1=MVI present / 0=MVI absent), <gene symbols...>

Ref:
  TCGA LIHC MVI paper: PMC8675478
  cBioPortal field: "Vascular Tumor Cell Type" or "Microvascular Invasion"
"""
from __future__ import annotations

import gzip
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
TMP = REPO / ".tmp_geo" / "gdc"
TMP.mkdir(parents=True, exist_ok=True)

# GDC-Xena hub — same S3 bucket as KIRC/LUAD builds
STAR_TPM_URL = (
    "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-LIHC.star_tpm.tsv.gz"
)
STAR_TPM_LOCAL = TMP / "TCGA-LIHC.star_tpm.tsv.gz"

# cBioPortal LIHC Pan-Cancer Atlas clinical data
# lihc_tcga (not pan_can_atlas) has VASCULAR_INVASION at patient level
CBIO_CLINICAL_URL = (
    "https://www.cbioportal.org/api/studies/lihc_tcga/clinical-data"
    "?clinicalDataType=PATIENT&pageSize=10000"
)
CBIO_CLINICAL_LOCAL = TMP / "lihc_tcga_patient.json"

OUT_CSV = REPO / "data" / "lihc_mvi.csv"

# Gene panel for MVI prediction
# Hypothesis: EpCAM (stemness/MVI marker) × CDK1 (proliferation) compound law
TARGET_GENES: dict[str, str] = {
    # Proliferation / cell cycle
    "TOP2A":  "ENSG00000131747",
    "MKI67":  "ENSG00000148773",
    "CDK1":   "ENSG00000170312",
    "CCNB1":  "ENSG00000134057",
    "PCNA":   "ENSG00000132646",
    # Stemness / invasion
    "EPCAM":  "ENSG00000119888",  # EpCAM — key MVI predictor
    "SOX9":   "ENSG00000125398",
    "CD44":   "ENSG00000026508",
    # EMT
    "VIM":    "ENSG00000026025",
    "ZEB1":   "ENSG00000148516",
    "CDH1":   "ENSG00000039068",  # E-cadherin (loss → MVI)
    "CDH2":   "ENSG00000170558",  # N-cadherin (gain → MVI)
    "SNAI1":  "ENSG00000124216",
    # HIF / hypoxia (hepatic)
    "EPAS1":  "ENSG00000116016",  # HIF-2α
    "HIF1A":  "ENSG00000100644",
    "VEGFA":  "ENSG00000112715",
    # Liver function / HCC markers
    "GPC3":   "ENSG00000147257",  # glypican-3, HCC marker
    "TERT":   "ENSG00000164362",  # telomerase, activated in HCC
    "AFP":    "ENSG00000081051",   # alpha-fetoprotein (single-gene ceiling)
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
        print(f"  [cached] {label}")
        return
    print(f"  [download] {label} ...")
    urllib.request.urlretrieve(url, dest)
    print(f"  [done] {dest.stat().st_size // 1024} KB")


def load_star_tpm(path: Path, genes: dict[str, str]) -> pd.DataFrame:
    """Parse GDC Xena STAR_TPM matrix → per-sample gene expression."""
    targets_versionless = {v: k for k, v in genes.items()}
    rows: list[tuple[str, np.ndarray]] = []
    sample_ids: list[str] = []

    with gzip.open(path, "rt") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        samples = header[1:]  # sample barcodes
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            ensembl_full = parts[0]
            ensembl = ensembl_full.split(".")[0]
            if ensembl not in targets_versionless:
                continue
            symbol = targets_versionless[ensembl]
            values = np.array([float(v) for v in parts[1:]], dtype=np.float32)
            rows.append((symbol, values))

    if not rows:
        raise RuntimeError("No target genes found in the STAR_TPM matrix.")

    expr = pd.DataFrame(
        {symbol: vals for symbol, vals in rows},
        index=samples,
    )
    expr.index.name = "sample_id"
    expr = expr.reset_index()
    # Filter to primary tumor
    expr["_type"] = expr["sample_id"].map(_sample_type)
    expr = expr[expr["_type"] == "tumor"].drop(columns=["_type"])
    # Shorten barcodes to patient level (first 12 chars: TCGA-XX-XXXX)
    # Keep full sample barcode as-is (some patients have multiple tumors)
    expr["patient_id"] = expr["sample_id"].map(_patient_id)
    return expr


def load_mvi_labels(path: Path) -> pd.DataFrame:
    """Parse cBioPortal PATIENT JSON (lihc_tcga) → patient_id → MVI label.

    VASCULAR_INVASION values: 'None' (label=0), 'Micro' (label=1), 'Macro' (excluded).
    Macrovascular invasion is clinically distinct from microvascular invasion.
    """
    with open(path) as fh:
        data = json.load(fh)

    records: list[dict] = []
    for entry in data:
        attr = entry.get("clinicalAttributeId", "")
        if attr.upper() != "VASCULAR_INVASION":
            continue
        pid = entry.get("patientId", "")
        value = str(entry.get("value", "")).strip()
        if value == "Micro":
            label = 1
        elif value == "None":
            label = 0
        else:
            continue  # Skip Macro (macrovascular) and unknown
        if pid:
            records.append({"patient_id": pid, "label": label})

    df = pd.DataFrame(records).drop_duplicates("patient_id")
    print(f"  MVI labels: {len(df)} patients, {df['label'].sum()} MVI-positive (Micro)")
    return df


def fetch_cbio_clinical() -> None:
    """Fetch cBioPortal clinical data. Falls back to manual note if API fails."""
    if CBIO_CLINICAL_LOCAL.exists():
        print("  [cached] cBioPortal clinical JSON")
        return
    print("  [fetch] cBioPortal LIHC clinical data...")
    try:
        req = urllib.request.Request(
            CBIO_CLINICAL_URL,
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        CBIO_CLINICAL_LOCAL.write_bytes(raw)
        print(f"  [done] {CBIO_CLINICAL_LOCAL.stat().st_size // 1024} KB")
    except Exception as exc:
        print(f"  [warn] cBioPortal fetch failed: {exc}")
        print("  Manual fallback: download from https://cbioportal.org/study/summary?id=lihc_tcga_pan_can_atlas_2018")
        print("  → 'Download' → 'All clinical data' → save as .tmp_geo/gdc/lihc_tcga_clinical_sample.json")
        sys.exit(1)


def build() -> pd.DataFrame:
    print("=== LIHC MVI data build ===")
    download_if_missing(STAR_TPM_URL, STAR_TPM_LOCAL, "TCGA-LIHC STAR_TPM")
    fetch_cbio_clinical()

    print("  Parsing expression matrix...")
    expr = load_star_tpm(STAR_TPM_LOCAL, TARGET_GENES)
    print(f"  Expression: {len(expr)} tumor samples, {len(TARGET_GENES)} target genes")

    print("  Parsing MVI labels...")
    mvi = load_mvi_labels(CBIO_CLINICAL_LOCAL)

    # Merge on patient_id
    merged = expr.merge(mvi, on="patient_id", how="inner")
    print(f"  After merge: {len(merged)} samples with MVI annotation")
    print(f"  Label distribution: {merged['label'].value_counts().to_dict()}")

    # Deduplicate: one sample per patient (take first tumor sample)
    merged = merged.drop_duplicates(subset=["patient_id"])

    gene_cols = [g for g in TARGET_GENES if g in merged.columns]
    out = merged[["sample_id", "label", "patient_id"] + gene_cols].copy()
    out = out.dropna(subset=["label"] + gene_cols)
    out["label"] = out["label"].astype(int)

    out.to_csv(OUT_CSV, index=False)
    print(f"  Written: {OUT_CSV} ({len(out)} rows, {len(gene_cols)} genes)")
    print(f"  MVI present: {out['label'].sum()} / {len(out)}")
    return out


if __name__ == "__main__":
    build()
