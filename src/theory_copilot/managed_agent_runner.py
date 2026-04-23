import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable

import anthropic

NIGHT2_SYSTEM = (
    "You are a scientific computing assistant specializing in symbolic regression. "
    "Your task: run a PySR hyperparameter sweep on the TCGA-KIRC tumor-vs-normal "
    "gene expression dataset, seeded with Opus-proposed law family guesses "
    "(config/law_proposals.json). Execute python3 src/pysr_sweep.py, then write the "
    "candidate equations (equation, auroc, complexity, seed, law_family) to "
    "results/night2/candidates.json. Log progress and confirm completion with a "
    "structured summary."
)

NIGHT3_SYSTEM = (
    "You are a scientific computing assistant specializing in hypothesis falsification. "
    "Your task: run the 5-test falsification gate on the top-50 candidate equations "
    "from Night 2. Execute python3 src/falsification_sweep.py to test each candidate "
    "against permutation null, bootstrap stability, best-single-feature baseline, "
    "covariate-only confound, and a decoy-feature null. Apply Benjamini-Hochberg FDR "
    "across candidates. Write the ranked report (equation, passes, perm_p, perm_p_fdr, "
    "ci_lower, delta_baseline, delta_confound, decoy_p, fail_reason) to "
    "results/night3/falsification_report.json. Confirm completion with a structured summary."
)

NIGHT4_SYSTEM = (
    "You are a scientific computing assistant specializing in biological law replay. "
    "Your task: replay the top surviving law from Night 3 on the GSE40435 cohort "
    "(independent ccRCC kidney tissue cohort, 101 paired tumor-normal samples, "
    "microarray platform — different from TCGA-KIRC's RNA-seq). Run the same "
    "5-test falsification gate on the independent cohort with per-cohort z-score "
    "standardization. Compute an honest replay verdict: pass, attenuated, or fail. "
    "Write all results (AUC with 95% CI, replay verdict, caveat note) to "
    "results/night4/transfer_report.json. Confirm completion with a structured summary."
)

_NIGHT_SYSTEMS = {2: NIGHT2_SYSTEM, 3: NIGHT3_SYSTEM, 4: NIGHT4_SYSTEM}

_NIGHT_TASKS = {
    2: (
        "Run the PySR hyperparameter sweep:\n"
        "  python3 src/pysr_sweep.py --config config/datasets.json --outdir results/night2\n"
        "Then batch-judge all candidate equations and write the final manifest to "
        "manifest_night2.json. Include top-10 equations with AUC scores."
    ),
    3: (
        "Run the falsification sweep on the top-50 candidates from manifest_night2.json:\n"
        "  python3 src/falsification_sweep.py "
        "--manifest results/night2/manifest_night2.json "
        "--top 50 --outfile results/night3/falsification_report.json\n"
        "Write the ranked results to falsification_report.json."
    ),
    4: (
        "Run GSE40435 replay validation on the surviving equation from "
        "falsification_report.json:\n"
        "  theory-copilot replay "
        "--flagship-artifacts results/night3 "
        "--transfer-dataset GSE40435 --output-root results/night4\n"
        "Write results with AUC and 95% CI to results/night4/transfer_run/transfer_report.json."
    ),
}


def run_path_b(
    night: int,
    hpc_project_dir: str = "",
    title: str | None = None,
) -> dict:
    """
    Path B: single Managed Agent with agent_toolset_20260401 (public beta, no waitlist).

    Night 2 task: run PySR sweep → batch Sonnet judgment → write manifest_night2.json
    Night 3 task: run falsification sweep on top 50 → write falsification_report.json
    Night 4 task: run GSE40435 replay → write transfer_report.json

    Returns: {"session_id": str, "agent_id": str, "output": str, "status": "completed"|"error"}
    """
    client = anthropic.Anthropic()

    system = _NIGHT_SYSTEMS[night]
    task = _NIGHT_TASKS[night]

    agent = client.beta.agents.create(
        name=f"theory_copilot_night{night}",
        model="claude-opus-4-7",
        system=system,
        tools=[{"type": "agent_toolset_20260401"}],
    )

    environment = client.beta.environments.create(
        name=f"theory-copilot-env-night{night}",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )

    session = client.beta.sessions.create(
        agent=agent.id,
        environment_id=environment.id,
        title=title or f"Night {night} theory copilot sweep",
    )

    output_parts: list[str] = []
    status = "completed"

    try:
        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": task}],
                    }
                ],
            )
            for event in stream:
                match event.type:
                    case "agent.message":
                        for block in event.content:
                            output_parts.append(block.text)
                    case "session.status_idle":
                        break
    except Exception as exc:
        status = "error"
        output_parts.append(f"Error: {exc}")

    return {
        "session_id": session.id,
        "agent_id": agent.id,
        "output": "".join(output_parts),
        "status": status,
    }


