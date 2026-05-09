"""
Live integration tests for the per-article subagent research pipeline (M2.M4).
==============================================================================

These tests fire real HTTP requests against a running backend at
``http://127.0.0.1:8000``, which in turn talks to a real Ollama server
(``gpt-oss:20b``). They are gated behind the ``live`` marker; the default
``pytest`` invocation in CI does not pick them up.

Run from ``backend/``::

    python -m pytest tests/integration/test_research_live.py \
        -v --tb=short -m live

Pre-flight checks (auto-skip):

* ``GET /health`` on ``http://127.0.0.1:8000`` returns 200 within 5s
* ``GET /api/tags`` on ``http://localhost:11434`` returns 200 within 5s

If either probe fails, ALL tests in this module skip cleanly with a
diagnostic reason.

Three scaling tiers exercise the M4 architecture under increasing load:

1. **1-article scenario** — verifies the per-article fan-out path fires
   at all and the citation guard rail still holds.
2. **10-article scenario** — verifies the SubagentPool's max-concurrent
   cap is honoured and the report cites at least 3 distinct sources.
3. **20-article scenario** — verifies the orchestrator's synthesis-prompt
   size stays bounded (< 30KB) even when 20 articles are summarised. This
   is the architectural payoff: with naive concatenation, a 20-article
   prompt would be 40-100KB; with per-article summaries it is under 30KB.

The prompt-size check parses the backend's structured log line
``synthesis_prompt_size=N articles=M sub_questions=K sources=S``. The
service emits this via :py:meth:`AgenticResearchService._synthesize_streaming`.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx
import pytest


BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Path to the backend.out.log that uvicorn writes to (used for
# prompt-size grep in test 3). Tests that don't need it tolerate a
# missing log file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_LOG = _REPO_ROOT / "logs" / "backend.out.log"


# ------------------------------------------------------------------------ #
#  Pre-flight skip
# ------------------------------------------------------------------------ #


def _backend_alive() -> Tuple[bool, str]:
    try:
        r = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
        if r.status_code != 200:
            return False, f"backend /health returned {r.status_code}"
    except Exception as exc:  # noqa: BLE001
        return False, f"backend unreachable: {exc}"
    return True, ""


def _ollama_alive() -> Tuple[bool, str]:
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        if r.status_code != 200:
            return False, f"ollama /api/tags returned {r.status_code}"
        data = r.json()
        # Verify gpt-oss:20b is loaded; otherwise the agent will fail.
        names = [m.get("name", "") for m in data.get("models", [])]
        if not any("gpt-oss" in n for n in names):
            return False, f"gpt-oss not in /api/tags: {names}"
    except Exception as exc:  # noqa: BLE001
        return False, f"ollama unreachable: {exc}"
    return True, ""


@pytest.fixture(scope="module", autouse=True)
def _preflight():
    backend_ok, backend_reason = _backend_alive()
    if not backend_ok:
        pytest.skip(f"backend not reachable: {backend_reason}")
    ollama_ok, ollama_reason = _ollama_alive()
    if not ollama_ok:
        pytest.skip(f"ollama not reachable or missing model: {ollama_reason}")


# ------------------------------------------------------------------------ #
#  SSE stream helper
# ------------------------------------------------------------------------ #


def _stream_research(
    question: str, *, timeout: float = 240.0
) -> Tuple[List[Dict[str, Any]], float]:
    """POST ``question`` to ``/api/research`` and collect every SSE event.

    Returns ``(events, wall_clock_seconds)``. Events are the parsed JSON
    payloads from each ``data:`` frame. Comment frames (``: keepalive``)
    are silently dropped.

    Raises ``RuntimeError`` if the response is not 200 or the body is
    empty / unparseable.
    """
    events: List[Dict[str, Any]] = []
    t0 = time.monotonic()

    with httpx.Client(timeout=httpx.Timeout(timeout, read=timeout)) as client:
        with client.stream(
            "POST",
            f"{BACKEND_URL}/api/research",
            json={"question": question},
        ) as resp:
            if resp.status_code != 200:
                body = resp.read().decode("utf-8", "replace")[:500]
                raise RuntimeError(
                    f"/api/research returned {resp.status_code}: {body}"
                )

            buf = ""
            for chunk in resp.iter_text():
                buf += chunk
                while "\n\n" in buf:
                    frame, buf = buf.split("\n\n", 1)
                    frame = frame.strip()
                    if not frame:
                        continue
                    if frame.startswith(":"):
                        continue  # comment frame (keepalive)
                    if frame.startswith("data:"):
                        payload_text = frame[len("data:"):].strip()
                        try:
                            events.append(json.loads(payload_text))
                        except json.JSONDecodeError:
                            continue

    return events, time.monotonic() - t0


# ------------------------------------------------------------------------ #
#  Subagent timeline analysis
# ------------------------------------------------------------------------ #


def _max_in_flight(events: List[Dict[str, Any]], skill: str) -> int:
    """Walk the event timeline; return the peak number of concurrent
    ``skill`` subagents in flight (count of seen starts minus matched
    dones/errors at any moment).
    """
    in_flight = 0
    peak = 0
    for ev in events:
        if ev.get("type") != "subagent" or ev.get("skill") != skill:
            continue
        if ev.get("data") == "start":
            in_flight += 1
            peak = max(peak, in_flight)
        elif ev.get("data") in ("done", "error"):
            in_flight = max(0, in_flight - 1)
    return peak


def _subagent_starts(events: List[Dict[str, Any]], skill: str) -> List[Dict[str, Any]]:
    return [
        e
        for e in events
        if e.get("type") == "subagent"
        and e.get("data") == "start"
        and e.get("skill") == skill
    ]


def _distinct_citations(report: str) -> int:
    """Count the number of distinct ``[N]`` citation indices in ``report``."""
    return len({int(n) for n in re.findall(r"\[(\d+)\]", report or "")})


def _read_synthesis_prompt_sizes(question_marker: str) -> List[int]:
    """Scan ``backend.out.log`` for ``synthesis_prompt_size=N`` records.

    Returns every match in the file; the test that uses this filters to
    the most recent one (which corresponds to its own run). The marker
    arg is reserved for future filtering — for now we trust that the
    test runs serially and the latest record is ours.
    """
    if not BACKEND_LOG.exists():
        return []
    sizes: List[int] = []
    pattern = re.compile(r"synthesis_prompt_size=(\d+)")
    try:
        with BACKEND_LOG.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = pattern.search(line)
                if m:
                    sizes.append(int(m.group(1)))
    except OSError:
        return []
    return sizes


# ------------------------------------------------------------------------ #
#  Tests
# ------------------------------------------------------------------------ #


@pytest.mark.live
def test_one_article_scenario():
    """1-article tier: focused query yields 1-2 articles, run completes.

    The query ``"What did Bumble announce about removing the swipe?"``
    targets article 588 (Bumble swipe news), which is a unique mention
    in the corpus — a focused decomposition will surface 1-3 articles.
    """
    question = "What did Bumble announce about removing the swipe?"
    events, wall_clock = _stream_research(question, timeout=120.0)

    # Wall clock budget.
    assert wall_clock <= 120.0, f"wall clock {wall_clock:.1f}s > 120s"

    # No fatal errors.
    assert not any(e.get("type") == "error" for e in events), [
        e for e in events if e.get("type") == "error"
    ][:3]

    # Done event with non-empty report.
    done = [e for e in events if e.get("type") == "phase" and e.get("data") == "done"]
    assert len(done) == 1, "expected exactly one done event"
    report = done[0].get("report") or ""
    assert isinstance(report, str) and report.strip(), "report is empty"

    # Subagent fan-out: the agent's decomposer expands the focused
    # question into 3-5 sub-questions, each searching with top_k=5; with
    # dedup that yields up to ~15 unique articles, capped at 20 by the
    # MAX_ARTICLES_FANOUT constant. We assert >= 1 (proving fan-out
    # fired at all) and the architectural cap (<= 20).
    starts = _subagent_starts(events, "summarize_article")
    assert 1 <= len(starts) <= 20, (
        f"expected 1-20 summarize_article starts in the 1-article tier, "
        f"got {len(starts)}"
    )

    # Max-in-flight cap: even on a tiny tier, the pool must respect
    # max_concurrent_subagents (default 4). This is the M3 contract.
    peak = _max_in_flight(events, "summarize_article")
    assert peak <= 4, f"max-in-flight peak={peak} > 4"

    # Citation guard rail: report has >= 1 [N] marker AND ## Sources Used.
    assert re.search(r"\[\d+\]", report), "no [N] citation in report"
    assert re.search(r"(?im)^##\s+Sources\s+Used\s*$", report), \
        "no '## Sources Used' section"


@pytest.mark.live
def test_ten_article_scenario():
    """10-article tier: broader query, max-concurrent cap honoured.

    The query ``"What's been happening with OpenAI lately?"`` matches
    ~9 articles in the corpus (Trusted Contact, Musk lawsuit, Mira Murati
    deposition, voice intelligence, etc.). The decomposer's 3-5
    sub-questions will surface a mix.
    """
    question = "What's been happening with OpenAI lately?"
    events, wall_clock = _stream_research(question, timeout=240.0)

    assert wall_clock <= 240.0, f"wall clock {wall_clock:.1f}s > 240s"

    assert not any(e.get("type") == "error" for e in events), [
        e for e in events if e.get("type") == "error"
    ][:3]

    done = [e for e in events if e.get("type") == "phase" and e.get("data") == "done"]
    assert len(done) == 1
    report = done[0].get("report") or ""

    # Subagent count: between 3 and 20 (we accept a wide band because
    # search top_k * sub_q count varies by decomposer).
    starts = _subagent_starts(events, "summarize_article")
    assert 3 <= len(starts) <= 20, (
        f"expected 3-20 summarize_article starts in the 10-article tier, "
        f"got {len(starts)}"
    )

    # Max-in-flight: at most 4 (settings.max_concurrent_subagents default).
    peak = _max_in_flight(events, "summarize_article")
    assert peak <= 4, f"max-in-flight peak={peak} > 4"

    # At least 3 distinct citations.
    distinct = _distinct_citations(report)
    assert distinct >= 3, f"only {distinct} distinct [N] citations in report"

    # Sources Used section.
    assert re.search(r"(?im)^##\s+Sources\s+Used\s*$", report), \
        "no '## Sources Used' section"


@pytest.mark.live
def test_twenty_article_scenario():
    """20-article tier: prompt-size canary is the architectural proof.

    The query ``"What recent AI news has been happening?"`` is broad —
    49 articles match ``%AI%`` in the corpus. After dedup + the M4
    fan-out cap (MAX_ARTICLES_FANOUT=20), this surfaces ~15-20 unique
    article IDs. The synthesis prompt size is the key assertion: it
    MUST stay under 30KB. Naive concatenation of 20 article bodies
    would be 40-100KB.
    """
    # Snapshot the log size before the run so we can locate "our" log line.
    log_offset_before: int = 0
    if BACKEND_LOG.exists():
        try:
            log_offset_before = BACKEND_LOG.stat().st_size
        except OSError:
            log_offset_before = 0

    question = "What recent AI news has been happening?"
    events, wall_clock = _stream_research(question, timeout=300.0)

    assert wall_clock <= 300.0, f"wall clock {wall_clock:.1f}s > 300s"

    assert not any(e.get("type") == "error" for e in events), [
        e for e in events if e.get("type") == "error"
    ][:3]

    done = [e for e in events if e.get("type") == "phase" and e.get("data") == "done"]
    assert len(done) == 1
    report = done[0].get("report") or ""

    # Subagent count: 5-25 (broad query). The fan-out CAP is 20
    # (MAX_ARTICLES_FANOUT); the floor depends on how many distinct
    # articles the decomposer's sub-questions surface — broad
    # multi-token AI queries yield ~9-15 unique IDs after dedup.
    starts = _subagent_starts(events, "summarize_article")
    assert 5 <= len(starts) <= 25, (
        f"expected 5-25 summarize_article starts in the 20-article tier, "
        f"got {len(starts)}"
    )

    # Max-in-flight cap.
    peak = _max_in_flight(events, "summarize_article")
    assert peak <= 4, f"max-in-flight peak={peak} > 4"

    # At least 5 distinct citations.
    distinct = _distinct_citations(report)
    assert distinct >= 5, f"only {distinct} distinct [N] citations in report"

    # ---- The architectural canary: synthesis prompt size < 30KB.
    # We read the backend log starting from where it was before our run
    # and pick the latest synthesis_prompt_size record.
    new_sizes: List[int] = []
    if BACKEND_LOG.exists():
        try:
            with BACKEND_LOG.open("r", encoding="utf-8", errors="replace") as fh:
                fh.seek(log_offset_before)
                pattern = re.compile(r"synthesis_prompt_size=(\d+)")
                for line in fh:
                    m = pattern.search(line)
                    if m:
                        new_sizes.append(int(m.group(1)))
        except OSError:
            pass

    if new_sizes:
        prompt_size = new_sizes[-1]
        assert prompt_size < 30000, (
            f"synthesis prompt size {prompt_size} >= 30000 chars "
            f"(M4 architectural canary failed; the orchestrator may be "
            f"leaking raw bodies). Sizes seen: {new_sizes}"
        )
    else:
        # No log line found — the log path may be wrong or backend is
        # logging elsewhere. We don't fail the test on this alone (the
        # subagent + citation assertions above already prove the
        # architecture is working) but we mark it explicitly.
        pytest.fail(
            f"could not find 'synthesis_prompt_size=N' in {BACKEND_LOG}; "
            f"prompt-size canary unverifiable"
        )
