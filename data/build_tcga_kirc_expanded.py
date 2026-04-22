"""Build expanded-gene-set variants of the TCGA-KIRC survival + metastasis CSVs.

Re-uses the already-cached TCGA-KIRC.star_tpm.tsv.gz to extract ~45 genes
spanning HIF/hypoxia, Warburg metabolism, normal-kidney tubule markers,
proliferation, metastasis/EMT, and housekeeping controls. Then merges with
the existing survival + metastasis label CSVs to produce:

  data/kirc_survival_expanded.csv
  data/kirc_metastasis_expanded.csv

Both have the same label definitions as kirc_survival.csv /
kirc_metastasis.csv but with 30 extra gene columns on top of the 15 already
present. The extra genes let Track A's Option A stress-test whether
PySR's "law collapses to single dominant gene" pattern persists when the
feature space is 3x larger.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd


STAR_TPM_LOCAL = Path(".tmp_geo/gdc/TCGA-KIRC.star_tpm.tsv.gz")

# Ensembl ID -> gene symbol. 45 curated genes spanning the relevant ccRCC
# biology axes. Version suffixes are stripped at load time.
EXPANDED_GENES: dict[str, str] = {
    # HIF / hypoxia / angiogenesis (existing + new)
    "CA9":       "ENSG00000107159",
    "CA12":      "ENSG00000074410",
    "VEGFA":     "ENSG00000112715",
    "ANGPTL4":   "ENSG00000167772",
    "EPAS1":     "ENSG00000116016",
    "BHLHE40":   "ENSG00000134107",
    "DDIT4":     "ENSG00000168209",
    "NDUFA4L2":  "ENSG00000185633",
    # Warburg / glycolysis
    "LDHA":      "ENSG00000134333",
    "LDHB":      "ENSG00000111716",
    "SLC2A1":    "ENSG00000117394",
    "ENO1":      "ENSG00000074800",
    "ENO2":      "ENSG00000111674",
    "HK2":       "ENSG00000159399",
    "PFKP":      "ENSG00000067057",
    "ALDOA":     "ENSG00000149925",
    "PDK1":      "ENSG00000152256",
    "PGK1":      "ENSG00000102144",
    "PKM":       "ENSG00000067225",
    # Normal kidney / tubule identity
    "AGXT":      "ENSG00000172482",
    "ALB":       "ENSG00000163631",
    "CUBN":      "ENSG00000107611",
    "LRP2":      "ENSG00000081479",
    "PTGER3":    "ENSG00000050628",
    "CALB1":     "ENSG00000104327",
    "SLC12A1":   "ENSG00000074803",
    "SLC12A3":   "ENSG00000070031",
    "SLC22A8":   "ENSG00000149452",
    # Proliferation
    "MKI67":     "ENSG00000148773",
    "CDK1":      "ENSG00000170312",
    "CCNB1":     "ENSG00000134057",
    "TOP2A":     "ENSG00000131747",
    "PCNA":      "ENSG00000132646",
    "MCM2":      "ENSG00000073111",
    # Metastasis / EMT
    "COL4A2":    "ENSG00000134871",
    "SPP1":      "ENSG00000118785",
    "MMP9":      "ENSG00000100985",
    "S100A4":    "ENSG00000196154",
    "CXCR4":     "ENSG00000121966",
    # ccRCC-specific lineage / dedifferentiation
    "PAX8":      "ENSG00000125618",
    "PAX2":      "ENSG00000075891",
    "KRT7":      "ENSG00000135480",
    # Housekeeping / control
    "ACTB":      "ENSG00000075624",
    "GAPDH":     "ENSG00000111640",
    "RPL13A":    "ENSG00000142541",
}


def _load_star_tpm(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise RuntimeError(
            f"Cached star_tpm not found at {path}. Run data/build_tcga_kirc.py first."
        )
    df = pd.read_csv(path, sep="\t", index_col=0)
    return df


def _extract_genes(star_tpm: pd.DataFrame) -> pd.DataFrame:
    # Drop Ensembl version suffix ("ENSG00000107159.12" -> "ENSG00000107159")
    base_ids = [i.split(".")[0] for i in star_tpm.index]
    star_tpm = star_tpm.copy()
    star_tpm.index = base_ids

    keep_rows = []
    symbol_by_row = {}
    for sym, ensid in EXPANDED_GENES.items():
        if ensid in star_tpm.index:
            keep_rows.append(ensid)
            symbol_by_row[ensid] = sym

    sub = star_tpm.loc[keep_rows]
    sub.index = [symbol_by_row[r] for r in sub.index]
    # Samples become rows. sample_id format: "TCGA-B0-5695-01A"
    mat = sub.T
    mat.index.name = "sample_id"
    print(
        f"Extracted {mat.shape[1]} genes for {mat.shape[0]} samples "
        f"(missing: {sorted(set(EXPANDED_GENES) - set(symbol_by_row.values()))})"
    )
    return mat.reset_index()


def _merge_with_labels(expr: pd.DataFrame, label_csv: Path, out_csv: Path) -> None:
    if not label_csv.exists():
        print(f"SKIP: {label_csv} not found")
        return

    labels = pd.read_csv(label_csv)
    # Keep only label + covariates + identity from the old CSV; drop the old
    # 15-gene columns and replace with the expanded set.
    meta_cols = [
        c for c in labels.columns
        if c in {
            "sample_id", "label", "stage", "vital_status", "days_to_death",
            "days_to_last_fu", "m_stage", "age", "batch_index", "patient_id",
        }
    ]
    labels_meta = labels[meta_cols].copy()

    merged = labels_meta.merge(expr, on="sample_id", how="inner")

    gene_cols = [c for c in merged.columns if c not in meta_cols]
    ordered = meta_cols + sorted(gene_cols)
    merged = merged[ordered]

    merged.to_csv(out_csv, index=False)
    print(
        f"Wrote {out_csv}: {merged.shape[0]} samples x {merged.shape[1]} cols"
    )
    print(f"Label counts: {merged['label'].value_counts().to_dict()}")


def main() -> None:
    star_tpm = _load_star_tpm(STAR_TPM_LOCAL)
    print(f"star_tpm shape: {star_tpm.shape}")

    expr = _extract_genes(star_tpm)

    _merge_with_labels(
        expr,
        Path("data/kirc_survival.csv"),
        Path("data/kirc_survival_expanded.csv"),
    )
    _merge_with_labels(
        expr,
        Path("data/kirc_metastasis.csv"),
        Path("data/kirc_metastasis_expanded.csv"),
    )


if __name__ == "__main__":
    main()
