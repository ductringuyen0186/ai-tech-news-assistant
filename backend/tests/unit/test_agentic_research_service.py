"""
Unit tests for AgenticResearchService (Milestone 1)
====================================================

Covers the four paths the M1 acceptance contract calls out:

1. ``test_run_happy_path`` - decomposer succeeds first try, every
   sub-question returns hits, synthesis emits a markdown report with
   inline ``[N]`` citations and a ``## Sources Used`` section. Verifies
   the event order is exactly:
       phase: "Decomposing"
       phase: "Searching (i/N)"  (one per sub-question)
       phase: "Synthesizing"
       phase: "done"

2. ``test_invalid_json_then_retry`` - first decomposer call returns
   garbage, second call (the strict retry) returns valid JSON. The run
   completes with the retried sub-questions; only one retry happened.

3. ``test_invalid_json_fallthrough`` - both decomposer calls return
   garbage; the run falls through to single-question mode and still
   completes with exactly one ``Searching (1/1)`` phase.

4. ``test_zero_hit_subquestion`` - one sub-question returns no hits;
   the run still completes, the synthesis prompt explicitly contains
   the "Could not find data on ..." instruction for that sub-question,
   and the final report has ``[N]`` + ``## Sources Used`` (because we
   stitch them server-side as a guard rail).

Ollama is mocked at the ``_call_ollama`` boundary so these tests run
without a live LLM. The SearchService is also faked.
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from src.services.agentic_research_service import (
    AgenticResearchService,
    _SubQuestionResult,
)


# ---------------------------------------------------------------------- #
#  Test doubles
# ---------------------------------------------------------------------- #

class _FakeSearchResult:
    """Quacks like SearchResultItem for the agent's purposes."""

    def __init__(self, **kw):
        self.id = kw.get("id", "article:1")
        self.title = kw.get("title", "Untitled")
        self.url = kw.get("url", "https://example.com/x")
        self.source = kw.get("source", "example")
        self.summary = kw.get("summary", "Some summary text about the topic.")
        self.content = kw.get("content", None)
        self.similarity_score = kw.get("similarity_score", 0.85)


class _FakeSearchResponse:
    def __init__(self, results: List[_FakeSearchResult]):
        self.results = results
        self.execution_time_ms = 1.0


class _FakeSearchService:
    """Records every search call; returns a canned response per call.

    ``responses`` is a list of result-lists. Each ``search`` consumes
    the next entry; if the list is exhausted, returns the last one.
    """

    def __init__(self, responses: List[List[_FakeSearchResult]]):
        assert responses, "need at least one canned response"
        self._responses = responses
        self.calls: List[str] = []

    async def initialize(self):
        return None

    async def search(self, request):
        self.calls.append(request.query)
        idx = min(len(self.calls) - 1, len(self._responses) - 1)
        return _FakeSearchResponse(self._responses[idx])


def _hit(n: int) -> _FakeSearchResult:
    return _FakeSearchResult(
        id=f"article:{n}",
        title=f"Article {n}",
        url=f"https://example.com/a{n}",
        source=f"source{n}",
        summary=f"Body {n}: details about the topic of interest.",
    )


def _collect_event_pairs(events: List[Dict[str, Any]]) -> List[tuple]:
    """Reduce events to (type, data) tuples for easy sequence asserts."""
    return [(e["type"], e.get("data")) for e in events]


# ---------------------------------------------------------------------- #
#  Fixtures
# ---------------------------------------------------------------------- #

VALID_DECOMPOSER_JSON = (
    '{"sub_questions": ['
    '"What companies announced AI chips this week?", '
    '"What technical specs were disclosed?", '
    '"How does this compare to previous announcements?"'
    ']}'
)

GOOD_SYNTHESIS_REPORT = (
    "## Executive Summary\n"
    "Several companies announced new AI chips this week [1].\n"
    "\n"
    "## Key Findings\n"
    "- New silicon from vendor A [1]\n"
    "- Updated specs from vendor B [2]\n"
    "\n"
    "## Trends & Themes\n"
    "Increased focus on inference efficiency [1][2].\n"
    "\n"
    "## Sources Used\n"
    "[1] Article 1 - source1 (https://example.com/a1)\n"
    "[2] Article 2 - source2 (https://example.com/a2)\n"
)


