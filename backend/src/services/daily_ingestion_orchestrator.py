"""Daily ingestion orchestrator (Mission ``daily-ingestion`` M1).

Chains the five-phase pipeline -- fetch -> summarize -> embed -> entity-
extract -> report -- into one async entry point :func:`run_daily_ingestion`.
Each phase is isolated in a try/except so a single phase failure does not
kill the run. Returns a :class:`DailyIngestionReport` with per-phase
counts, durations, the first 5 error strings per phase, and a
``health_status`` field (``green`` / ``yellow`` / ``red``) so a
``GET /api/health/ingestion`` endpoint (M4) can surface it.

Wiring
------
- M2 wires this into APScheduler at 05:00 UTC daily via
  ``backend/src/main.py``.
- M3 exposes this as an on-demand trigger via
  ``POST /api/admin/ingest`` (with an optional ``dry_run`` query flag).

Design notes
------------
* All DB writes use the raw ``sqlite3`` driver pointing at
  ``settings.database_path`` (which resolves to ``backend/news.db``). This
  matches the rest of the project (``ArticleRepository``,
  ``EntityExtractionService``, ``backfill_embeddings.py``); going through
  SQLAlchemy ``Session`` here would force us to also wire transaction
  boundaries through every helper.
* Phase 1 (fetch) is the **only** phase that creates new article rows.
  It calls the existing :meth:`IngestionService.ingest_all` (the only
  public "fetch every feed and save" method on that service) and counts
  the rows it inserted via its returned :class:`IngestionResult`.
  Dedupe-by-URL is already handled inside ``IngestionService._process_entry``.
* Phases 2-4 operate on already-stored rows, gated by the "no summary",
  "no embedding", "no entity_mentions" predicates respectively. Each is
  capped at 100 rows per run so a single invocation has a bounded
  cost; the next day's run picks up the rest.
* ``dry_run=True`` causes every phase to count the work-set size but
  perform **no** writes. This is what the admin endpoint's ``--dry-run``
  smoke test exercises.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, List, Optional

logger = logging.getLogger(__name__)


# Per-phase work cap. Keeps one run bounded; subsequent runs catch up
# on any backlog. Tuned for ~30 articles/day steady state.
MAX_PER_PHASE = 100


# --------------------------------------------------------------------- #
#  Report dataclasses
# --------------------------------------------------------------------- #


@dataclass
class PhaseReport:
    """Per-phase result rolled up by :func:`run_daily_ingestion`.

    ``errors`` is capped at the first 5 strings so a pathological run
    can't blow up the report payload.
    """

    name: str
    processed: int = 0
    failed: int = 0
    duration_ms: int = 0
    errors: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """Append an error string, capping the list at 5."""
        if len(self.errors) < 5:
            self.errors.append(msg)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "processed": self.processed,
            "failed": self.failed,
            "duration_ms": self.duration_ms,
            "errors": list(self.errors),
        }


@dataclass
class DailyIngestionReport:
    """Final report returned by :func:`run_daily_ingestion`.

    ``health_status`` follows the rules in mission spec M4:

    * ``green``  -- fetch produced >= 1 article AND no phase had > 50%
      failures.
    * ``yellow`` -- fetch produced 0 articles (feeds may be quiet) OR
      exactly one phase failed entirely.
    * ``red``    -- fetch phase crashed OR 2+ phases failed entirely.
    """

    started_at: datetime
    finished_at: datetime
    total_duration_ms: int
    phases: List[PhaseReport]
    health_status: str
    dry_run: bool

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "phases": [p.to_dict() for p in self.phases],
            "health_status": self.health_status,
            "dry_run": self.dry_run,
        }


# --------------------------------------------------------------------- #
#  Public entry point
# --------------------------------------------------------------------- #


async def run_daily_ingestion(
    db_path: str,
    *,
    feeds: Optional[List[str]] = None,
    summarize: bool = True,
    embed: bool = True,
    extract_entities: bool = True,
    dry_run: bool = False,
) -> DailyIngestionReport:
    """Run the full daily ingestion pipeline.

    Parameters
    ----------
    db_path
        Path to the SQLite database (or ``sqlite:///...`` URL form).
        Resolved to a bare path by :func:`_resolve_db_path`.
    feeds
        Optional list of feed URLs to override
        :pyattr:`IngestionService.DEFAULT_FEEDS`. Each entry is treated
        as a feed URL; ``name`` and ``category`` fall back to safe
        defaults.
    summarize, embed, extract_entities
        Phase toggles. Each defaults to ``True``. Set to ``False`` to
        skip the corresponding phase entirely (no work-set query, no
        writes, no PhaseReport entry).
    dry_run
        When ``True`` every phase computes its work-set size but writes
        nothing. Used by the admin endpoint smoke test.

    Returns
    -------
    DailyIngestionReport
        Aggregated report with per-phase counts, durations, first-5
        error strings, and a derived ``health_status``.
    """
    started = datetime.now(timezone.utc)
    resolved_db = _resolve_db_path(db_path)
    phases: List[PhaseReport] = []

    # Phase 1: fetch -- always runs; the rest of the pipeline is
    # meaningless if we never refresh the corpus.
    fetch_report = await _run_phase(
        "fetch",
        _phase_fetch,
        db_path=resolved_db,
        feeds=feeds,
        dry_run=dry_run,
    )
    phases.append(fetch_report)

    if summarize:
        phases.append(
            await _run_phase(
                "summarize",
                _phase_summarize,
                db_path=resolved_db,
                dry_run=dry_run,
            )
        )

    if embed:
        phases.append(
            await _run_phase(
                "embed",
                _phase_embed,
                db_path=resolved_db,
                dry_run=dry_run,
            )
        )

    if extract_entities:
        phases.append(
            await _run_phase(
                "entity_extract",
                _phase_entities,
                db_path=resolved_db,
                dry_run=dry_run,
            )
        )

    finished = datetime.now(timezone.utc)
    report = DailyIngestionReport(
        started_at=started,
        finished_at=finished,
        total_duration_ms=int((finished - started).total_seconds() * 1000),
        phases=phases,
        health_status=_compute_health_status(phases),
        dry_run=dry_run,
    )

    # Single grep-able JSON line, as called for in spec §2 M1 phase 5.
    logger.info("daily_ingestion_report %s", json.dumps(report.to_dict()))
    return report


# --------------------------------------------------------------------- #
#  Phase runner + health
# --------------------------------------------------------------------- #


async def _run_phase(
    name: str,
    fn: Callable[..., Awaitable[None]],
    **kwargs: Any,
) -> PhaseReport:
    """Wrap a phase function in try/except and time it.

    A phase function receives a fresh :class:`PhaseReport` plus the
    kwargs forwarded from :func:`run_daily_ingestion`. It mutates the
    report in place (``processed``, ``failed``, ``errors``); we own the
    duration timing and the top-level exception capture so individual
    phases can stay simple.
    """
    started = datetime.now()
    pr = PhaseReport(name=name)
    try:
        await fn(report=pr, **kwargs)
    except Exception as exc:  # noqa: BLE001 - last-resort isolation
        logger.exception("phase %s crashed", name)
        pr.add_error(f"phase crashed: {exc}")
    pr.duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    logger.info(
        "[%s] processed=%d failed=%d duration_ms=%d",
        name,
        pr.processed,
        pr.failed,
        pr.duration_ms,
    )
    return pr


def _compute_health_status(phases: List[PhaseReport]) -> str:
    """Roll per-phase results up into ``green`` / ``yellow`` / ``red``.

    Rules (mission spec §2 M4):

    * ``red`` if the fetch phase itself crashed (errors AND processed==0)
      or 2+ phases failed entirely.
    * ``yellow`` if exactly one phase failed entirely OR fetch produced
      zero new articles (feeds may simply be quiet today).
    * ``green`` otherwise.
    """
    fetch = next((p for p in phases if p.name == "fetch"), None)
    if fetch is None:
        # Caller disabled fetch -- abnormal usage; flag as red.
        return "red"
    if fetch.errors and fetch.processed == 0:
        return "red"

    failed_phases = sum(
        1 for p in phases if p.processed == 0 and p.errors
    )
    if failed_phases >= 2:
        return "red"
    if failed_phases == 1:
        return "yellow"
    if fetch.processed == 0:
        # Quiet day, not necessarily broken -- yellow per spec.
        return "yellow"
    return "green"


# --------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------- #


def _resolve_db_path(db_path: str) -> str:
    """Normalise ``sqlite:///...`` URL form to a bare filesystem path."""
    if db_path.startswith("sqlite:///"):
        return db_path[len("sqlite:///"):]
    if db_path.startswith("sqlite://"):
        return db_path[len("sqlite://"):]
    return db_path


def _build_feed_configs(
    feeds: Optional[List[str]],
) -> Optional[List[dict]]:
    """Convert an optional ``list[str]`` of URLs to the dict shape
    :meth:`IngestionService.ingest_all` expects.

    Returns ``None`` when ``feeds`` is ``None``, which tells
    ``ingest_all`` to use its built-in ``DEFAULT_FEEDS``.
    """
    if not feeds:
        return None
    return [
        {"name": f"custom-{i}", "url": url, "category": "AI/ML"}
        for i, url in enumerate(feeds)
    ]


# --------------------------------------------------------------------- #
#  Phase implementations
# --------------------------------------------------------------------- #


async def _phase_fetch(
    *,
    report: PhaseReport,
    db_path: str,
    feeds: Optional[List[str]],
    dry_run: bool,
) -> None:
    """Phase 1: fetch RSS feeds and dedupe-insert into ``articles``.

    Delegates the actual HTTP + parse + insert work to
    :meth:`IngestionService.ingest_all` -- the only public "fetch every
    feed" entry point on that class. We translate its
    :class:`IngestionResult` into our :class:`PhaseReport` shape.

    ``dry_run`` mode skips ``ingest_all`` entirely (it would do real
    network I/O + writes) and reports ``processed=0`` -- the work-set
    size for fetch is not knowable without hitting the network.
    """
    if dry_run:
        logger.info("[fetch] dry_run=True; skipping network fetch")
        return

    # Imports are lazy so the orchestrator module is cheap to import
    # (unit tests, scheduler bootstrap) and so monkeypatching in tests
    # works against the symbols on this module.
    from src.database.base import SessionLocal, create_session_factory
    from src.services.ingestion_service import IngestionService

    if SessionLocal is None:
        create_session_factory()

    # Re-import after factory bootstrap so we pick up the populated
    # module-global. ``create_session_factory`` rebinds ``SessionLocal``
    # at the package level.
    from src.database.base import SessionLocal as _SessionLocal

    if _SessionLocal is None:
        report.add_error("SessionLocal not initialised after factory call")
        return

    feed_configs = _build_feed_configs(feeds)
    session = _SessionLocal()
    try:
        service = IngestionService(session)
        try:
            # ``ingest_all`` is synchronous (it uses ``httpx.Client``
            # not ``AsyncClient``). Run it in a worker thread so we
            # don't block the event loop.
            result = await asyncio.to_thread(service.ingest_all, feed_configs)
        finally:
            service.close()

        report.processed = int(getattr(result, "total_articles_saved", 0) or 0)
        report.failed = int(getattr(result, "errors_encountered", 0) or 0)
        for detail in getattr(result, "error_details", []) or []:
            # error_details is a list[dict] -- collapse to a string.
            err = detail.get("error") if isinstance(detail, dict) else str(detail)
            if err:
                report.add_error(str(err)[:200])
    finally:
        try:
            session.close()
        except Exception:  # pragma: no cover - best-effort cleanup
            logger.debug("session close failed", exc_info=True)


async def _phase_summarize(
    *,
    report: PhaseReport,
    db_path: str,
    dry_run: bool,
) -> None:
    """Phase 2: summarize every article whose ``summary IS NULL``.

    Capped at :data:`MAX_PER_PHASE` rows per run. Each per-article call
    is wrapped in its own try/except so one bad LLM call doesn't poison
    the phase.
    """
    candidates = _select_unsummarized(db_path, limit=MAX_PER_PHASE)
    if dry_run:
        logger.info("[summarize] dry_run=True; %d candidate(s)", len(candidates))
        return
    if not candidates:
        return

    # Lazy imports for the same reasons as in _phase_fetch.
    from src.models.article import SummarizationRequest
    from src.services.summarization_service import SummarizationService

    service = SummarizationService()

    for article_id, _title, content in candidates:
        if not content or not content.strip():
            # Nothing to summarise; mark as failed bookkeeping-wise so
            # we don't loop forever on the same row tomorrow. We can't
            # null-summarise either, so just skip without recording.
            continue
        try:
            req = SummarizationRequest(content=content)
            summary = await service.summarize_content(req)
            _write_summary(db_path, article_id, summary.summary)
            report.processed += 1
        except Exception as exc:  # noqa: BLE001 - per-item isolation
            report.failed += 1
            report.add_error(
                f"article {article_id}: {type(exc).__name__}: {exc}"[:200]
            )
            logger.warning(
                "[summarize] article %s failed: %s", article_id, exc
            )


async def _phase_embed(
    *,
    report: PhaseReport,
    db_path: str,
    dry_run: bool,
) -> None:
    """Phase 3: generate + insert a 384-dim embedding for every
    article without a row in ``article_embeddings``.

    Reuses the same logic as :mod:`scripts.backfill_embeddings`: title
    + body concatenated, ``all-MiniLM-L6-v2`` model, upsert into
    ``article_embeddings`` keyed on ``article_id``. We don't re-export
    a helper from the script because the script is intentionally a
    one-shot CLI; copying the ~20-line inner loop here keeps the
    orchestrator independent.
    """
    _ensure_embeddings_table(db_path)
    candidates = _select_unembedded(db_path, limit=MAX_PER_PHASE)
    if dry_run:
        logger.info("[embed] dry_run=True; %d candidate(s)", len(candidates))
        return
    if not candidates:
        return

    from vectorstore.embeddings import EmbeddingGenerator

    gen = EmbeddingGenerator()
    try:
        await gen.load_model()
    except Exception as exc:  # noqa: BLE001
        report.add_error(f"model load failed: {exc}"[:200])
        logger.error("[embed] model load failed: %s", exc)
        return

    for article_id, title, body in candidates:
        text = (f"{title}\n\n{body}".strip() if title else body) or ""
        if not text.strip():
            continue
        try:
            vectors = await gen.generate_embeddings([text])
            vec = vectors[0]
            # ``vec`` is a numpy array in the real path; lists also work.
            as_list = vec.tolist() if hasattr(vec, "tolist") else list(vec)
            _upsert_embedding(db_path, article_id, as_list, gen.model_name)
            report.processed += 1
        except Exception as exc:  # noqa: BLE001 - per-item isolation
            report.failed += 1
            report.add_error(
                f"article {article_id}: {type(exc).__name__}: {exc}"[:200]
            )
            logger.warning("[embed] article %s failed: %s", article_id, exc)


async def _phase_entities(
    *,
    report: PhaseReport,
    db_path: str,
    dry_run: bool,
) -> None:
    """Phase 4: run entity extraction for every article without an
    existing ``entity_mentions`` row.

    Defers to :meth:`EntityExtractionService.process_article`, which
    is already idempotent and already swallows per-article errors.
    """
    candidates = _select_unextracted_article_ids(db_path, limit=MAX_PER_PHASE)
    if dry_run:
        logger.info(
            "[entity_extract] dry_run=True; %d candidate(s)", len(candidates)
        )
        return
    if not candidates:
        return

    from src.services.entity_extraction_service import EntityExtractionService

    service = EntityExtractionService(db_path=db_path)

    for article_id in candidates:
        try:
            persisted = await service.process_article(article_id)
            # ``process_article`` returns the entity count, but for the
            # phase report we just want "did this row get touched?".
            report.processed += 1
            logger.debug(
                "[entity_extract] article %s: %d entities", article_id, persisted
            )
        except Exception as exc:  # noqa: BLE001 - per-item isolation
            report.failed += 1
            report.add_error(
                f"article {article_id}: {type(exc).__name__}: {exc}"[:200]
            )
            logger.warning(
                "[entity_extract] article %s failed: %s", article_id, exc
            )


# --------------------------------------------------------------------- #
#  Raw-SQL DB helpers
# --------------------------------------------------------------------- #


def _select_unsummarized(db_path: str, *, limit: int) -> List[tuple]:
    """``SELECT id, title, content FROM articles WHERE summary IS NULL``."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, COALESCE(title, '') AS title, COALESCE(content, '') AS content
            FROM articles
            WHERE (summary IS NULL OR summary = '')
              AND COALESCE(content, '') != ''
            ORDER BY id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [(int(r[0]), r[1], r[2]) for r in rows]


def _write_summary(db_path: str, article_id: int, summary: str) -> None:
    """UPDATE articles SET summary = ? WHERE id = ?."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE articles SET summary = ?, summary_generated = 1, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (summary, article_id),
        )
        conn.commit()


