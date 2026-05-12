"""
Saved Research Models
=====================

Pydantic models for the M3.M5 saved-research feature. A saved research
record is a completed research report (markdown) plus the originating
question and any structured sources collected during the run. Sources
are stored as JSON text in the database; the API surface deals in native
lists of dicts so frontend code never has to round-trip JSON itself.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SavedResearchCreate(BaseModel):
    """Request body for POST /api/saved-research."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Originating research question",
    )
    report_md: str = Field(
        ...,
        min_length=1,
        description="Final research report as markdown",
    )
    sources: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description=(
            "Structured sources used in the report. Empty list allowed when "
            "the frontend cannot easily extract structured sources."
        ),
    )


class SavedResearchRead(BaseModel):
    """Full saved-research record returned by POST / GET-by-id."""

    id: int
    question: str
    report_md: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str

    model_config = {"from_attributes": True}


class SavedResearchListItem(BaseModel):
    """Lightweight list-view row returned by GET /api/saved-research.

    Excludes the (potentially large) ``report_md`` and ``sources`` fields
    so the list endpoint stays cheap to hydrate even with 100 rows.
    """

    id: int
    question: str
    created_at: str

    model_config = {"from_attributes": True}
