# PhK — Does `sessions.events.list` preserve adaptive-thinking content?

**Question.** Opus 4.7's launch (2026-04-16) introduces `thinking.display =
"summarized"` as the only adaptive-thinking surface. Managed Agents' event log
is append-only and retrievable via `sessions.events.list`. The uniquely-new
capability claim in the 2026-04-23 deep-research was: *a downstream Opus 4.7
call can ingest a prior agent's REASONING (not just conclusions) by loading
the session's thinking events from `events.list`.* That claim needed an
empirical check.

**Method.** Created a Managed Agent (Opus 4.7, no tools), sent a
thinking-inducing prompt (calculate 95% CI on AUROC_A − AUROC_B = 0.004 at
n=505 using Hanley–McNeil SE), streamed events + re-fetched via
`events.list`, compared thinking-chars across both retrieval paths.

**Verdict.** `NO_THINKING_CONTENT_IN_EVENT_LOG` (revised from initial
`NO_THINKING_OBSERVED` after inspecting raw event payloads).

The `agent.thinking` event **IS emitted** (confirmed in both stream + list),
but its JSON payload is `{id, processed_at, type}` — **no content blocks, no
thinking text**. The model's actual reasoning for this prompt was instead
written into the `agent.message` text as step-by-step output (3717 output
tokens, full Hanley–McNeil calculation visible).

**Evidence.**
- Event types seen in BOTH stream and `events.list` (identical):
  `session.status_running`, `user.message`, `span.model_request_start`,
  `agent.thinking`, `agent.message`, `span.model_request_end`,
  `session.status_idle`.
- `agent.thinking` serialized payload (raw from SDK `.model_dump()`):
  ```json
  {"id":"sevt_01Lh2GcetqvZmG9wJYTxQvbb",
   "processed_at":"2026-04-23 17:23:13.635000+00:00",
   "type":"agent.thinking"}
  ```
- `agent.message` content[0].text carries the full reasoning (1.3 kB text,
  all four Hanley–McNeil steps + final 95% CI).

**Implication for submission narrative.**

The uniquely-new claim requires REVISION:

- ❌ "Managed Agents provides a durable REASONING-TRACE substrate accessible
  to downstream 1M-context synthesis." — this is **NOT SUPPORTED** by the
  current event-log design (as of 2026-04-23). Thinking content is not
  persisted.
- ✅ "Managed Agents provides a durable TIMESTAMPED ORDERING of thinking-
  occurrence events plus full agent output text." — this IS supported and
  is still auditable (you can prove a thinking event happened at time T
  before output at time T+Δ, server-attested). But the content inside the
  thinking event is not available to future callers.
- ✅ "The agent's own REASONING STEPS, when written to `agent.message` text
  (common on math / calculation prompts), ARE preserved in `events.list`."
  This is where the published Hanley–McNeil walkthrough ended up in our
  probe — not in `agent.thinking` but in `agent.message`.

**Recommended framing for the hackathon submission:**

> The Managed Agents event log preserves: (a) the complete text of every
> agent message, including step-by-step reasoning the model chooses to
> verbalize, and (b) timestamped markers of when adaptive thinking
> occurred (server-attested ordering). It does NOT preserve the
> intermediate thinking tokens themselves — those are dropped after the
> turn completes. This still composes with Opus 4.7's 1M context for
> retrospective synthesis of *prior agent output + timing metadata*, but
> not for synthesis of *prior agent thinking*. Our H2 1M-context
> synthesis (`src/opus_1m_synthesis.py`) already operates on the
> former — rejection records + survivor equations — so the overall
> architecture stands; only one specific capability claim weakens.

**Cost.** ~$0.10 (one Opus 4.7 call, ~4.4k output tokens).

**Next steps.** None required. This verdict is a scope clarification, not a
blocker. The downstream `opus_1m_synthesis.py` already operates on
`agent.message` + metric bundles, which ARE in the event log.
