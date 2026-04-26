"""Build data/dipg_openpecan.csv — DMG-H3K27M from OpenPedCan v15.

Task: overall survival above/below median within H3K27M-mutant DIPG/DMG.
Dataset: OpenPedCan v15 (public S3, no auth), n~220 DMG-H3K27M.

Why: H3K27M is universal (~80%) → useless for stratification within mutants.
     ACVR1 co-mutation (20%) → longer OS. OPC-AC axis → statin/ferroptosis
     sensitivity. Hypothesis: OLIG2 − UQCRC1 or ID1 + ID2 − COX4I1 compound law.
     ID1/ID2 confirmed by GSE125627 ACVR1→BMP→ID1/ID2 axis (prior work).

Downloads (no auth, public S3, requester-pays=False):
  Gene expression matrix (FPKM collapsed):
    https://s3.amazonaws.com/d3b-openaccess-us-east-1-prd-pbta/open-targets/v15/gene-expression-rsem-fpkm-collapsed.rds
  OR the TSV version:
    https://s3.amazonaws.com/d3b-openaccess-us-east-1-prd-pbta/open-targets/v15/gene-expression-rsem-fpkm-collapsed.tsv.gz

  Clinical histologies:
    https://s3.amazonaws.com/d3b-openaccess-us-east-1-prd-pbta/open-targets/v15/histologies.tsv

Run:
    python3 data/build_dipg_openpecan.py

Output: data/dipg_openpecan.csv
Fallback: If OpenPedCan S3 fails, use GSE115397 (42 samples) or GSE101108 (34 samples).
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
TMP = REPO / ".tmp_geo" / "openpecan"
TMP.mkdir(parents=True, exist_ok=True)

# OpenPedCan v15 — public S3 (no credentials needed)
BASE_S3 = "https://s3.amazonaws.com/d3b-openaccess-us-east-1-prd-pbta/open-targets/v15"
EXPR_URL = f"{BASE_S3}/gene-expression-rsem-fpkm-collapsed.tsv.gz"
HIST_URL = f"{BASE_S3}/histologies.tsv"

EXPR_LOCAL = TMP / "openpecan_v15_fpkm.tsv.gz"
HIST_LOCAL = TMP / "openpecan_v15_histologies.tsv"

OUT_CSV = REPO / "data" / "dipg_openpecan.csv"

# GEO fallback accessions (smaller n but simpler download)
GEO_PRIMARY = "GSE115397"    # 42 DIPG biopsy samples, survival annotated
GEO_BACKUP  = "GSE101108"    # 34 pediatric brainstem glioma

# Gene panel — DIPG OPC/AC state + BMP/ACVR1 axis
# Hypotheses:
#   OPC → statin-sensitive: OLIG2 high, SOX10 high, HMGCR high, PDGFRA high
#   AC → ferroptosis-sensitive: CD44 high, VIM high, GFAP high
#   BMP output (ACVR1 mutant): ID1, ID2, ID3 high (confirmed by GSE125627)
#   OXPHOS (AC): UQCRC1, COX4I1, NDUFB8 high
#   Proliferation: CDK4, CCND1, CDK6 (CDK4/6 amplification in H3.1K27M)
TARGET_GENE_SYMBOLS = [
    # OPC state (statin-sensitive)
    "OLIG2",    # OPC master TF — OPC-like tumor marker
    "SOX10",    # OPC state marker
    "PDGFRA",   # co-mutated in H3.1K27M-ACVR1 tumors
    "HMGCR",    # cholesterol synthesis rate-limiting — statin target in OPC-like
    "LDLR",     # LDL receptor — OPC cholesterol import
    "SQLE",     # squalene epoxidase — cholesterol synthesis
    # AC state (ferroptosis-sensitive)
    "CD44",     # AC marker, mesenchymal
    "VIM",      # vimentin, EMT
    "GFAP",     # astrocytic differentiation
    # ACVR1/BMP pathway output (ID1/ID2 confirmed in GSE125627)
    "ID1",      # BMP target → ACVR1 downstream
    "ID2",      # BMP target → ACVR1 downstream
    "ID3",      # BMP target
    # OXPHOS (AC-state vulnerability)
    "UQCRC1",   # ubiquinol-cytochrome c reductase — Complex III
    "COX4I1",   # cytochrome c oxidase — Complex IV
    "NDUFB8",   # NADH dehydrogenase — Complex I
    # PRC2 complex (H3K27M-inhibited)
    "EZH2",     # PRC2 catalytic subunit (inhibited by H3K27M)
    "SUZ12",    # PRC2 component
    # Cell cycle / amplification
    "CDK4",     # CDK4 amplification in H3.1K27M
    "CDK6",     # CDK6 amplification
    "CCND1",    # Cyclin D1, CDK4/6 regulatory partner
    "CDKN2A",   # p16/p14ARF — frequently deleted
    # Proliferation control
    "MKI67",    # proliferation index
    "TOP2A",    # proliferation / topo II
]


def download_if_missing(url: str, dest: Path, label: str, timeout: int = 120) -> bool:
    if dest.exists():
        print(f"  [cached] {label} ({dest.stat().st_size // (1024**2)} MB)")
        return True
    print(f"  [download] {label} ...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  [done] {dest.stat().st_size // (1024**2)} MB")
        return True
    except Exception as exc:
        print(f"  [fail] {exc}")
        if dest.exists():
            dest.unlink()
        return False


def build_from_openpecan() -> pd.DataFrame | None:
    print("=== Attempt 1: OpenPedCan v15 (preferred, n~220) ===")
    if not download_if_missing(HIST_URL, HIST_LOCAL, "histologies.tsv"):
        return None
    if not download_if_missing(EXPR_URL, EXPR_LOCAL, "FPKM expression matrix (~4GB, slow)"):
        return None

    print("  Loading histologies...")
    hist = pd.read_csv(HIST_LOCAL, sep="\t", low_memory=False)
    print(f"  Histologies: {len(hist)} rows, columns: {list(hist.columns)[:15]}")

    # Filter to DIPG/DMG-H3K27M
    dipg_mask = (
        hist["short_histology"].str.upper().str.contains("DIPG|DMG|H3K27M", na=False)
        | hist["broad_histology"].str.upper().str.contains("MIDLINE|DIPG|DMG", na=False)
    )
    dipg = hist[dipg_mask].copy()
    print(f"  DIPG/DMG samples: {len(dipg)}")

    if len(dipg) == 0:
        print("  [warn] No DIPG samples found — check histologies.tsv column names")
        print(f"  Available short_histology values: {hist['short_histology'].unique()[:20]}")
        return None

    # Parse overall survival
    os_col = next((c for c in dipg.columns if "overall_survival" in c.lower() or "os_days" in c.lower()), None)
    if os_col is None:
        os_col = "OS"
        print(f"  [warn] OS column not found. Available: {[c for c in dipg.columns if 'surv' in c.lower() or 'death' in c.lower() or 'os' in c.lower()]}")

    print(f"  Loading expression matrix (this may take several minutes)...")
    import gzip
    samples_of_interest = set(dipg.get("Kids_First_Biospecimen_ID", dipg.get("sample_id", pd.Series())).dropna())

    rows: dict[str, list[float]] = {}
    gene_order: list[str] = []
    sample_ids: list[str] = []

    with gzip.open(EXPR_LOCAL, "rt") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        all_samples = header[1:]
        # Find which columns are DIPG samples
        dipg_col_idx = [i for i, s in enumerate(all_samples) if s in samples_of_interest]
        dipg_sample_ids = [all_samples[i] for i in dipg_col_idx]

        for line in fh:
            parts = line.rstrip("\n").split("\t")
            gene = parts[0]
            if gene not in TARGET_GENE_SYMBOLS:
                continue
            vals = [float(parts[i + 1]) for i in dipg_col_idx]
            rows[gene] = vals
            gene_order.append(gene)

    sample_ids = dipg_sample_ids
    expr = pd.DataFrame(rows, index=sample_ids)
    expr.index.name = "sample_id"
    expr = expr.reset_index()

    # Merge with clinical
    bs_col = "Kids_First_Biospecimen_ID" if "Kids_First_Biospecimen_ID" in dipg.columns else "sample_id"
    clinical_subset = dipg[[bs_col, os_col, "vital_status"]].rename(
        columns={bs_col: "sample_id", os_col: "os_days"}
    ) if "vital_status" in dipg.columns else dipg[[bs_col, os_col]].rename(
        columns={bs_col: "sample_id", os_col: "os_days"}
    )
    merged = expr.merge(clinical_subset, on="sample_id", how="inner")
    merged = merged[merged["os_days"].notna()].copy()

    if len(merged) < 20:
        print(f"  [warn] Only {len(merged)} samples with OS — OpenPedCan merge failed. Falling back to GEO.")
        return None

    median_os = merged["os_days"].median()
    merged["label"] = (merged["os_days"] > median_os).astype(int)
    print(f"  Median OS: {median_os:.0f} days ({median_os/30:.1f} months)")
    print(f"  Label dist: {merged['label'].value_counts().to_dict()}")

    gene_cols = [g for g in TARGET_GENE_SYMBOLS if g in merged.columns]
    out = merged[["sample_id", "label", "os_days"] + gene_cols]
    out.to_csv(OUT_CSV, index=False)
    print(f"  Written: {OUT_CSV} ({len(out)} rows, {len(gene_cols)} genes)")
    return out


def build_from_geo_fallback() -> pd.DataFrame | None:
    print(f"\n=== Fallback: GEO {GEO_PRIMARY} (n=42) ===")
    try:
        import GEOparse
    except ImportError:
        print("  GEOparse not installed. Run: pip install GEOparse")
        return None

    print(f"  Downloading {GEO_PRIMARY} series matrix...")
    gse = GEOparse.get_GEO(GEO_PRIMARY, destdir=str(TMP), silent=True)

    # Parse metadata for survival
    records = []
    for gsm_id, gsm in gse.gsms.items():
        meta = gsm.metadata
        chars = {}
        for item in meta.get("characteristics_ch1", []):
            s = (item[0] if isinstance(item, list) else str(item))
            if ":" in s:
                k, v = s.split(":", 1)
                chars[k.strip().lower()] = v.strip()

        os_months = None
        vital = None
        for k, v in chars.items():
            if "survival" in k or "os" == k.strip() or "month" in k:
                try:
                    os_months = float(v)
                except ValueError:
                    pass
            if "vital" in k or "status" in k or "death" in k:
                vital = 1 if v.lower() in {"dead", "deceased", "died", "1"} else 0

        records.append({"gsm_id": gsm_id, "os_months": os_months, "vital_status": vital})

    meta_df = pd.DataFrame(records)
    print(f"  {GEO_PRIMARY}: {len(meta_df)} samples, OS annotated: {meta_df['os_months'].notna().sum()}")
    print(f"  Sample characteristics keys: {list(records[0].keys()) if records else 'none'}")
    print(f"  Full char example: {gse.gsms[list(gse.gsms.keys())[0]].metadata.get('characteristics_ch1', [])[:5]}")

    # Parse expression
    gpl = list(gse.gpls.values())[0]
    ann = gpl.table
    sym_col = next((c for c in ["Gene Symbol", "GENE_SYMBOL", "Symbol", "gene_assignment"] if c in ann.columns), None)
    if sym_col is None:
        print(f"  [warn] No gene symbol column found in GPL. Columns: {list(ann.columns)[:10]}")
        return None

    expr_data = {}
    for gsm_id, gsm in gse.gsms.items():
        t = gsm.table.copy()
        t["ID"] = t["ID_REF"].astype(str) if "ID_REF" in t.columns else t.index.astype(str)
        merged_t = t.merge(ann[["ID", sym_col]].rename(columns={"ID": "ID"}), on="ID", how="left")
        merged_t["VALUE"] = pd.to_numeric(merged_t.get("VALUE", merged_t.get("VALUE", 0)), errors="coerce")
        expr_data[gsm_id] = {
            g: float(merged_t[merged_t[sym_col].str.contains(g, na=False)]["VALUE"].mean())
            for g in TARGET_GENE_SYMBOLS
        }

    expr = pd.DataFrame(expr_data).T
    expr.index.name = "gsm_id"
    expr = expr.reset_index()

    merged = meta_df.merge(expr, on="gsm_id", how="inner")
    with_os = merged[merged["os_months"].notna()].copy()

    if len(with_os) < 15:
        print(f"  [warn] Only {len(with_os)} rows with OS. Metadata parsing may have failed.")
        print("  Inspect with: import GEOparse; gse=GEOparse.get_GEO('GSE115397')")
        print("  list(gse.gsms.values())[0].metadata['characteristics_ch1']")
        return None

    median_os = with_os["os_months"].median()
    with_os["label"] = (with_os["os_months"] > median_os).astype(int)
    gene_cols = [g for g in TARGET_GENE_SYMBOLS if g in with_os.columns]
    out = with_os[["gsm_id", "label", "os_months"] + gene_cols].rename(columns={"gsm_id": "sample_id"})
    out.to_csv(OUT_CSV, index=False)
    print(f"  Written: {OUT_CSV} ({len(out)} rows)")
    return out


if __name__ == "__main__":
    result = build_from_openpecan()
    if result is None:
        print("\n  OpenPedCan failed. Trying GEO fallback...")
        result = build_from_geo_fallback()
    if result is None:
        print("\n[MANUAL STEP NEEDED]")
        print("OpenPedCan and GEO auto-download both failed.")
        print("Options:")
        print("  1. AWS CLI: aws s3 cp s3://d3b-openaccess-us-east-1-prd-pbta/open-targets/v15/ . --recursive --no-sign-request")
        print("  2. PedcBioPortal: https://pedcbioportal.org/study/summary?id=pbta-all")
        print("  3. CAVATICA / CBTN portal: https://cbtn.org")
        sys.exit(1)
