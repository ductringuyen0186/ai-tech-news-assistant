"""
Backfill AI summaries for existing articles.

Walks the configured SQLite database, finds every article that does not yet
have an AI summary (`summary_generated = FALSE` or empty/NULL summary), and
runs each through SummarizationOrchestrator -> SummarizationService -> Ollama.

Usage (from the backend/ directory):

    # Make sure Ollama is running locally and the model is pulled, e.g.:
    #   ollama serve
    #   ollama pull llama3.2:1b

    # Backfill in batches of 50, default limit 1000:
    python scripts/backfill_summaries.py

    # Tighter run for a smoke test:
    python scripts/backfill_summaries.py --limit 5 --batch 5

    # Point at a specific DB:
    python scripts/backfill_summaries.py --db ./news.db

Exit codes:
    0 - all articles processed (or none pending)
    1 - one or more articles failed during processing
    2 - infrastructure error (Ollama unreachable, DB missing, etc.)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure src/ is importable when run from backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from src.repositories.article_repository import ArticleRepository  # noqa: E402
from src.services.summarization_orchestrator import (  # noqa: E402
    SummarizationOrchestrator,
)
from src.services.summarization_service import SummarizationService  # noqa: E402


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Backfill AI summaries for unsummarized articles."
    )
    p.add_argument(
        "--db",
        default=None,
        help="SQLite DB path. Defaults to settings.sqlite_database_path.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max total articles to process across all batches (default 1000).",
    )
    p.add_argument(
        "--batch",
        type=int,
        default=50,
        help="Max articles per batch / run_pending() call (default 50).",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Articles to summarize in parallel per batch (default 2).",
    )
    p.add_argument(
        "--max-summary-length",
        type=int,
        default=200,
        help="Target summary length in words (default 200).",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose / DEBUG logging.",
    )
    return p


async def _run(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )
    log = logging.getLogger("backfill")

    # Build repo + service explicitly so we can verify Ollama before doing work.
    repo = ArticleRepository(args.db) if args.db else None
    service = SummarizationService()

    log.info("Ollama: host=%s model=%s", service.base_url, service.model)
    health = await service.health_check()
    log.info("Ollama health: %s", health.get("status"))

    if health.get("status") == "unhealthy":
        log.error("Ollama is not reachable. Start it with `ollama serve`.")
        return 2
    if not health.get("model_loaded"):
        log.error(
            "Model %s is not pulled. Run: ollama pull %s",
            service.model,
            service.model,
        )
        return 2

    orchestrator = SummarizationOrchestrator(
        repository=repo,
        service=service,
        max_summary_length=args.max_summary_length,
        concurrency=args.concurrency,
    )

    totals = {"requested": 0, "summarized": 0, "skipped_short": 0, "failed": 0}
    processed = 0

    while processed < args.limit:
        room = args.limit - processed
        batch_size = min(args.batch, room)
        log.info("Running batch (size=%d, processed_so_far=%d)", batch_size, processed)

        result = await orchestrator.run_pending(limit=batch_size)

        for k in totals:
            totals[k] += getattr(result, k, 0)
        processed += result.requested

        if result.requested == 0:
            log.info("No more pending articles. Stopping.")
            break

        # Show first few errors per batch for quick triage
        for err in result.errors[:3]:
            log.warning("err: %s", err)

    log.info("---- Backfill summary ----")
    for k, v in totals.items():
        log.info("  %s: %d", k, v)

    return 0 if totals["failed"] == 0 else 1


def main() -> int:
    args = _build_arg_parser().parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
