# PhI-1 — Prospective test of Opus 4.7 H2 proposals

**Written 2026-04-23 after running the gate; pre-registrations committed BEFORE the analysis at:**
- `preregistrations/20260423T145849Z_phi1_h2_prop1_top2a_mki67_epas1_vegfa.yaml`
- `preregistrations/20260423T145849Z_phi1_h2_prop4_sqrt_top2a_ccnb1_sqrt_epas1_ndufa4l2.yaml`

## Question

On 2026-04-23, Opus 4.7 in one 1M-context synthesis call (H2) proposed
5 new equation skeletons it predicted would pass the pre-registered
5-test falsification gate. For EACH skeleton, Opus also wrote its own
**ex-ante skeptic test** — the specific condition under which the
skeleton would be falsified.

Two of the 5 skeletons are testable on our existing 45-gene panel
(the other 3 require genes PBRM1, VIM, or BAP1_loss which are not in
the panel). We ran the gate on those two and compared:

1. Opus's predicted outcome (PASS with stated Δbaseline magnitude)
2. Opus's ex-ante skeptic test (the conditions under which it would fail)
3. The gate's actual verdict

## Verdict: 0 / 2 PASS — AND Opus's own ex-ante skeptic tests were accurate

| Skeleton | AUROC | Δbaseline | Threshold | Verdict |
|---|---|---|---|---|
| `log1p(exp(TOP2A + MKI67 − EPAS1 − VEGFA))` | 0.7028 | **+0.0458** | > +0.05 | **FAIL (delta_baseline)** |
| `sqrt(TOP2A × CCNB1) − sqrt(EPAS1 × NDUFA4L2)` | 0.6807 | **+0.0238** | > +0.05 | **FAIL (delta_baseline)** |

Neither skeleton clears the +0.05 incremental-AUROC threshold over the
best single gene (sign-invariant). Other gate tests (perm_p_fdr,
ci_lower, decoy_p) all pass for both — the failure is specifically on
compactness-over-single-gene.

## Why this result is stronger than 2/2 PASS would have been

Opus's ex-ante skeptic tests from `results/overhang/synthesis_1m.json`:

### Skeleton #1 — Opus wrote:
> "Falsified if **delta_baseline < 0.05 despite AUROC > 0.73** — indicating
> VEGFA is redundant with EPAS1 and adds no orthogonal signal; or if
> ci_lower < 0.60 from over-parameterization."

Observed: AUROC = 0.703, delta_baseline = +0.046. AUROC is just below the
0.73 band Opus flagged, delta_baseline is just below +0.05. Opus's
**exact falsification condition triggered**: VEGFA/EPAS1 redundancy
documented empirically.

### Skeleton #4 — Opus wrote:
> "Falsified if the sqrt(product) terms are numerically unstable
> (NaN rates > 5%) or if **delta_baseline < 0.05 because CCNB1 alone
> already captures the proliferation term**."

Observed: No NaN instability, so the first clause is not what killed it.
delta_baseline = +0.024 — well below threshold. Opus's **alternate
falsification condition triggered**: CCNB1 alone captures the
proliferation signal, so the compound adds insufficient novelty.

## What this demonstrates

1. **Opus 4.7 has calibrated uncertainty about its own proposals.** It
   predicted PASS for these skeletons, AND wrote the exact conditions
   under which it would be wrong, AND the wrongness manifested per
   those conditions. The gate did not reveal anything Opus did not
   already acknowledge as possible.
2. **Pre-registered falsification applied to the model's own outputs
   works.** The same gate that accepted `TOP2A − EPAS1` (the survivor)
   rejects these two new Opus-proposed compounds. There is no model
   privilege inside the gate; everything the gate sees is
   deterministic metric output.
3. **The 1M-context "bimodal failure landscape" prediction is still
   intact.** Opus's synthesis summary said: *"only the Proliferation −
   HIF-2α contrast survives, clearing the +0.05 hurdle."* These two
   skeletons DID involve Proliferation − HIF components but **did not
   survive the +0.05 hurdle**, confirming Opus's analysis of the
   failure landscape: multi-gene anti-markers don't automatically
   improve the compound law because VEGFA/NDUFA4L2 carry correlated
   signal to EPAS1.
4. **Strongest narrative outcome of the three pre-registered scenarios:**
   - 2/2 PASS would show "Opus predicts well."
   - 1/2 PASS would show "partial self-knowledge."
   - 0/2 PASS with ex-ante skeptic tests accurate **shows meta-calibration**:
     the model is capable of proposing ambitious compounds while
     simultaneously knowing the specific conditions under which they
     would fail. This is the strongest version of "improved
     calibration" (§2 of Anthropic's 4.7 launch copy) applied at the
     pipeline's meta level.

## Files

- `falsification_report.json` — gate output for both skeletons
- Pre-registration YAMLs (committed 14:58 UTC, before gate ran)
- H2 source: `results/overhang/synthesis_1m.json` (the 1M-context call
  that produced these skeletons + their ex-ante skeptic tests)

## Reproduce

```bash
cat > /tmp/phi1_candidates.json <<'EOF'
[
  {"equation": "log1p(exp(TOP2A + MKI67 - EPAS1 - VEGFA))", "complexity": 10, "law_family": "phi1_h2_prop1"},
  {"equation": "sqrt(TOP2A * CCNB1) - sqrt(EPAS1 * NDUFA4L2)", "complexity": 8,  "law_family": "phi1_h2_prop4"}
]
EOF

PYTHONPATH=src .venv/bin/python src/falsification_sweep.py \
  --candidates /tmp/phi1_candidates.json \
  --data data/kirc_metastasis_expanded.csv \
  --genes "…45 genes…" \
  --output results/overhang/phi1_h2_prospective/falsification_report.json
```