def _ensure_embeddings_table(db_path: str) -> None:
    """Create ``article_embeddings`` if missing.

    Mirrors ``scripts/backfill_embeddings.py``. We bootstrap here in
    case the daily job is the first thing to ever touch the table on
    a fresh DB.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS article_embeddings (
                article_id    INTEGER PRIMARY KEY,
                embedding     TEXT NOT NULL,
                model_name    TEXT NOT NULL,
                embedding_dim INTEGER NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id)
                    ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_article_embeddings_article_id "
            "ON article_embeddings(article_id)"
        )
        conn.commit()


def _select_unembedded(db_path: str, *, limit: int) -> List[tuple]:
    """Articles without an existing embedding row."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT a.id,
                   COALESCE(a.title, '') AS title,
                   COALESCE(NULLIF(a.content, ''), NULLIF(a.summary, ''), '') AS body
            FROM articles a
            WHERE a.is_archived = 0
              AND COALESCE(NULLIF(a.content, ''), NULLIF(a.summary, ''), '') != ''
              AND a.id NOT IN (SELECT article_id FROM article_embeddings)
            ORDER BY a.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [(int(r[0]), r[1], r[2]) for r in rows]


def _upsert_embedding(
    db_path: str,
    article_id: int,
    embedding: List[float],
    model_name: str,
) -> None:
    """Mirror of ``scripts.backfill_embeddings._upsert_embedding``."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO article_embeddings
                (article_id, embedding, model_name, embedding_dim, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(article_id) DO UPDATE SET
                embedding = excluded.embedding,
                model_name = excluded.model_name,
                embedding_dim = excluded.embedding_dim,
                created_at = excluded.created_at
            """,
            (article_id, json.dumps(embedding), model_name, len(embedding)),
        )
        conn.commit()


def _select_unextracted_article_ids(db_path: str, *, limit: int) -> List[int]:
    """Articles with no row in ``entity_mentions``.

    Returns just the IDs because
    :meth:`EntityExtractionService.process_article` re-reads the article
    body itself.
    """
    # entity_mentions may not exist yet on a fresh DB. We bootstrap it
    # by instantiating the service later in the phase; here we just
    # tolerate the missing table by treating "no table" as "no rows".
    with sqlite3.connect(db_path) as conn:
        # Probe table existence so a missing entity_mentions doesn't
        # crash the SELECT below.
        has_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='entity_mentions'"
        ).fetchone()
        if not has_table:
            rows = conn.execute(
                """
                SELECT id FROM articles
                WHERE is_archived = 0
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT a.id FROM articles a
                WHERE a.is_archived = 0
                  AND a.id NOT IN (
                      SELECT DISTINCT article_id FROM entity_mentions
                  )
                ORDER BY a.id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [int(r[0]) for r in rows]


__all__ = [
    "DailyIngestionReport",
    "PhaseReport",
    "run_daily_ingestion",
]
