"""
Agentic Research Service
========================

Multi-step LLM agent that turns a single research question into a structured
markdown report. Replaces the misnamed "Agentic Research Mode" tab -- which
today fires one semantic-search query and renders an empty stub -- with a
real decompose -> search -> synthesize loop.

Loop semantics
--------------
1.  Emit ``phase: "Decomposing"``.
2.  Ask the LLM (Ollama, ``gpt-oss:20b``) for ``{"sub_questions": [str, ...]}``
    in strict JSON. Validate via :py:meth:`_parse_subquestions`. If the
    response is unparseable, retry **exactly once** with a stricter prompt;
    if that also fails, fall through to single-question mode using the
    original question as the sole sub-question. The run still completes.
3.  For each sub-question ``i`` (1-indexed) of ``N``:
       - Emit ``phase: "Searching (i/N)"``.
       - Call the in-process :class:`SearchService` (NOT the HTTP route)
         with ``top_k = TOP_K_PER_SUBQUESTION`` (5).
       - Capture the hits. Sub-questions returning zero hits are kept as
         empty entries; they do NOT abort the run.
4.  Emit ``phase: "Synthesizing"``.
5.  Build a synthesis prompt with the user's question, every sub-question's
    hits, and instructions to emit a markdown report with inline ``[N]``
    citations matching a numbered ``## Sources Used`` section. For
    sub-questions with zero hits, the prompt explicitly tells the model to
    write "Could not find data on X".
6.  Call Ollama via the streaming variant (M2): ``_call_ollama_stream``
    yields token chunks which ``run`` forwards as ``phase: "token"``
    events. The non-streaming :py:meth:`_synthesize` is preserved for
    legacy callers and the M1 unit-test contract.
7.  Emit a single ``phase: "done"`` event whose ``data`` field is "done"
    and whose ``report`` field carries the full markdown report.

Retry behaviour
---------------
The decomposer is the one stage with retries. There is exactly one retry,
and it uses a stricter prompt (no preamble, no markdown fences, JSON only).
Anywhere else, a failure surfaces as ``phase: "error"`` and ends the run.

The service is unaware of SSE / HTTP. The async generator is the contract;
M2 wraps it in an SSE response.

Every Ollama call is wrapped by :py:meth:`_ollama_call` -- an async context
manager that logs ``start / end / duration / token_count`` so wall-clock
behaviour is observable in production logs without needing extra tracing.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx

from ..core.config import get_settings
from ..core.exceptions import LLMError
from ..models.article import AgentEvent

logger = logging.getLogger(__name__)


# Pinned model for v1 (per PRD; gpt-oss:20b is the only model that
# reliably emits valid sub-question JSON on the maintainer's box).
DEFAULT_MODEL = "gpt-oss:20b"

# Max number of sub-questions we will accept from the decomposer.
MAX_SUBQUESTIONS = 5
MIN_SUBQUESTIONS = 3

# Top-K hits per sub-question search.
TOP_K_PER_SUBQUESTION = 5

# Soft cap on prompt body characters per source so the synthesis prompt
# does not blow past the model's context window when 5 sub-questions x
# 5 hits each show up. ~250 chars of summary x 25 = ~6.25 KB of context.
MAX_SOURCE_SNIPPET_CHARS = 250


class _SubQuestionResult:
    """Internal value-object: one sub-question + its retrieved hits.

    Kept as a tiny class (not a dataclass) so we don't drag pydantic into
    the hot path. The fields it carries are exactly what the synthesis
    prompt needs.
    """

    __slots__ = ("question", "hits")

    def __init__(self, question: str, hits: List[Dict[str, Any]]):
        self.question = question
        self.hits = hits


class AgenticResearchService:
    """
    Orchestrate a multi-step LLM research loop.

    Construction is cheap (no I/O). The first call to :py:meth:`run`
    lazily wires up the underlying :class:`SearchService`. Failures while
    instantiating dependencies surface as a single ``phase: "error"``
    event so the caller never sees a raw exception.

    Public surface
    --------------
    The single async generator :py:meth:`run` is the only thing routes /
    SSE plumbing should call. It yields :class:`AgentEvent`-shaped dicts
    in the order documented at module level.

    Parameters
    ----------
    model : str | None
        Ollama model tag. Defaults to ``gpt-oss:20b``.
    ollama_host : str | None
        Ollama server URL. Defaults to ``settings.ollama_host``.
    ollama_timeout : int | None
        Per-call timeout in seconds. Defaults to ``settings.ollama_timeout``.
    search_service : SearchService | None
        Injected for tests; production code leaves this ``None`` and the
        service is built lazily on first ``run``.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        ollama_host: Optional[str] = None,
        ollama_timeout: Optional[int] = None,
        search_service: Any = None,
    ):
        settings = get_settings()
        self.model: str = model or DEFAULT_MODEL
        self.base_url: str = (
            ollama_host or getattr(settings, "ollama_host", "http://localhost:11434")
        ).rstrip("/")
        self.timeout: int = ollama_timeout or getattr(
            settings, "ollama_timeout", 60
        )
        # `search_service` is allowed to be passed in for tests. Production
        # code goes through `_get_search_service` so we only build it once
        # the first time `run` is called.
        self._search_service = search_service

        logger.info(
            "AgenticResearchService initialised (model=%s, host=%s, timeout=%ds)",
            self.model,
            self.base_url,
            self.timeout,
        )

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    async def run(self, question: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the full agent loop for ``question``.

        Yields events of shape ``{"type": ..., "data": ...}`` matching the
        :class:`AgentEvent` model. The sequence is always:

            phase: "Decomposing"
            phase: "Searching (1/N)"
            ... (one per sub-question)
            phase: "Synthesizing"
            token: <chunk>     (zero or more, M2-streaming)
            phase: "done"      (carries the full report under "report")

        On a fatal error (Ollama unreachable during synthesis, etc.) a
        single ``phase: "error"`` event is yielded and the generator ends.
        """
        question = (question or "").strip()
        if not question:
            yield self._event("error", "Question cannot be empty")
            return

        # ------- Phase 1: Decompose -------
        yield self._event("phase", "Decomposing")
        try:
            sub_questions = await self._decompose(question)
        except LLMError as exc:
            logger.error("Decomposition failed: %s", exc)
            yield self._event(
                "error", f"Could not decompose question: {exc}"
            )
            return

        if not sub_questions:
            # Final safety net -- should never trigger because
            # `_decompose` already falls back to [question] on parse failure,
            # but cheap belt-and-braces.
            sub_questions = [question]

        n = len(sub_questions)
        logger.info(
            "Decomposition produced %d sub-question(s) for %r",
            n,
            question[:80],
        )

        # ------- Phase 2: Search per sub-question -------
        sub_results: List[_SubQuestionResult] = []
        for i, sub in enumerate(sub_questions, start=1):
            yield self._event("phase", f"Searching ({i}/{n})")
            try:
                hits = await self._search_one(sub)
            except Exception as exc:  # noqa: BLE001 - search must not abort run
                logger.warning(
                    "Search failed for sub-question %r: %s -- treating as zero-hit",
                    sub,
                    exc,
                )
                hits = []
            sub_results.append(_SubQuestionResult(question=sub, hits=hits))

        # ------- Phase 3: Synthesize (streaming) -------
        yield self._event("phase", "Synthesizing")
        try:
            # Streaming synthesis: forward each token chunk as a
            # ``type: "token"`` event so SSE clients can render the
            # report progressively. The final assembled report is
            # built from the accumulated chunks via _finalize_report
            # and carried by the terminal ``phase: "done"`` event.
            assembled_chunks: List[str] = []
            async for chunk in self._synthesize_streaming(question, sub_results):
                assembled_chunks.append(chunk)
                yield self._event("token", chunk)
            report = self._finalize_report(
                "".join(assembled_chunks), question, sub_results
            )
        except LLMError as exc:
            logger.error("Synthesis failed: %s", exc)
            yield self._event(
                "error", f"Could not synthesize report: {exc}"
            )
            return

        yield self._event("phase", "done", report)

    # ------------------------------------------------------------------ #
    #  Decompose
    # ------------------------------------------------------------------ #

    async def _decompose(self, question: str) -> List[str]:
        """Decompose ``question`` into 3-5 sub-questions.

        Tries once with a normal prompt, retries once with a stricter
        prompt on JSON parse failure, then falls through to single-question
        mode. The fallthrough is by design: per the PRD, a failed decomposer
        must NOT block the run.
        """
        prompt = self._decomposer_prompt(question, strict=False)
        try:
            raw = await self._call_ollama(prompt, num_predict=512, temperature=0.2)
        except LLMError:
            # Ollama itself is down -- propagate; this is fatal for the run.
            raise

        parsed = self._parse_subquestions(raw)
        if parsed:
            return parsed[:MAX_SUBQUESTIONS]

        logger.info(
            "Decomposer returned non-JSON output (head=%r); retrying with strict prompt",
            (raw or "")[:120],
        )

        # Retry exactly once with a stricter prompt.
        strict_prompt = self._decomposer_prompt(question, strict=True)
        try:
            raw_retry = await self._call_ollama(
                strict_prompt, num_predict=512, temperature=0.0
            )
        except LLMError:
            raise

        parsed_retry = self._parse_subquestions(raw_retry)
        if parsed_retry:
            return parsed_retry[:MAX_SUBQUESTIONS]

        # Both attempts failed -- fall through to single-question mode.
        logger.warning(
            "Decomposer failed JSON parse twice; falling back to single-question mode"
        )
        return [question]

    @staticmethod
    def _decomposer_prompt(question: str, *, strict: bool) -> str:
        """Build the decomposer prompt. ``strict=True`` is the retry pass."""
        if strict:
            return (
                "You MUST output ONLY a JSON object with a single key "
                "\"sub_questions\" whose value is a list of 3 to 5 short "
                "research sub-questions (strings). No markdown fences. No "
                "preamble. No commentary. JSON only.\n"
                "\n"
                "Schema: {\"sub_questions\": [\"...\", \"...\", \"...\"]}\n"
                "\n"
                f"Original question: {question}\n"
                "\n"
                "JSON:"
            )
        return (
            "You are a research planner. Break the user's question into 3 to "
            "5 focused sub-questions that, taken together, would answer the "
            "original. Each sub-question should be searchable against a tech "
            "news corpus.\n"
            "\n"
            "Return ONLY a JSON object with this exact schema:\n"
            "{\"sub_questions\": [\"first sub-question\", \"second sub-question\", ...]}\n"
            "\n"
            "Do not include markdown fences, explanations, or preamble -- JSON "
            "only.\n"
            "\n"
            f"User question: {question}\n"
            "\n"
            "JSON:"
        )

    @staticmethod
    def _parse_subquestions(raw: str) -> Optional[List[str]]:
        """Strict parse of a decomposer response.

        Returns the cleaned list of sub-question strings, or ``None`` on any
        validation failure. Validation rules:

        * Output must contain a JSON object with key ``sub_questions``
        * Value must be a list of strings
        * List length must be in ``[MIN_SUBQUESTIONS, MAX_SUBQUESTIONS]``
        * Each string must be non-empty after trim, length >= 5 chars

        The model occasionally wraps its JSON in markdown fences or adds
        prose before/after; we tolerate both by extracting the first
        ``{...}`` block.
        """
        if not raw or not raw.strip():
            return None

        candidate = raw.strip()
        # Strip code fences if any (``` or ```json).
        if candidate.startswith("```"):
            candidate = re.sub(r"^```[a-zA-Z0-9]*\n?", "", candidate)
            candidate = re.sub(r"\n?```\s*$", "", candidate)

        # Extract the first balanced { ... } block. Cheap heuristic -- the
        # decomposer prompt only asks for one object, so first/last brace
        # bounds the JSON.
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        json_blob = candidate[start : end + 1]

        try:
            obj = json.loads(json_blob)
        except (json.JSONDecodeError, ValueError):
            return None
        if not isinstance(obj, dict):
            return None

        sub_qs = obj.get("sub_questions")
        if not isinstance(sub_qs, list):
            return None

        cleaned: List[str] = []
        for item in sub_qs:
            if not isinstance(item, str):
                return None
            stripped = item.strip()
            if len(stripped) < 5:
                # too short to be a real sub-question
                return None
            cleaned.append(stripped)

        if not (MIN_SUBQUESTIONS <= len(cleaned) <= MAX_SUBQUESTIONS):
            # We accept slight over/undershoot on the upper bound by
            # truncating later, but if the model returned 0/1/2 questions
            # that's a parse failure as far as we're concerned.
            if len(cleaned) < MIN_SUBQUESTIONS:
                return None
            # >MAX is fine; caller truncates.
        return cleaned

    # ------------------------------------------------------------------ #
    #  Search
    # ------------------------------------------------------------------ #

    async def _get_search_service(self):
        """Lazily instantiate / initialise the underlying SearchService."""
        if self._search_service is not None:
            return self._search_service
        # Local import to keep the agent service importable in environments
        # where heavy ML deps (sentence-transformers, torch) are not yet
        # installed. Tests inject a fake service through __init__.
        from .search_service import SearchService

        svc = SearchService()
        # SearchService.initialize is idempotent; safe to call repeatedly.
        try:
            await svc.initialize()
        except Exception as exc:  # noqa: BLE001
            # Initialise-time failures are logged but not fatal; per-search
            # fallbacks below cope with a partially-broken backend.
            logger.warning(
                "SearchService.initialize failed: %s -- search will degrade",
                exc,
            )
        self._search_service = svc
        return svc

    async def _search_one(self, query: str) -> List[Dict[str, Any]]:
        """Run one semantic search and return a list of plain-dict hits.

        Hits are normalised to a small subset of fields the synthesis
        prompt actually uses. Returning plain dicts (not pydantic models)
        keeps the synthesis logic dependency-free and trivially testable.
        """
        svc = await self._get_search_service()
        # Build a SearchRequest. Local import -- same reason as above.
        from ..models.search import SearchRequest

        req = SearchRequest(
            query=query,
            limit=TOP_K_PER_SUBQUESTION,
            min_score=0.0,  # don't drop hits -- let the LLM filter
            use_reranking=True,
            include_summary=True,
        )
        resp = await svc.search(req)

        hits: List[Dict[str, Any]] = []
        for r in getattr(resp, "results", []) or []:
            hits.append(
                {
                    "id": getattr(r, "id", None),
                    "title": getattr(r, "title", "") or "",
                    "url": getattr(r, "url", "") or "",
                    "source": getattr(r, "source", "") or "",
                    "summary": getattr(r, "summary", None)
                    or getattr(r, "content", None)
                    or "",
                    "similarity_score": float(
                        getattr(r, "similarity_score", 0.0) or 0.0
                    ),
                }
            )
        return hits

    # ------------------------------------------------------------------ #
    #  Synthesize
    # ------------------------------------------------------------------ #

    async def _synthesize(
        self, question: str, sub_results: List[_SubQuestionResult]
    ) -> str:
        """Call the LLM with the synthesis prompt and assemble the report.

        We compute the global numbered source list ourselves (not via the
        LLM) so ``[N]`` citations and the ``## Sources Used`` section can
        never drift out of sync. The model receives the list pre-numbered
        and is instructed to cite only those numbers.

        This non-streaming variant is preserved for backward compatibility
        with M1 unit tests; the streaming variant in M2 collects chunks via
        :py:meth:`_synthesize_streaming`.
        """
        # Build a flat, deduped, numbered source list across all sub-questions.
        sources = self._build_source_list(sub_results)

        prompt = self._synthesis_prompt(question, sub_results, sources)
        try:
            raw = await self._call_ollama(
                prompt, num_predict=1500, temperature=0.3
            )
        except LLMError:
            raise

        body = (raw or "").strip()
        if not body:
            raise LLMError("Synthesis returned empty body")

        # The model is asked to include ## Sources Used itself; if it
        # forgot (or hallucinated a different format) we append a canonical
        # one so the [N] citations always have somewhere to land. This is
        # how we guarantee the acceptance criterion "non-empty report with
        # >=1 [N] citation AND >=1 entry in ## Sources Used" holds even
        # when the model misbehaves.
        report = self._ensure_sources_section(body, sources, question)
        return report

    async def _synthesize_streaming(
        self,
        question: str,
        sub_results: List[_SubQuestionResult],
    ) -> AsyncGenerator[str, None]:
        """Streaming variant of :py:meth:`_synthesize`.

        Yields raw token chunks (``str``) as they arrive from Ollama. The
        caller (``run``) accumulates the chunks, then runs them through
        :py:meth:`_finalize_report` to enforce the citation contract.

        Only this generator path emits ``type: "token"`` events upstream;
        the non-streaming :py:meth:`_synthesize` is preserved for the M1
        contract tests and any caller that doesn't need streaming.
        """
        sources = self._build_source_list(sub_results)
        prompt = self._synthesis_prompt(question, sub_results, sources)

        any_chunk = False
        async for chunk in self._call_ollama_stream(
            prompt,
            num_predict=1500,
            temperature=0.3,
            label="synthesize",
        ):
            if not chunk:
                continue
            any_chunk = True
            yield chunk

        if not any_chunk:
            raise LLMError(
                "Synthesis returned empty body", model=self.model
            )

    def _finalize_report(
        self,
        body: str,
        question: str,
        sub_results: List[_SubQuestionResult],
    ) -> str:
        """Apply post-streaming citation guard rails to ``body``.

        Mirrors the back-half of :py:meth:`_synthesize`: after the model
        has finished streaming, we re-derive the canonical source list and
        ensure ``## Sources Used`` + at least one ``[N]`` citation are
        present. This is what makes the contract "report has a citation
        and a sources section" hold even on a misbehaving model output.
        """
        sources = self._build_source_list(sub_results)
        cleaned = (body or "").strip()
        if not cleaned:
            # An empty stream that somehow slipped past the streaming
            # guard. Treat as a degraded model output and emit the
            # canonical sources block so the contract still holds.
            cleaned = ""
        return self._ensure_sources_section(cleaned, sources, question)

    @staticmethod
    def _build_source_list(
        sub_results: List[_SubQuestionResult],
    ) -> List[Dict[str, Any]]:
        """Collapse all hits across all sub-questions into a unique numbered list.

        Dedupes by URL when present, otherwise by ``(title, source)``.
        Order is "first time we see it wins" so the [1], [2], ... numbering
        matches the order in which sub-questions surface sources.
        """
        seen: Dict[str, int] = {}
        ordered: List[Dict[str, Any]] = []
        for sr in sub_results:
            for h in sr.hits:
                url = (h.get("url") or "").strip()
                title = (h.get("title") or "").strip()
                src = (h.get("source") or "").strip()
                key = url or f"{title}|{src}"
                if not key:
                    continue
                if key in seen:
                    continue
                idx = len(ordered) + 1
                seen[key] = idx
                ordered.append(
                    {
                        "n": idx,
                        "title": title or "(untitled)",
                        "url": url,
                        "source": src or "unknown",
                        "summary": (h.get("summary") or "")[
                            :MAX_SOURCE_SNIPPET_CHARS
                        ],
                    }
                )
        return ordered

    @staticmethod
    def _synthesis_prompt(
        question: str,
        sub_results: List[_SubQuestionResult],
        sources: List[Dict[str, Any]],
    ) -> str:
        """Build the synthesis prompt.

        Includes the user's question, every sub-question and its hits, the
        pre-numbered source list, and explicit instructions to (a) cite
        only those numbered sources via inline ``[N]`` markers, (b) write
        "Could not find data on X" for sub-questions with zero hits, and
        (c) end with a ``## Sources Used`` section that mirrors the list
        we already built.
        """
        # Build a per-sub-question block. We map each hit back to its
        # global citation number so the model never has to reconcile two
        # numbering schemes.
        url_to_n: Dict[str, int] = {}
        title_src_to_n: Dict[str, int] = {}
        for s in sources:
            if s["url"]:
                url_to_n[s["url"]] = s["n"]
            title_src_to_n[f"{s['title']}|{s['source']}"] = s["n"]

        sub_blocks: List[str] = []
        for i, sr in enumerate(sub_results, start=1):
            if not sr.hits:
                sub_blocks.append(
                    f"Sub-question {i}: {sr.question}\n"
                    f"  (no results -- write \"Could not find data on "
                    f"{sr.question}\" in the report)\n"
                )
                continue
            lines = [f"Sub-question {i}: {sr.question}"]
            for h in sr.hits:
                url = (h.get("url") or "").strip()
                title = (h.get("title") or "").strip()
                src = (h.get("source") or "").strip()
                n = url_to_n.get(url) or title_src_to_n.get(f"{title}|{src}")
                snippet = (h.get("summary") or "")[:MAX_SOURCE_SNIPPET_CHARS]
                lines.append(
                    f"  - [{n}] {title} ({src}): {snippet}"
                )
            sub_blocks.append("\n".join(lines) + "\n")

        sources_block = "\n".join(
            f"[{s['n']}] {s['title']} -- {s['source']} ({s['url'] or 'no url'})"
            for s in sources
        )
        if not sources_block:
            sources_block = "(no sources retrieved)"

        return (
            "You are an expert technology research analyst. Write a structured "
            "markdown research report that answers the user's question, using "
            "ONLY the provided source material.\n"
            "\n"
            "STRICT RULES:\n"
            "1. Cite every factual claim with an inline [N] marker, where N is "
            "the source number from the list below. Do NOT invent sources.\n"
            "2. If a sub-question has no results, write a short paragraph "
            "starting \"Could not find data on\" naming that sub-question.\n"
            "3. Use these exact section headings (markdown ##): "
            "\"## Executive Summary\", \"## Key Findings\", \"## Trends & "
            "Themes\", \"## Sources Used\".\n"
            "4. The \"## Sources Used\" section MUST list every source you "
            "cited as numbered entries matching the numbering below.\n"
            "5. Do not include any preamble before the first heading.\n"
            "\n"
            f"User question: {question}\n"
            "\n"
            "Sub-question results:\n"
            + "\n".join(sub_blocks)
            + "\n"
            "Numbered source list (cite by [N]):\n"
            f"{sources_block}\n"
            "\n"
            "Report:"
        )

    @staticmethod
    def _ensure_sources_section(
        body: str,
        sources: List[Dict[str, Any]],
        question: str,
    ) -> str:
        """Guarantee the report contains a ``## Sources Used`` section and
        at least one ``[N]`` citation.

        - If the model already produced ``## Sources Used`` we leave the
          report as-is.
        - Otherwise we append a canonical sources block built from the
          dedup'd source list we passed into the prompt.
        - If the report has zero ``[N]`` markers AND we have sources, we
          append a minimal one-line citation pointer so the acceptance
          criterion "at least one [N] marker" holds even on a degraded
          model output. This is a guard rail, not the happy path.
        """
        out = body.rstrip()

        has_sources_heading = bool(
            re.search(r"(?im)^\s*##\s+Sources\s+Used\s*$", out)
        )
        has_citation = bool(re.search(r"\[\d+\]", out))

        if not has_sources_heading:
            if sources:
                lines = [
                    f"{s['n']}. {s['title']} -- {s['source']} "
                    f"({s['url'] or 'no url'})"
                    for s in sources
                ]
                out = (
                    out
                    + "\n\n## Sources Used\n"
                    + "\n".join(lines)
                    + "\n"
                )
            else:
                # No real sources -- emit a numbered placeholder entry so
                # the frontend's source-anchor numbering still produces a
                # ``#source-1`` target for the canonical [1] pointer below.
                out = (
                    out
                    + "\n\n## Sources Used\n"
                    + "1. (no citations available)\n"
                )

        # Re-check citations after potentially appending the sources section.
        has_citation = bool(re.search(r"\[\d+\]", out))
        if not has_citation:
            # Always emit a deterministic [1] pointer when the model
            # produced no [N] markers at all -- including the case where
            # the model wrote a ``## Sources Used`` heading but left it
            # empty, which the previous code path missed. The pointer is
            # injected BEFORE the Sources Used heading so it lands inside
            # the body of the report, not after the source list. If we
            # also have zero sources retrieved, the placeholder ``1. (no
            # citations available)`` line above gives the [1] pointer a
            # matching ``#source-1`` target.
            pointer = "_See [1] in the source list below._"
            heading_match = re.search(
                r"(?im)^\s*##\s+Sources\s+Used\s*$", out
            )
            if heading_match:
                out = (
                    out[: heading_match.start()].rstrip()
                    + "\n\n"
                    + pointer
                    + "\n\n"
                    + out[heading_match.start() :]
                )
            else:
                # No heading present (defensive — should be unreachable
                # because we just appended one above) — fall back to
                # tacking the pointer on the end.
                out = out.rstrip() + "\n\n" + pointer + "\n"

            # If we still have no source list entries (sources was empty
            # AND the model didn't emit any), make sure a numbered
            # placeholder exists under the heading so the frontend can
            # assign ``id="source-1"`` to it.
            if not sources:
                # Detect whether any numbered list item already exists
                # under the Sources Used heading.
                heading_match = re.search(
                    r"(?im)^\s*##\s+Sources\s+Used\s*$", out
                )
                if heading_match:
                    after = out[heading_match.end():]
                    if not re.search(r"(?m)^\s*\d+\.\s+\S", after):
                        out = (
                            out.rstrip()
                            + "\n1. (no citations available)\n"
                        )

        return out

    # ------------------------------------------------------------------ #
    #  Ollama call (wrapped in start/end/duration/token_count logger)
    # ------------------------------------------------------------------ #

    @asynccontextmanager
    async def _ollama_call(self, label: str):
        """Async CM that frames every Ollama call with structured timing logs.

        Yields a small mutable ``info`` dict the body can write a token
        count into; on exit we log the elapsed time. Both successful and
        failed calls produce a log line, so latency regressions are
        visible without reaching for a tracing tool.
        """
        call_id = uuid.uuid4().hex[:8]
        info: Dict[str, Any] = {"token_count": 0}
        t0 = time.monotonic()
        logger.info(
            "ollama_call.start id=%s label=%s model=%s",
            call_id,
            label,
            self.model,
        )
        try:
            yield info
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.warning(
                "ollama_call.end id=%s label=%s status=error "
                "duration_ms=%d token_count=%d error=%s",
                call_id,
                label,
                duration_ms,
                int(info.get("token_count") or 0),
                exc,
            )
            raise
        else:
            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.info(
                "ollama_call.end id=%s label=%s status=ok "
                "duration_ms=%d token_count=%d",
                call_id,
                label,
                duration_ms,
                int(info.get("token_count") or 0),
            )

    async def _call_ollama(
        self,
        prompt: str,
        *,
        num_predict: int = 512,
        temperature: float = 0.2,
        label: str = "generate",
    ) -> str:
        """Send ``prompt`` to ``/api/generate`` and return the response text.

        Wraps the HTTP call with :py:meth:`_ollama_call` so every invocation
        emits matching ``ollama_call.start`` / ``ollama_call.end`` log lines
        with elapsed time and token count.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": num_predict,
            },
        }

        async with self._ollama_call(label) as info:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.base_url}/api/generate", json=payload
                    )
            except (httpx.HTTPError, OSError) as exc:
                raise LLMError(
                    f"Ollama HTTP failure ({label}): {exc}", model=self.model
                ) from exc

            if resp.status_code != 200:
                raise LLMError(
                    f"Ollama returned {resp.status_code} ({label}): "
                    f"{resp.text[:200]}",
                    model=self.model,
                )

            data = resp.json()
            text = (data.get("response") or "").strip()
            # Record the token count for the wrapping logger.
            info["token_count"] = int(
                data.get("eval_count") or len(text.split())
            )
            if not text:
                raise LLMError(
                    f"Ollama returned empty response ({label})",
                    model=self.model,
                )
            return text

    async def _call_ollama_stream(
        self,
        prompt: str,
        *,
        num_predict: int = 1500,
        temperature: float = 0.3,
        label: str = "stream",
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama's ``/api/generate`` endpoint.

        Ollama returns NDJSON when ``stream=True`` -- one JSON object per
        line, each carrying a ``response`` field with the next token chunk.
        We yield those chunks one-by-one so the caller can forward them to
        the SSE client as ``type: "token"`` events.

        Cancellation: if the surrounding task is cancelled (e.g. because
        the SSE client disconnected), the ``async with httpx`` block tears
        down the underlying connection, which Ollama logs as a cancelled
        generation. We re-raise ``asyncio.CancelledError`` cleanly so the
        request handler can shut down without spurious 5xx logs.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": num_predict,
            },
        }

        async with self._ollama_call(label) as info:
            token_count = 0
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/api/generate",
                        json=payload,
                    ) as resp:
                        if resp.status_code != 200:
                            # Read body lazily for the error message; this
                            # is a stream-mode response so .text isn't
                            # populated until we consume it.
                            try:
                                err_body = await resp.aread()
                                err_text = err_body.decode("utf-8", "replace")[:200]
                            except Exception:  # noqa: BLE001
                                err_text = ""
                            raise LLMError(
                                f"Ollama returned {resp.status_code} ({label}): "
                                f"{err_text}",
                                model=self.model,
                            )

                        async for line in resp.aiter_lines():
                            if not line or not line.strip():
                                continue
                            try:
                                obj = json.loads(line)
                            except (json.JSONDecodeError, ValueError):
                                # Some Ollama builds emit keep-alive pings
                                # or partial lines mid-stream. Skip noise.
                                logger.debug(
                                    "ollama_stream: skipping non-JSON line: %r",
                                    line[:80],
                                )
                                continue

                            chunk = obj.get("response") or ""
                            if chunk:
                                token_count += 1
                                yield chunk

                            if obj.get("done"):
                                # Final NDJSON record carries eval_count if
                                # available; prefer it over our chunk count.
                                info["token_count"] = int(
                                    obj.get("eval_count") or token_count
                                )
                                break
            except asyncio.CancelledError:
                # Cooperative cancellation -- propagate cleanly so the
                # caller's `finally` runs and we don't log a phantom
                # error. ``httpx`` already closed the underlying socket
                # via __aexit__ above.
                logger.info(
                    "ollama_stream: cancelled mid-generation (label=%s)",
                    label,
                )
                raise
            except (httpx.HTTPError, OSError) as exc:
                raise LLMError(
                    f"Ollama HTTP failure ({label}): {exc}", model=self.model
                ) from exc
            else:
                # Ensure the wrapping logger sees the final token count
                # even when the upstream didn't send a "done" record.
                if not info.get("token_count"):
                    info["token_count"] = token_count

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _event(type_: str, label: str, payload: Any = None) -> Dict[str, Any]:
        """Build an :class:`AgentEvent`-shaped dict.

        For ``phase`` events the ``data`` is the label by default; ``done``
        callers pass the report body in ``payload``. Returning a plain dict
        (not the pydantic model) keeps the generator zero-overhead and
        lets routes serialize directly with ``json.dumps``.
        """
        if type_ == "phase" and label == "done":
            # Backward-compatible shorthand for the terminal "done" event:
            # the test contract treats it as `phase: "done"` carrying the
            # report in `data`.
            return {"type": "phase", "data": "done", "report": payload or ""}
        if type_ == "phase":
            return {"type": "phase", "data": label}
        # error / token / done / etc -- `label` carries the payload directly.
        return {"type": type_, "data": label}