def run_path_a(
    night: int,
    title: str | None = None,
) -> dict:
    """
    Path A: callable_agents multiagent (requires waitlist).

    Three-agent pattern:
      - Proposer agent (Opus 4.7): reads law_proposals.json, refines law families
      - Searcher agent (Sonnet 4.6): executes PySR via bash, writes candidates
      - Falsifier agent (Opus 4.7): runs falsification_sweep.py, writes report

    Raises NotImplementedError if MANAGED_AGENTS_WAITLIST != "approved".
    Returns same dict shape as run_path_b.
    """
    if os.environ.get("MANAGED_AGENTS_WAITLIST") != "approved":
        raise NotImplementedError("callable_agents requires waitlist approval")

    client = anthropic.Anthropic()

    proposer = client.beta.agents.create(
        name=f"proposer_night{night}",
        model="claude-opus-4-7",
        system=(
            "You are a scientific hypothesis proposer. Read config/law_proposals.json, "
            "select and refine the most promising law families for this experimental run, "
            "and write your refined proposals to results/proposer_output.json."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )

    searcher = client.beta.agents.create(
        name=f"searcher_night{night}",
        model="claude-sonnet-4-6",
        system=(
            "You are a symbolic regression executor. Read results/proposer_output.json "
            "to get the law families to search, then run PySR via bash: "
            "python3 src/pysr_sweep.py. Write candidate equations to results/candidates.json."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )

    falsifier = client.beta.agents.create(
        name=f"falsifier_night{night}",
        model="claude-opus-4-7",
        system=(
            "You are a scientific falsifier. Read results/candidates.json, "
            "run python3 src/falsification_sweep.py on each candidate, "
            "and write the ranked falsification report to results/falsification_report.json."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )

    environment = client.beta.environments.create(
        name=f"theory-copilot-multiagent-night{night}",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )

    role_outputs: dict[str, str] = {}
    status = "completed"
    last_session = None

    chain = [
        (
            "proposer",
            proposer,
            (
                f"Night {night}: select 3-5 compact law families from config/law_proposals.json "
                "(including the required negative control) and write a refined set to "
                "results/proposer_output.json. Emit the family list as JSON in your final message."
            ),
        ),
        (
            "searcher",
            searcher,
            (
                "Read the Proposer's law families below and run PySR via bash:\n"
                "  python3 src/pysr_sweep.py --data <flagship_csv> --genes <CSV of genes> "
                "--proposals config/law_proposals.json --standardize "
                "--output results/candidates.json\n"
                "Emit a JSON summary of candidate equations with train_auroc + test_auroc + novelty.\n\n"
                "=== Proposer output ===\n{proposer}\n=== end Proposer output ==="
            ),
        ),
        (
            "falsifier",
            falsifier,
            (
                "Read the Searcher's candidate equations below and run the 5-test gate:\n"
                "  python3 src/falsification_sweep.py --candidates results/candidates.json "
                "--data <flagship_csv> --genes <CSV of genes> --covariate-cols age,batch_index "
                "--output results/falsification_report.json\n"
                "Emit a JSON summary naming every candidate plus perm_p, perm_p_fdr, ci_lower, "
                "delta_baseline, delta_confound, decoy_p, passes, fail_reason. Flag any law where "
                "train_auroc >> test_auroc as overfit.\n\n"
                "=== Searcher output ===\n{searcher}\n=== end Searcher output ==="
            ),
        ),
    ]

    for role, agent, task_template in chain:
        task = task_template.format(
            proposer=role_outputs.get("proposer", ""),
            searcher=role_outputs.get("searcher", ""),
        )
        session = client.beta.sessions.create(
            agent=agent.id,
            environment_id=environment.id,
            title=title or f"Night {night} {role}",
        )
        last_session = session
        output_parts: list[str] = []
        try:
            with client.beta.sessions.events.stream(session.id) as stream:
                client.beta.sessions.events.send(
                    session.id,
                    events=[
                        {
                            "type": "user.message",
                            "content": [{"type": "text", "text": task}],
                        }
                    ],
                )
                for event in stream:
                    match event.type:
                        case "agent.message":
                            for block in event.content:
                                output_parts.append(block.text)
                        case "session.status_idle":
                            break
        except Exception as exc:
            status = "error"
            output_parts.append(f"Error in {role}: {exc}")
            role_outputs[role] = "".join(output_parts)
            break
        role_outputs[role] = "".join(output_parts)

    import json as _json
    return {
        "session_id": last_session.id if last_session else "",
        "agent_id": falsifier.id,
        "output": _json.dumps(role_outputs),
        "status": status,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Path C — Routine (long-running scheduled driver)
#
# Boris Cherny (2026-04-21 Built with Opus 4.7 kickoff) flagged server-side
# Routines as the area "no one has cracked yet." Path C is Theory Copilot's
# concrete answer: a replication-watchdog that wakes on an interval (or when
# a watched directory changes), runs the Path B Managed Agent for whichever
# night is relevant, and writes a dated verdict log. The loop is deliberately
# local so the repo ships today without requiring a not-yet-public Routines
# API, but the `invoke_fn` injection point lets a native Routine swap in
# once the API is stable.
# ─────────────────────────────────────────────────────────────────────────────


def _dir_fingerprint(path: Path) -> str:
    """Hash of (filename, size, mtime) tuples under path. Cheap, non-recursive."""
    if not path.exists():
        return "missing"
    entries = sorted(
        (f.name, f.stat().st_size, int(f.stat().st_mtime))
        for f in path.iterdir()
        if f.is_file()
    )
    return hashlib.sha256(json.dumps(entries).encode()).hexdigest()[:16]


def run_path_c_routine(
    night: int,
    *,
    interval_seconds: int = 1800,
    max_iterations: int = 0,
    watch_dir: str | None = None,
    log_path: str = "results/routine/verdicts.jsonl",
    invoke_fn: Callable[[int], dict] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict:
    """
    Path C: scheduled Routine wrapper around Path B.

    Parameters
    ----------
    night : int (2, 3, or 4)
        Which night task to drive each iteration.
    interval_seconds : int
        Seconds between iterations. Default 30 min. Set to 0 for fire-and-return.
    max_iterations : int
        Hard stop after this many invocations (0 = unbounded, exit via SIGINT).
    watch_dir : str | None
        If set, only invoke when this directory's file fingerprint changes
        between iterations. The first iteration always runs (baseline).
    log_path : str
        Append-mode JSONL file of per-iteration verdicts.
    invoke_fn : callable(night) -> dict
        Override the invocation (testing / swap-in for native Routines API).
        Defaults to `run_path_b`.
    sleeper : callable(float) -> None
        Override sleep (testing).

    Returns
    -------
    dict with last iteration's result plus `iteration_count` and `status`.
    """
    if night not in (2, 3, 4):
        raise ValueError(f"night must be 2, 3, or 4; got {night}")

    invoke = invoke_fn or (lambda n: run_path_b(n))
    watch_path = Path(watch_dir) if watch_dir else None
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)

    last_fingerprint: str | None = None
    last_result: dict = {"status": "not_started"}
    iteration = 0

    try:
        while True:
            iteration += 1
            current_fp = _dir_fingerprint(watch_path) if watch_path else None

            should_run = (
                watch_path is None  # unconditional cadence
                or last_fingerprint is None  # first pass always runs
                or current_fp != last_fingerprint  # change-triggered
            )

            if should_run:
                last_result = invoke(night)
                entry = {
                    "iteration": iteration,
                    "timestamp": int(time.time()),
                    "night": night,
                    "watch_fingerprint": current_fp,
                    "session_id": last_result.get("session_id", ""),
                    "status": last_result.get("status", "unknown"),
                    "output_chars": len(last_result.get("output", "") or ""),
                }
                with log.open("a") as fh:
                    fh.write(json.dumps(entry) + "\n")
                last_fingerprint = current_fp
            else:
                entry = {
                    "iteration": iteration,
                    "timestamp": int(time.time()),
                    "night": night,
                    "watch_fingerprint": current_fp,
                    "status": "skipped_no_change",
                }
                with log.open("a") as fh:
                    fh.write(json.dumps(entry) + "\n")

            if max_iterations and iteration >= max_iterations:
                break
            if interval_seconds <= 0:
                break
            sleeper(interval_seconds)
    except KeyboardInterrupt:
        last_result["status"] = last_result.get("status", "interrupted")

    return {
        **last_result,
        "iteration_count": iteration,
        "log_path": str(log),
    }