def _make_service(
    *,
    decomposer_outputs: List[str],
    synthesis_output: str,
    search_responses: List[List[_FakeSearchResult]],
):
    """Construct a service with a mocked _call_ollama and a fake search service."""
    fake_search = _FakeSearchService(search_responses)
    svc = AgenticResearchService(search_service=fake_search)

    # _call_ollama is called multiple times during a run:
    #   1. decompose (label='generate' by default)
    #   2. (optional) decompose retry
    #   3. synthesize
    # We feed responses in order. A sentinel covers any extra calls.
    call_log: List[Dict[str, Any]] = []
    response_queue = list(decomposer_outputs) + [synthesis_output]

    async def fake_call_ollama(prompt, *, num_predict=512, temperature=0.2, label="generate"):
        call_log.append(
            {
                "prompt": prompt,
                "num_predict": num_predict,
                "temperature": temperature,
                "label": label,
            }
        )
        if response_queue:
            return response_queue.pop(0)
        return synthesis_output  # safety net

    svc._call_ollama = fake_call_ollama  # type: ignore[assignment]
    return svc, fake_search, call_log


# ---------------------------------------------------------------------- #
#  Tests
# ---------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_run_happy_path():
    """Decompose succeeds; each sub-question returns hits; synthesis emits
    a citation-rich markdown report. Event order matches the M1 contract.
    """
    svc, fake_search, calls = _make_service(
        decomposer_outputs=[VALID_DECOMPOSER_JSON],
        synthesis_output=GOOD_SYNTHESIS_REPORT,
        search_responses=[[_hit(1), _hit(2)]],
    )

    events = [evt async for evt in svc.run("AI chip announcements this week")]

    # ---- Event order ----
    pairs = _collect_event_pairs(events)
    # First event must be "Decomposing"
    assert pairs[0] == ("phase", "Decomposing"), pairs
    # Then 3 "Searching (i/3)" events (one per sub-question)
    searching = [p for p in pairs if p[0] == "phase" and p[1].startswith("Searching")]
    assert searching == [
        ("phase", "Searching (1/3)"),
        ("phase", "Searching (2/3)"),
        ("phase", "Searching (3/3)"),
    ], searching
    # Exactly one Synthesizing
    assert pairs.count(("phase", "Synthesizing")) == 1
    # Exactly one done — must be the LAST event
    done_events = [e for e in events if e["type"] == "phase" and e["data"] == "done"]
    assert len(done_events) == 1
    assert events[-1] is done_events[0]

    # ---- No error events ----
    assert not any(e["type"] == "error" for e in events)

    # ---- Final report sanity ----
    report = done_events[0].get("report") or done_events[0].get("data")
    # If the implementation puts the report under "report" we use that;
    # otherwise the test falls back to data which would be "done" (string).
    # The strict expectation: there is a non-empty report somewhere.
    if report == "done":
        # Maybe carried under a different key; check the entire event.
        report = (
            done_events[0].get("report")
            or done_events[0].get("payload")
            or done_events[0].get("body")
        )
    assert isinstance(report, str) and report.strip(), done_events[0]
    assert "[1]" in report or "[2]" in report, "missing inline citation"
    assert "## Sources Used" in report, "missing sources section"

    # ---- Search was called once per sub-question ----
    assert len(fake_search.calls) == 3

    # ---- Ollama was called exactly twice (decompose + synthesize) ----
    labels = [c["label"] for c in calls]
    # Implementation default label is 'generate'; we only assert the count
    assert len(calls) == 2, calls


@pytest.mark.asyncio
async def test_invalid_json_then_retry():
    """First decomposer call is garbage; second is valid JSON. Run completes."""
    svc, fake_search, calls = _make_service(
        decomposer_outputs=[
            "This is not JSON at all, the model went rogue.",
            VALID_DECOMPOSER_JSON,
        ],
        synthesis_output=GOOD_SYNTHESIS_REPORT,
        search_responses=[[_hit(1)]],
    )

    events = [evt async for evt in svc.run("Original question?")]
    pairs = _collect_event_pairs(events)

    # Decomposer should have been called twice (initial + retry)
    # Synthesis once: 3 total calls.
    assert len(calls) == 3, [c["label"] for c in calls]

    # Final event is the done event; run completed.
    assert events[-1]["type"] == "phase"
    assert events[-1]["data"] == "done"

    # We should have 3 searching phases (one per sub-question from the retry).
    searching = [p for p in pairs if p[0] == "phase" and p[1].startswith("Searching")]
    assert len(searching) == 3, searching


