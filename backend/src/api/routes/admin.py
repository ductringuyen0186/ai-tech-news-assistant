"""
Admin Routes
============

Operator-facing endpoints for manual maintenance.

Currently exposes:
- ``POST /api/admin/retention/run?dry_run=<bool>`` — trigger the retention
  service on demand. Useful for the first prod run (always do
  ``dry_run=true`` first), and as the hook used by the E2E test suite to
  verify retention without waiting for the daily cron.

NOTE: There is no auth in this project. Until M4 lands SSO, admin routes
should be firewalled at the reverse proxy / load balancer (e.g. require a
specific source IP or basic-auth in nginx). The daily cron itself runs
in-process and does not need an auth boundary.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from ...services.retention_service import RetentionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/retention/run")
async def run_retention(
    dry_run: bool = Query(
        default=False,
        description=(
            "If true, log/return what would be deleted without committing. "
            "Recommended for the first call against a fresh DB."
        ),
    ),
) -> Dict[str, Any]:
    """Trigger a retention pass on demand."""
    try:
        service = RetentionService()
        result = service.run(dry_run=dry_run)
        return {"status": "ok", "data": result.to_dict()}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Manual retention run failed")
        raise HTTPException(
            status_code=500,
            detail=f"Retention run failed: {exc}",
        )
