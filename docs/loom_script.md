# Loom demo script — 90 seconds

Target length: **90 seconds, 210 spoken words max (≈ 140 WPM).**
Voice: one take, first-person, no B-roll, plain walkthrough.
Screen: single 1920 × 1080 terminal + browser split, no fancy overlays.

## Shot list (timing + screen content + spoken)

### 0 : 00 – 0 : 10 — Hook

**Screen:** `results/RESULTS.md` open at the top in editor.
**Narration (≈ 28 words):**

> "AI for science has a cheap scalable failure mode: the model that
> proposes a hypothesis is also the judge of whether the hypothesis
> survives. This project fixes that by pre-registering the gate."

### 0 : 10 – 0 : 25 — The setup

**Screen:** `config/law_proposals.json` → scroll to KIRC entries.
**Narration (≈ 40 words):**

> "Opus 4.7 proposes seven compact law families for ccRCC, including
> two negative controls it expects to fail. A five-test statistical
> gate — permutation, bootstrap, baseline, confound, decoy — runs in
> plain Python. Opus cannot rationalise its own laws into passing."

### 0 : 25 – 0 : 45 — The reject cycle

**Screen:** `results/flagship_run/falsification_report.json` with
`jq` or just open; then `results/track_a_task_landscape/SUMMARY.md`
scrolled to the 4-task matrix.
**Narration (≈ 52 words):**

> "On real TCGA-KIRC, the gate rejects 100-plus candidates across
> four tasks. Even the textbook HIF-axis law that Opus itself
> proposed — `log1p(CA9) plus log1p(VEGFA) minus log1p(AGXT)` —
> fails, because CA9 alone already reaches AUROC 0.965 and a
> compound needs plus 0.05 incremental. The gate catches its own
> side."

### 0 : 45 – 1 : 10 — The accept cycle

**Screen:** `results/track_a_task_landscape/metastasis_expanded/falsification_report.json`
showing the passing candidates, then
`results/track_a_task_landscape/plots/survivor_scatter_top2a_vs_epas1.png`
opened full-screen.
**Narration (≈ 62 words):**

> "Then we expand the panel from 11 to 45 genes. Same gate. Same
> thresholds. Nine of thirty candidates pass on metastasis. The
> simplest — `TOP2A minus EPAS1` — says: when a tumour's
> proliferation program runs ahead of its HIF-2α program, it's more
> likely to be metastatic. That's the published ccA-vs-ccB subtype
> axis. PySR re-derived it from scratch. The gate accepted it."

### 1 : 10 – 1 : 25 — The robustness

**Screen:** `results/track_a_task_landscape/survivor_robustness/SUMMARY.md`
showing the robustness table.
**Narration (≈ 32 words):**

> "Same toolkit Track B used to harden the reject verdict now applied
> to the accept. Five of six axes robust, one honest caveat: a 2-gene
> LR with interaction also hits AUROC 0.722 on the same pair."

### 1 : 25 – 1 : 30 — The close

**Screen:** single terminal with `make audit` → `OK`, then git log
one line: `TOP2A - EPAS1`.
**Narration (≈ 18 words):**

> "Twin outcome on one infrastructure. The artefact is the gate.
> Accept and reject are both the point."

## Total

- Narration: ~ 210 spoken words / 90 seconds at ~140 WPM
- Screens: 6 cuts, all local files, no browser sign-in required
- No patient data, no institutional identifiers (`make audit`
  confirms the repo is clean before recording)

## Backup GIF fallback (if Loom upload fails on 4/26)

1. A 6-second GIF of the terminal running `make demo-kirc` and
   printing the survivor row, looped 4x.
2. Embedded in README.md under the "Read first" section with a
   `[demo_gif]` caption.
3. The full static walkthrough in `docs/demo_walkthrough.md` remains
   the long-form reference.

## Rehearsal checklist

- [ ] `make audit` passes before rolling camera
- [ ] `results/flagship_run/falsification_report.json` has `passes:
      false` rows visible
- [ ] `results/track_a_task_landscape/metastasis_expanded/falsification_report.json`
      has ≥ 1 `passes: true` row visible
- [ ] `survivor_scatter_top2a_vs_epas1.png` opens without overflow on
      1920 × 1080
- [ ] Narration cleared for institutional references (only "TCGA-KIRC",
      "GSE40435", "PySR", "Opus 4.7", "Managed Agents", "ccA",
      "ccB")
- [ ] Clock check: script rehearsed under 90 s without cutting