@pytest.mark.asyncio
async def test_invalid_json_fallthrough():
    """Both decomposer calls fail; run falls through to single-question mode."""
    svc, fake_search, calls = _make_service(
        decomposer_outputs=[
            "garbage 1",
            "garbage 2 also not json",
        ],
        synthesis_output=GOOD_SYNTHESIS_REPORT,
        search_responses=[[_hit(1)]],
    )

    question = "What's happening with AI chips?"
    events = [evt async for evt in svc.run(question)]
    pairs = _collect_event_pairs(events)

    # Decomposer x2, synthesis x1.
    assert len(calls) == 3

    # Single-question mode: exactly one Searching (1/1) phase.
    searching = [p for p in pairs if p[0] == "phase" and p[1].startswith("Searching")]
    assert searching == [("phase", "Searching (1/1)")], searching

    # The single search should have been issued with the original question.
    assert fake_search.calls == [question], fake_search.calls

    # Run still completes with done.
    assert events[-1]["data"] == "done"
    # And no error events.
    assert not any(e["type"] == "error" for e in events)


@pytest.mark.asyncio
async def test_zero_hit_subquestion():
    """A sub-question with zero hits does not abort the run.

    The synthesis prompt is asked to write 'Could not find data on X' for
    that sub-question, and the final report still has [N] + Sources Used
    because we stitch the citation contract server-side.
    """
    captured_prompts: List[str] = []

    fake_search = _FakeSearchService(
        responses=[
            [_hit(1), _hit(2)],   # sub 1 has hits
            [],                   # sub 2 has zero hits
            [_hit(3)],            # sub 3 has hits
        ]
    )
    svc = AgenticResearchService(search_service=fake_search)

    response_queue = [VALID_DECOMPOSER_JSON, GOOD_SYNTHESIS_REPORT]

    async def fake_call_ollama(prompt, *, num_predict=512, temperature=0.2, label="generate"):
        captured_prompts.append(prompt)
        return response_queue.pop(0)

    svc._call_ollama = fake_call_ollama  # type: ignore[assignment]

    events = [evt async for evt in svc.run("Ai chip topic")]
    pairs = _collect_event_pairs(events)

    # Run completed with 'done'.
    assert events[-1]["data"] == "done"
    assert not any(e["type"] == "error" for e in events)

    # Three searching phases (sub-question 2 still emits its phase, just empty hits).
    searching = [p for p in pairs if p[0] == "phase" and p[1].startswith("Searching")]
    assert len(searching) == 3, searching

    # Synthesis prompt is the second captured prompt; it must contain the
    # "Could not find data on" instruction for the zero-hit sub-question.
    synthesis_prompt = captured_prompts[1]
    assert "Could not find data on" in synthesis_prompt

    # Report still satisfies the citation contract.
    report = events[-1].get("report") or ""
    assert "[1]" in report or "[2]" in report
    assert "## Sources Used" in report


@pytest.mark.asyncio
async def test_done_event_carries_report_string():
    """The done event must carry the final assembled markdown report.

    The exact key carrying the report is implementation-defined (could be
    ``data`` or ``report``), but SOMEWHERE in the done event there must be
    a non-empty string with both a `[N]` citation marker and a
    `## Sources Used` section per the M1 contract.
    """
    svc, _, _ = _make_service(
        decomposer_outputs=[VALID_DECOMPOSER_JSON],
        synthesis_output=GOOD_SYNTHESIS_REPORT,
        search_responses=[[_hit(1), _hit(2)]],
    )

    events = [evt async for evt in svc.run("AI chip news")]
    done = events[-1]
    assert done["type"] == "phase"
    assert done["data"] == "done"

    report = done.get("report") or (done["data"] if done["data"] != "done" else None)
    assert isinstance(report, str) and report.strip()
    import re

    assert re.search(r"\[\d+\]", report), report[:200]
    assert re.search(r"(?im)^##\s+Sources\s+Used\s*$", report), report[:300]


# ---------------------------------------------------------------------- #
#  Direct unit checks on the parser (cheap, isolated)
# ---------------------------------------------------------------------- #

def test_parse_subquestions_accepts_clean_json():
    out = AgenticResearchService._parse_subquestions(VALID_DECOMPOSER_JSON)
    assert isinstance(out, list)
    assert 3 <= len(out) <= 5
    assert all(isinstance(s, str) for s in out)


def test_parse_subquestions_rejects_non_json():
    assert AgenticResearchService._parse_subquestions("not json") is None
    assert AgenticResearchService._parse_subquestions("") is None
    assert AgenticResearchService._parse_subquestions(None) is None


def test_parse_subquestions_rejects_too_few_items():
    bad = '{"sub_questions": ["only one"]}'
    assert AgenticResearchService._parse_subquestions(bad) is None


def test_parse_subquestions_handles_markdown_fence():
    fenced = (
        "```json\n"
        + VALID_DECOMPOSER_JSON
        + "\n```"
    )
    out = AgenticResearchService._parse_subquestions(fenced)
    assert isinstance(out, list) and len(out) >= 3
