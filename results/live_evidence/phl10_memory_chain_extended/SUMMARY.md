# PhL-10 — Extended Skeptic Memory chain (sessions 4 + 5)

**Verdict:** PASS — memory chain grew from 3 lesson entries (after
PhL-3 + PhL-7) to 5 entries after two more sessions, and the agent
visibly **quoted and refined** prior lessons instead of restating the
gate thresholds.

## Why this demo exists

PhL-3 showed the minimum-viable read/write pattern (2 sessions).
PhL-7 added a third lesson via the compound orchestrator.
**Three entries is an existence proof, not a visceral demonstration.**
PhL-10 extends the chain so judges can see the Rakuten "distill
lessons from every session" pattern at the scale where the
accumulation is tangible rather than stipulated.

## What the two new sessions tested

| Session | Candidate | Cohort | Axis tested | Predicted | Observed |
|---|---|---|---|---|---|
| 4 | `MKI67 - EPAS1` | TCGA-KIRC metastasis_expanded | **Same** proliferation-vs-HIF-2α axis as prior TOP2A-EPAS1 survivor, **different** proliferation marker | PASS | PASS |
| 5 | `SFTPC - log1p(MKI67)` | **TCGA-LUAD** tumor-vs-normal | **Different cancer**; tests whether prior `best-single ≥ 0.95 → reject` rule generalizes | FAIL | FAIL |

The point of session 5 is not LUAD per se — it is the **cross-cancer
transfer** of a rule the Skeptic wrote for KIRC. If the memory only
captures domain-specific trivia, the LUAD call should ignore it. If
the memory captures **generalizable structure**, the LUAD call should
cite the KIRC rule and apply it.

## What the agent actually did (verbatim highlights)

Session 4 text opened with:

> *"Prior lesson that applies: the second lesson explicitly says
> `proliferation_marker − HIF_TF` is the exact headroom regime earlier
> rejections routed toward. This candidate instantiates that family
> with MKI67 swapped for TOP2A. Structural twin → do not demand extra
> novelty evidence..."*

Session 5 text opened with:

> *"Prior lesson that applies: the ceiling-effect rule (`best-single ≥
> 0.95 → reject on delta_baseline`). SFTPC is the LUAD structural
> analog of CA9 for KIRC — canonical tissue-of-origin marker — so the
> rule transfers directly across cancers. Rule upgraded in this
> session's appended lesson to cover LUAD/SFTPC, THCA/TG, PRAD/KLK3,
> HCC/AFP, etc."*

Both quotes are paraphrases of the agent's own output; the verbatim
text is in `verdict.json:sessions[*].agent_text`.

## Server-side verification

After both sessions completed, the memory store was dumped via raw
`/v1/memory_stores/{store_id}/memories` GETs (not the agent API
surface):

```
Memory store contains 1 file(s); ~5 lesson entries.
```

Content file: `/lessons.md` (4 601 chars) — visible in
`memory_snapshot_after.jsonl`. The 5 lessons read as:

1. `[FAIL]` CA9/VEGFA/AGXT → ceiling-effect template (PhL-3 session A)
2. `[FAIL]` LDHA/SLC2A1/ALB → template upgraded, rule-of-thumb coined
3. `[PASS]` TOP2A−EPAS1 → routes around ceiling via metastasis task
4. `[PASS]` MKI67−EPAS1 → **structural twin of #3** (this session)
5. `[FAIL]` SFTPC−MKI67 → **ceiling rule generalizes across cancers** (this session)

## Artefacts

| File | Contents |
|---|---|
| `verdict.json` | session IDs, candidate equations, metrics supplied, per-session agent text |
| `memory_snapshot_after.jsonl` | raw memory-store dump (one row per file) |

## Reproduce

```bash
export ANTHROPIC_API_KEY=<your-key>
PYTHONPATH=src .venv/bin/python src/phl10_memory_chain_extended.py
```

Cost: ~$0.40 across 2 Opus 4.7 sessions.
Wall time: ~3-5 min.
