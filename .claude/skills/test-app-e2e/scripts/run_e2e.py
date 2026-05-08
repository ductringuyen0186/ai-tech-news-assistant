"""
Black-box end-to-end test runner for the AI Tech News Assistant.

Talks to the running backend over HTTP and (optionally) checks the running
frontend. Reads no application source code ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â failures here are based purely
on observable behaviour, which is exactly what a real user would experience.

The runner is deliberately tolerant: each test is independent, failures are
captured rather than aborting the run, and every failure includes enough
context (URL, HTTP status, response snippet, exception trace) for an
automated fixer agent to start work without rerunning the test.

Usage:
    python run_e2e.py                                # default: http://127.0.0.1:8000
    python run_e2e.py --backend http://10.0.0.5:8000 --frontend http://localhost:5173
    python run_e2e.py --json                         # machine-readable report
    python run_e2e.py --skip-pipeline                # don't trigger ingest+summarize
    python run_e2e.py --ollama-host http://127.0.0.1:11434

Exit codes:
    0  all tests passed
    1  one or more tests failed (see report)
    2  setup error (couldn't reach backend at all)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------- #
#  Test result types
# ---------------------------------------------------------------------- #

SEVERITY_CRITICAL = "critical"  # backend not reachable, app unusable
SEVERITY_HIGH = "high"          # core feature broken
SEVERITY_MEDIUM = "medium"      # secondary feature broken
SEVERITY_LOW = "low"            # cosmetic / config drift


@dataclass
class TestResult:
    name: str
    category: str          # "infra" | "api" | "pipeline" | "frontend" | "config"
    passed: bool
    severity: str = SEVERITY_MEDIUM
    duration_ms: int = 0
    detail: str = ""
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    suggested_fix_area: Optional[str] = None  # hint for the fixer agent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "severity": self.severity,
            "duration_ms": self.duration_ms,
            "detail": self.detail,
            "request": self.request,
            "response": self.response,
            "suggested_fix_area": self.suggested_fix_area,
        }


# ---------------------------------------------------------------------- #
#  Tiny HTTP client (stdlib only ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no extra deps for the runner)
# ---------------------------------------------------------------------- #

def http_request(
    method: str,
    url: str,
    body: Optional[Any] = None,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Dict[str, str], str]:
    """Return (status, headers, body_text). Never raises on HTTP errors."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req_headers = {"Accept": "application/json"}
    if data is not None:
        req_headers["Content-Type"] = "application/json"
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, dict(exc.headers or {}), body_text
    except urllib.error.URLError as exc:
        return 0, {}, f"URLError: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return 0, {}, f"{type(exc).__name__}: {exc}"


def parse_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


# ---------------------------------------------------------------------- #
#  Test definitions
# ---------------------------------------------------------------------- #

class E2ESuite:
    def __init__(self, backend: str, frontend: Optional[str], ollama: str,
                 skip_pipeline: bool, skip_frontend: bool,
                 include_live_ingest: bool = False):
        self.backend = backend.rstrip("/")
        self.frontend = frontend.rstrip("/") if frontend else None
        self.ollama = ollama.rstrip("/")
        self.skip_pipeline = skip_pipeline
        self.skip_frontend = skip_frontend
        # live_ingest_smoke is opt-in: it hits real RSS feeds and takes
        # 1-5 minutes. Off by default so the standard run stays fast
        # even when --skip-pipeline is not passed.
        self.include_live_ingest = include_live_ingest
        self.results: List[TestResult] = []

    # -------------------------------------------------------------- #
    #  Test runner mechanics
    # -------------------------------------------------------------- #

    def _run(self, name: str, category: str, severity: str,
             fn: Callable[[], Tuple[bool, str, Dict[str, Any], Dict[str, Any], Optional[str]]]) -> TestResult:
        t0 = time.time()
        try:
            passed, detail, request, response, fix_area = fn()
        except Exception as exc:  # noqa: BLE001
            passed = False
            detail = f"Test crashed: {exc}\n{traceback.format_exc()}"
            request, response, fix_area = {}, {}, "test-runner"
        result = TestResult(
            name=name, category=category, passed=passed, severity=severity,
            duration_ms=int((time.time() - t0) * 1000),
            detail=detail, request=request, response=response,
            suggested_fix_area=fix_area,
        )
        self.results.append(result)
        return result

    # -------------------------------------------------------------- #
    #  Individual tests
    # -------------------------------------------------------------- #

    def test_backend_reachable(self):
        def _t():
            url = f"{self.backend}/health"
            status, _, body = http_request("GET", url, timeout=5.0)
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body_snippet": body[:300]}
            if status == 0:
                return False, f"Backend not reachable at {self.backend}: {body}", req, resp, "backend-startup"
            if status >= 500:
                return False, f"Backend returned 5xx on /health: {status}", req, resp, "backend-startup"
            return True, f"Backend reachable (HTTP {status})", req, resp, None
        return self._run("backend_reachable", "infra", SEVERITY_CRITICAL, _t)

    def test_health_payload(self):
        def _t():
            url = f"{self.backend}/health"
            status, _, body = http_request("GET", url)
            data = parse_json(body) or {}
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body": data}
            if status != 200:
                return False, f"/health returned {status}", req, resp, "backend-routes-health"
            if "status" not in data:
                return False, "/health response missing 'status' field", req, resp, "backend-routes-health"
            if data.get("status") not in ("healthy", "degraded", "unhealthy"):
                return False, f"unexpected status value: {data.get('status')}", req, resp, "backend-routes-health"
            return True, f"/health.status = {data.get('status')}", req, resp, None
        return self._run("health_payload", "api", SEVERITY_HIGH, _t)

    def test_news_list_endpoint(self):
        def _t():
            url = f"{self.backend}/api/news/?page=1&page_size=5"
            status, _, body = http_request("GET", url)
            data = parse_json(body) or {}
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body": data}
            if status != 200:
                return False, f"GET /api/news/ returned {status}", req, resp, "backend-routes-news"
            if not isinstance(data, dict) or "data" not in data:
                return False, "/api/news/ response missing 'data' field", req, resp, "backend-routes-news"
            if not isinstance(data["data"], list):
                return False, "/api/news/ 'data' is not a list", req, resp, "backend-routes-news"
            return True, f"listed {len(data['data'])} articles", req, resp, None
        return self._run("news_list_endpoint", "api", SEVERITY_HIGH, _t)

    def test_news_stats_endpoint(self):
        def _t():
            url = f"{self.backend}/api/news/stats"
            status, _, body = http_request("GET", url)
            data = parse_json(body) or {}
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body": data}
            if status != 200:
                return False, f"GET /api/news/stats returned {status}", req, resp, "backend-routes-news"
            payload = data.get("data", data)
            if not isinstance(payload, dict):
                return False, "/api/news/stats 'data' missing or wrong type", req, resp, "backend-routes-news"
            for k in ("total_articles", "articles_with_summaries"):
                if k not in payload:
                    return False, f"/api/news/stats missing '{k}'", req, resp, "backend-routes-news"
            return True, f"total={payload.get('total_articles')}, summarized={payload.get('articles_with_summaries')}", req, resp, None
        return self._run("news_stats_endpoint", "api", SEVERITY_MEDIUM, _t)

    def test_summarize_status_endpoint(self):
        def _t():
            url = f"{self.backend}/api/summarize/status"
            status, _, body = http_request("GET", url, timeout=20.0)
            data = parse_json(body) or {}
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body": data}
            if status != 200:
                return False, f"GET /api/summarize/status returned {status}", req, resp, "backend-routes-summarize"
            inner = data.get("data", data)
            if "status" not in inner and "provider" not in inner:
                return False, "summarize/status missing 'status' and 'provider' fields", req, resp, "backend-routes-summarize"
            return True, f"summarize service {inner.get('status', '?')} (provider={inner.get('provider', '?')})", req, resp, None
        return self._run("summarize_status_endpoint", "api", SEVERITY_MEDIUM, _t)

    def test_ollama_reachable(self):
        def _t():
            url = f"{self.ollama}/api/tags"
            status, _, body = http_request("GET", url, timeout=5.0)
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body_snippet": body[:200]}
            if status == 0:
                return False, "Ollama not reachable - is `ollama serve` running?", req, resp, "ollama-setup"
            if status != 200:
                return False, f"Ollama returned {status}", req, resp, "ollama-setup"
            data = parse_json(body) or {}
            models = [m.get("name", "") for m in data.get("models", [])]
            if not models:
                return False, "Ollama is up but no models pulled (try `ollama pull llama3.2:1b`)", req, resp, "ollama-setup"
            return True, f"Ollama up with {len(models)} model(s): {', '.join(models[:3])}", req, resp, None
        return self._run("ollama_reachable", "infra", SEVERITY_HIGH, _t)

    def test_ingest_status_endpoint(self):
        def _t():
            url = f"{self.backend}/api/ingest/status"
            status, _, body = http_request("GET", url)
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body_snippet": body[:200]}
            if status != 200:
                return False, f"GET /api/ingest/status returned {status}", req, resp, "backend-routes-ingest"
            return True, "ingest status endpoint responsive", req, resp, None
        return self._run("ingest_status_endpoint", "api", SEVERITY_MEDIUM, _t)

    def test_pipeline_summarize_pending(self):
        """Trigger the orchestrator and confirm articles_with_summaries goes up."""
        def _t():
            stats_url = f"{self.backend}/api/news/stats"
            _, _, before_body = http_request("GET", stats_url)
            before = (parse_json(before_body) or {}).get("data", {})
            before_summaries = before.get("articles_with_summaries", 0)
            before_total = before.get("total_articles", 0)

            run_url = f"{self.backend}/api/ingest/summarize-pending?limit=5"
            status, _, body = http_request("POST", run_url, timeout=120.0)
            data = parse_json(body) or {}
            req = {"method": "POST", "url": run_url}
            resp = {"status": status, "body": data}

            if status != 200:
                return False, f"POST /api/ingest/summarize-pending returned {status}", req, resp, "backend-orchestrator"
            result = (data.get("result") if isinstance(data, dict) else {}) or {}
            if result.get("failed", 0) > 0:
                return False, f"orchestrator reported {result['failed']} failure(s): {result.get('errors', [])}", req, resp, "backend-orchestrator"

            _, _, after_body = http_request("GET", stats_url)
            after = (parse_json(after_body) or {}).get("data", {})
            after_summaries = after.get("articles_with_summaries", 0)
            resp["before"] = {"total": before_total, "summarized": before_summaries}
            resp["after"] = {"total": after.get("total_articles", 0), "summarized": after_summaries}

            if before_total == 0:
                return True, "no articles in DB to summarize (orchestrator ran cleanly)", req, resp, None
            requested = result.get("requested", 0)
            if requested == 0:
                return True, "no pending articles to summarize (idempotent)", req, resp, None
            if after_summaries <= before_summaries and result.get("summarized", 0) > 0:
                return False, "orchestrator reported success but DB summary count didn't go up", req, resp, "backend-orchestrator"
            return True, (
                f"summarized {result.get('summarized', 0)}/{requested} "
                f"(skipped_short={result.get('skipped_short', 0)}, failed={result.get('failed', 0)})"
            ), req, resp, None
        return self._run("pipeline_summarize_pending", "pipeline", SEVERITY_HIGH, _t)

    def test_frontend_reachable(self):
        def _t():
            url = (self.frontend or "http://localhost:5173").rstrip("/") + "/"
            # Vite (and most SPA dev servers) do content-negotiation; the
            # default Accept header on http_request is application/json which
            # makes them return 404. Send a browser-shaped Accept header.
            status, _, body = http_request(
                "GET", url, timeout=5.0,
                headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            )
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body_snippet": body[:200]}
            if status == 0:
                return False, f"Frontend not reachable at {url}", req, resp, "frontend-startup"
            if status >= 400:
                return False, f"Frontend returned {status}", req, resp, "frontend-startup"
            if "<!doctype html" not in body.lower() and "<html" not in body.lower():
                return False, "Frontend response is not HTML", req, resp, "frontend-startup"
            return True, f"frontend reachable (HTTP {status})", req, resp, None
        return self._run("frontend_reachable", "frontend", SEVERITY_MEDIUM, _t)

    def test_cors_for_frontend(self):
        """Backend should allow at least one localhost frontend origin."""
        def _t():
            url = f"{self.backend}/api/news/?page_size=1"
            status, headers, _ = http_request(
                "GET", url,
                headers={"Origin": self.frontend or "http://localhost:5173"},
            )
            allow = headers.get("Access-Control-Allow-Origin") or headers.get("access-control-allow-origin")
            req = {"method": "GET", "url": url, "Origin": self.frontend}
            resp = {"status": status, "Access-Control-Allow-Origin": allow}
            if status >= 400:
                return False, f"backend returned {status}", req, resp, "backend-cors"
            if not allow:
                return False, "backend did not echo Access-Control-Allow-Origin header", req, resp, "backend-cors"
            return True, f"CORS allow header present: {allow}", req, resp, None
        return self._run("cors_for_frontend", "config", SEVERITY_MEDIUM, _t)


    def test_chat_rag_endpoint(self):
        """Chat tab: POST /api/rag/query should return a substantive answer."""
        def _t():
            url = f"{self.backend}/api/rag/query"
            body = {"question": "What are the latest AI chip announcements?", "top_k": 3, "min_score": 0.3}
            status, _, body_text = http_request("POST", url, body=body, timeout=120.0)
            data = parse_json(body_text) or {}
            inner = data.get("data", data)
            req = {"method": "POST", "url": url, "body": body}
            resp = {"status": status, "body": data}
            if status != 200:
                return False, f"/api/rag/query returned {status}", req, resp, "backend-routes-rag"
            answer = (inner.get("answer") or "").strip()
            if not answer:
                return False, "RAG endpoint returned empty answer", req, resp, "backend-routes-rag"
            if len(answer) < 30:
                return False, f"RAG answer suspiciously short ({len(answer)} chars): {answer[:80]!r}", req, resp, "backend-routes-rag"
            return True, f"answer ok ({len(answer)} chars, {len(inner.get('sources') or [])} sources)", req, resp, None
        return self._run("chat_rag_endpoint", "feature", SEVERITY_HIGH, _t)

    def test_semantic_search_endpoint(self):
        """Research tab: POST /api/search/semantic should return results array."""
        def _t():
            url = f"{self.backend}/api/search/semantic"
            body = {"query": "AI chip", "limit": 3}
            status, _, body_text = http_request("POST", url, body=body, timeout=30.0)
            data = parse_json(body_text) or {}
            req = {"method": "POST", "url": url, "body": body}
            resp = {"status": status, "body_snippet": body_text[:200]}
            if status >= 500:
                return False, f"semantic search returned {status}: {body_text[:200]}", req, resp, "backend-routes-search"
            inner = data.get("data", data) if isinstance(data, dict) else {}
            results = inner.get("results")
            if results is None and isinstance(data, dict):
                results = data.get("results")
            if results is None:
                return False, "semantic search response missing 'results' field", req, resp, "backend-routes-search"
            if not isinstance(results, list):
                return False, f"semantic search 'results' is not a list: {type(results).__name__}", req, resp, "backend-routes-search"
            return True, f"results array with {len(results)} hit(s)", req, resp, None
        return self._run("semantic_search_endpoint", "feature", SEVERITY_HIGH, _t)

    def test_digest_endpoint(self):
        """Digest tab: GET /api/digest/ should return topStories + categoryBreakdown."""
        def _t():
            url = f"{self.backend}/api/digest/"
            status, _, body_text = http_request("GET", url, timeout=10.0)
            data = parse_json(body_text) or {}
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body": data if isinstance(data, dict) else None}
            if status != 200:
                return False, f"/api/digest/ returned {status}", req, resp, "backend-routes-digest"
            for k in ("topStories", "categoryBreakdown", "trendingTopics"):
                if k not in data:
                    return False, f"digest response missing '{k}'", req, resp, "backend-routes-digest"
            if not isinstance(data["topStories"], list):
                return False, "topStories is not a list", req, resp, "backend-routes-digest"
            return True, f"digest ok ({len(data['topStories'])} stories, {len(data['categoryBreakdown'])} categories)", req, resp, None
        return self._run("digest_endpoint", "feature", SEVERITY_MEDIUM, _t)

    def test_settings_persistence(self):
        """Settings tab: PUT /api/settings then GET it back, expect the same shape."""
        def _t():
            url = f"{self.backend}/api/settings/"
            payload = {
                "categories": ["AI", "Robotics"],
                "view_mode": "detailed",
                "show_trending_only": False,
            }
            put_status, _, put_body = http_request("PUT", url, body=payload, timeout=10.0)
            put_data = parse_json(put_body) or {}
            req = {"method": "PUT", "url": url, "body": payload}
            resp = {"status": put_status, "body": put_data}
            if put_status != 200:
                return False, f"PUT /api/settings/ returned {put_status}", req, resp, "backend-routes-settings"
            put_inner = put_data.get("data", put_data)
            if not isinstance(put_inner, dict):
                return False, "PUT /api/settings/ response missing 'data'", req, resp, "backend-routes-settings"

            get_status, _, get_body = http_request("GET", url, timeout=10.0)
            get_data = parse_json(get_body) or {}
            resp["get_status"] = get_status
            resp["get_body"] = get_data
            if get_status != 200:
                return False, f"GET /api/settings/ returned {get_status}", req, resp, "backend-routes-settings"
            get_inner = get_data.get("data", get_data)
            if not isinstance(get_inner, dict):
                return False, "GET /api/settings/ response missing 'data'", req, resp, "backend-routes-settings"

            cats = get_inner.get("categories")
            if cats != payload["categories"]:
                return False, f"GET categories {cats!r} != PUT {payload['categories']!r}", req, resp, "backend-routes-settings"
            if get_inner.get("view_mode") != payload["view_mode"]:
                return False, (
                    f"GET view_mode {get_inner.get('view_mode')!r} != "
                    f"PUT {payload['view_mode']!r}"
                ), req, resp, "backend-routes-settings"
            if get_inner.get("show_trending_only") != payload["show_trending_only"]:
                return False, (
                    f"GET show_trending_only {get_inner.get('show_trending_only')!r} != "
                    f"PUT {payload['show_trending_only']!r}"
                ), req, resp, "backend-routes-settings"
            return True, (
                f"settings round-trip ok ({len(cats)} categories, "
                f"view_mode={get_inner.get('view_mode')})"
            ), req, resp, None
        return self._run("settings_persistence", "feature", SEVERITY_HIGH, _t)

    def test_retention_dry_run(self):
        """Milestone 3: insert a back-dated article, run retention dry-run
        (asserts it is listed), then run live (asserts it is gone).

        We talk to sqlite directly because the public API has no "insert
        article with a custom published_at" affordance ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â that's the whole
        point of retention being internal."""
        def _t():
            import os
            import sqlite3

            # Resolve the same db path the backend uses. The backend's
            # cwd is backend/, and DATABASE_URL=sqlite:///./news.db so the
            # absolute path is backend/news.db relative to repo root.
            here = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
            db_path = os.path.join(repo_root, "backend", "news.db")
            req: Dict[str, Any] = {"db_path": db_path}
            resp: Dict[str, Any] = {}

            if not os.path.exists(db_path):
                return False, f"backend DB not found at {db_path}", req, resp, "backend-startup"

            test_url = "https://test.local/retention-e2e-marker"
            inserted_id: Optional[int] = None

            try:
                con = sqlite3.connect(db_path)
                # Make sure no leftover row from a previous run skews us.
                con.execute("DELETE FROM articles WHERE url = ?", (test_url,))
                con.execute(
                    "INSERT INTO articles (title, url, source, published_at, content) "
                    "VALUES (?, ?, ?, datetime('now', '-31 days'), ?)",
                    ("retention-e2e", test_url, "e2e-test", "old test content"),
                )
                con.commit()
                inserted_id = con.execute(
                    "SELECT id FROM articles WHERE url = ?", (test_url,)
                ).fetchone()[0]
                con.close()
                req["inserted_id"] = inserted_id
            except Exception as exc:  # noqa: BLE001
                return False, f"failed to seed back-dated article: {exc}", req, resp, "backend-routes-admin"

            try:
                # Dry-run: should list the inserted ID
                dry_url = f"{self.backend}/api/admin/retention/run?dry_run=true"
                status, _, body = http_request("POST", dry_url, timeout=15.0)
                data = parse_json(body) or {}
                resp["dry_run"] = {"status": status, "body": data}
                if status != 200:
                    return False, f"POST /api/admin/retention/run?dry_run=true returned {status}: {body[:200]}", req, resp, "backend-routes-admin"
                inner = data.get("data", data)
                if not inner.get("dry_run"):
                    return False, "dry-run response did not flag dry_run=true", req, resp, "backend-routes-admin"
                would = inner.get("would_delete") or []
                if inserted_id not in would:
                    return False, (
                        f"dry-run did not include inserted id {inserted_id}; "
                        f"would_delete={would[:10]}"
                    ), req, resp, "backend-routes-admin"

                # Confirm the article still exists after dry-run
                con = sqlite3.connect(db_path)
                row = con.execute(
                    "SELECT id FROM articles WHERE url = ?", (test_url,)
                ).fetchone()
                con.close()
                if row is None:
                    return False, "dry-run unexpectedly deleted the article", req, resp, "backend-routes-admin"

                # Live run
                live_url = f"{self.backend}/api/admin/retention/run"
                status, _, body = http_request("POST", live_url, timeout=15.0)
                data = parse_json(body) or {}
                resp["live"] = {"status": status, "body": data}
                if status != 200:
                    return False, f"POST /api/admin/retention/run returned {status}: {body[:200]}", req, resp, "backend-routes-admin"

                # Confirm row is gone
                con = sqlite3.connect(db_path)
                row = con.execute(
                    "SELECT id FROM articles WHERE url = ?", (test_url,)
                ).fetchone()
                con.close()
                if row is not None:
                    return False, f"article {inserted_id} still present after live retention run", req, resp, "backend-routes-admin"

                return True, (
                    f"retention ok: dry-run listed id {inserted_id}, "
                    f"live deleted {(data.get('data') or {}).get('deleted_articles', 0)} article(s)"
                ), req, resp, None
            finally:
                # Best-effort cleanup in case anything above bailed out.
                try:
                    con = sqlite3.connect(db_path)
                    con.execute("DELETE FROM articles WHERE url = ?", (test_url,))
                    con.commit()
                    con.close()
                except Exception:  # noqa: BLE001
                    pass
        return self._run("retention_dry_run", "feature", SEVERITY_HIGH, _t)

    def test_live_ingest_smoke(self):
        """Milestone 5: real ingest round-trip.

        Hits live RSS feeds via POST /api/ingest/ (foreground,
        auto_summarize=false to keep the test reasonably fast), waits
        for completion, and asserts that total_articles strictly
        increased OR the ingest reported zero new articles (which is
        valid on a clean run if every feed item already exists).

        Marked opt-in via --include-live-ingest because:
          * it hits the real internet,
          * it takes 30s-5min depending on CPU,
          * it mutates the DB.
        """
        def _t():
            stats_url = f"{self.backend}/api/news/stats"
            ingest_url = f"{self.backend}/api/ingest/"
            status_url = f"{self.backend}/api/ingest/status"

            _, _, before_body = http_request("GET", stats_url, timeout=10.0)
            before = (parse_json(before_body) or {}).get("data", {})
            before_total = before.get("total_articles", 0)

            body = {"background": False, "auto_summarize": False}
            req = {"method": "POST", "url": ingest_url, "body": body}

            # Foreground call -- blocks until ingest finishes. Long
            # timeout because slow CPUs + RSS latency add up.
            status, _, ingest_body = http_request(
                "POST", ingest_url, body=body, timeout=600.0
            )
            ingest_data = parse_json(ingest_body) or {}
            resp: Dict[str, Any] = {
                "status": status,
                "ingest_body": ingest_data,
            }
            if status != 200:
                return False, f"POST /api/ingest/ returned {status}", req, resp, "backend-routes-ingest"

            # Even though the foreground call already completed, hit
            # /status once for parity with a future async path.
            poll_status, _, poll_body = http_request("GET", status_url, timeout=10.0)
            resp["poll_status"] = poll_status
            resp["poll_body"] = parse_json(poll_body)

            _, _, after_body = http_request("GET", stats_url, timeout=10.0)
            after = (parse_json(after_body) or {}).get("data", {})
            after_total = after.get("total_articles", 0)
            resp["before"] = {"total_articles": before_total}
            resp["after"] = {"total_articles": after_total}

            if after_total < before_total:
                return False, (
                    f"total_articles went DOWN: {before_total} -> {after_total}"
                ), req, resp, "backend-orchestrator"

            return True, (
                f"live ingest ok: total {before_total} -> {after_total} "
                f"(delta={after_total - before_total})"
            ), req, resp, None
        return self._run("live_ingest_smoke", "pipeline", SEVERITY_HIGH, _t)

    def test_news_sources_endpoint(self):
        """Filter / Topic tab: GET /api/news/sources should list configured sources."""
        def _t():
            url = f"{self.backend}/api/news/sources"
            status, _, body_text = http_request("GET", url, timeout=5.0)
            data = parse_json(body_text) or {}
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body": data if isinstance(data, dict) else None}
            if status != 200:
                return False, f"/api/news/sources returned {status}", req, resp, "backend-routes-news"
            inner = data.get("data", data)
            stats = inner.get("source_statistics", {})
            if not stats:
                return False, "no source_statistics returned", req, resp, "backend-routes-news"
            return True, f"{len(stats)} sources reported", req, resp, None
        return self._run("news_sources_endpoint", "feature", SEVERITY_MEDIUM, _t)

    def test_kg_endpoint(self):
        """Milestone 6: GET /api/knowledge-graph/?limit=N returns a valid
        {nodes, edges, total_entities} payload.

        Nodes / edges may be empty on a fresh DB (no extraction has run).
        The shape must hold either way.
        """
        def _t():
            url = f"{self.backend}/api/knowledge-graph/?limit=10"
            status, _, body_text = http_request("GET", url, timeout=10.0)
            data = parse_json(body_text) or {}
            req = {"method": "GET", "url": url}
            resp = {"status": status, "body": data if isinstance(data, dict) else None}

            if status != 200:
                return False, f"GET /api/knowledge-graph/?limit=10 returned {status}: {body_text[:200]}", req, resp, "backend-routes-knowledge-graph"
            if not isinstance(data, dict):
                return False, f"response is not a JSON object: {type(data).__name__}", req, resp, "backend-routes-knowledge-graph"
            if "nodes" not in data:
                return False, "response missing 'nodes' field", req, resp, "backend-routes-knowledge-graph"
            if "edges" not in data:
                return False, "response missing 'edges' field", req, resp, "backend-routes-knowledge-graph"
            if not isinstance(data["nodes"], list):
                return False, f"'nodes' is not a list: {type(data['nodes']).__name__}", req, resp, "backend-routes-knowledge-graph"
            if not isinstance(data["edges"], list):
                return False, f"'edges' is not a list: {type(data['edges']).__name__}", req, resp, "backend-routes-knowledge-graph"
            for n in data["nodes"]:
                if not isinstance(n, dict):
                    return False, f"node entry not a dict: {n!r}", req, resp, "backend-routes-knowledge-graph"
                for k in ("id", "name", "type", "mention_count"):
                    if k not in n:
                        return False, f"node missing '{k}' field: {n!r}", req, resp, "backend-routes-knowledge-graph"
            total = data.get("total_entities")
            if total is not None and (not isinstance(total, int) or total < 0):
                return False, f"total_entities invalid: {total!r}", req, resp, "backend-routes-knowledge-graph"
            return True, (
                f"kg ok ({len(data['nodes'])} nodes, "
                f"{len(data['edges'])} edges, total={total})"
            ), req, resp, None
        return self._run("kg_endpoint", "feature", SEVERITY_HIGH, _t)

    def test_research_sse_smoke(self):
        """Milestone 2: POST /api/research returns text/event-stream and at
        least one ``data:`` line decoding to a JSON ``phase`` event arrives
        within 5s.

        Talks to the live backend via ``urllib.request`` (stdlib only --
        same posture as the other contract tests). We post a question,
        read response bytes incrementally, and split on ``\n\n`` to
        parse SSE frames. The test passes as soon as the first ``phase``
        event is seen; we don't wait for ``done`` (the agent calls a real
        Ollama on the backend and a full run takes 30-90s).
        """
        def _t():
            url = f"{self.backend}/api/research"
            payload = {"question": "What's new in AI chips this week?"}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
            )
            request_meta = {"method": "POST", "url": url, "body": payload}
            resp_meta: Dict[str, Any] = {}

            try:
                # NOTE: don't pass a small timeout to ``urlopen`` for SSE
                # -- the timeout applies to socket reads, not the whole
                # stream lifetime. We bound the wait via a wall clock
                # check below.
                resp = urllib.request.urlopen(req, timeout=10.0)
            except urllib.error.HTTPError as exc:
                body_text = exc.read().decode("utf-8", "replace") if exc.fp else ""
                resp_meta = {"status": exc.code, "body_snippet": body_text[:300]}
                return False, (
                    f"POST /api/research returned {exc.code}: {body_text[:200]}"
                ), request_meta, resp_meta, "backend-routes-research"
            except urllib.error.URLError as exc:
                resp_meta = {"error": f"URLError: {exc.reason}"}
                return False, (
                    f"POST /api/research not reachable: {exc.reason}"
                ), request_meta, resp_meta, "backend-routes-research"
            except Exception as exc:  # noqa: BLE001
                resp_meta = {"error": f"{type(exc).__name__}: {exc}"}
                return False, (
                    f"POST /api/research crashed: {exc}"
                ), request_meta, resp_meta, "backend-routes-research"

            with resp:
                ctype = resp.headers.get("Content-Type", "")
                resp_meta["status"] = resp.status
                resp_meta["content_type"] = ctype
                if "text/event-stream" not in ctype:
                    return False, (
                        f"expected text/event-stream, got {ctype!r}"
                    ), request_meta, resp_meta, "backend-routes-research"

                deadline = time.time() + 5.0
                buf = b""
                phase_seen: Optional[Dict[str, Any]] = None
                # Read in small chunks. ``resp.read(size)`` blocks up to
                # the socket timeout; we picked 10s on urlopen but bail
                # out via the wall-clock check below either way.
                while time.time() < deadline:
                    try:
                        chunk = resp.read(512)
                    except Exception:  # noqa: BLE001
                        chunk = b""
                    if not chunk:
                        # No data this poll -- short sleep, try again.
                        time.sleep(0.1)
                        continue
                    buf += chunk
                    while b"\n\n" in buf:
                        block, _, buf = buf.partition(b"\n\n")
                        text = block.decode("utf-8", "replace").strip()
                        if not text or text.startswith(":"):
                            continue
                        if not text.startswith("data:"):
                            continue
                        json_text = text[len("data:"):].strip()
                        try:
                            evt = json.loads(json_text)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(evt, dict) and evt.get("type") == "phase":
                            phase_seen = evt
                            break
                    if phase_seen is not None:
                        break

                resp_meta["first_phase_event"] = phase_seen
                if phase_seen is None:
                    return False, (
                        "no phase event arrived within 5s of POST"
                    ), request_meta, resp_meta, "backend-routes-research"
                return True, (
                    f"first phase event: {phase_seen.get('data')!r}"
                ), request_meta, resp_meta, None

        return self._run(
            "research_sse_smoke", "feature", SEVERITY_HIGH, _t
        )

    def test_kg_no_mock(self):
        """Milestone 6: KnowledgeGraph.tsx must not contain a 'mockData'
        constant or any hardcoded fallback in the production code path.
        """
        def _t():
            import os
            here = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
            kg_path = os.path.join(
                repo_root, "frontend", "src", "components", "KnowledgeGraph.tsx"
            )
            req = {"file": kg_path, "patterns": ["mockData", "hardcoded"]}
            resp: Dict[str, Any] = {}

            if not os.path.exists(kg_path):
                return False, f"KnowledgeGraph.tsx not found at {kg_path}", req, resp, "frontend-knowledge-graph"

            try:
                with open(kg_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as exc:
                return False, f"failed to read KnowledgeGraph.tsx: {exc}", req, resp, "frontend-knowledge-graph"

            offenders: List[Dict[str, Any]] = []
            for lineno, line in enumerate(text.splitlines(), start=1):
                lower = line.lower()
                if "mockdata" in lower or "hardcoded" in lower:
                    offenders.append({"line": lineno, "text": line.strip()[:120]})

            resp["offenders"] = offenders
            resp["lines_scanned"] = len(text.splitlines())

            if offenders:
                return False, (
                    f"found {len(offenders)} mock/hardcoded reference(s) "
                    f"in KnowledgeGraph.tsx (first: line {offenders[0]['line']}: "
                    f"{offenders[0]['text']!r})"
                ), req, resp, "frontend-knowledge-graph"
            return True, "no mock/hardcoded references found", req, resp, None
        return self._run("kg_no_mock", "config", SEVERITY_HIGH, _t)

    # -------------------------------------------------------------- #
    #  Run order
    # -------------------------------------------------------------- #

    def run_all(self) -> List[TestResult]:
        # Infrastructure first; if backend not reachable, abort
        infra = self.test_backend_reachable()
        if not infra.passed:
            return self.results

        # Core API surface
        self.test_health_payload()
        self.test_news_list_endpoint()
        self.test_news_stats_endpoint()
        self.test_summarize_status_endpoint()
        self.test_ingest_status_endpoint()
        self.test_cors_for_frontend()

        # External dependency
        self.test_ollama_reachable()

        # Feature-level tests (one per frontend tab)
        self.test_news_sources_endpoint()
        self.test_digest_endpoint()
        self.test_settings_persistence()
        self.test_semantic_search_endpoint()
        self.test_chat_rag_endpoint()
        self.test_retention_dry_run()
        self.test_kg_endpoint()
        self.test_kg_no_mock()
        self.test_research_sse_smoke()

        # The actual pipeline
        if not self.skip_pipeline:
            self.test_pipeline_summarize_pending()

        # Live ingest smoke (Milestone 5) -- opt-in, slow.
        if self.include_live_ingest:
            self.test_live_ingest_smoke()

        # Frontend (if running)
        if not self.skip_frontend and self.frontend:
            self.test_frontend_reachable()

        return self.results


# ---------------------------------------------------------------------- #
#  Reporting
# ---------------------------------------------------------------------- #

def print_human_report(results: List[TestResult]) -> int:
    """Pretty-print results. Returns exit code (0 if all passed)."""
    width = 70
    print("=" * width)
    print(" E2E TEST REPORT")
    print("=" * width)
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"  [{mark}] ({r.severity:<8s}) {r.category:<10s} {r.name:<32s} {r.duration_ms:>5d}ms")
        if not r.passed:
            print(f"         -> {r.detail}")

    print()
    print(f" {len(passed)}/{len(results)} passed")
    if failed:
        print()
        print(" FAILURES (most severe first):")
        order = {SEVERITY_CRITICAL: 0, SEVERITY_HIGH: 1, SEVERITY_MEDIUM: 2, SEVERITY_LOW: 3}
        for r in sorted(failed, key=lambda x: order.get(x.severity, 9)):
            print(f"   - [{r.severity:>8s}] {r.name}: {r.detail}")
            if r.suggested_fix_area:
                print(f"     fix-hint: {r.suggested_fix_area}")
    print("=" * width)
    return 0 if not failed else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Black-box E2E test runner")
    p.add_argument("--backend", default="http://127.0.0.1:8000")
    p.add_argument("--frontend", default="http://localhost:5173")
    p.add_argument("--ollama-host", default="http://127.0.0.1:11434", dest="ollama")
    p.add_argument("--skip-pipeline", action="store_true",
                   help="Don't run the orchestrator round-trip test")
    p.add_argument("--include-live-ingest", action="store_true",
                   dest="include_live_ingest",
                   help="Include the live RSS ingest round-trip test "
                        "(slow; off by default).")
    p.add_argument("--skip-frontend", action="store_true",
                   help="Skip the frontend reachability test")
    p.add_argument("--json", action="store_true",
                   help="Emit a machine-readable JSON report on stdout")
    p.add_argument("--out", default=None,
                   help="Path to write the JSON report to (in addition to stdout)")
    args = p.parse_args()

    suite = E2ESuite(
        backend=args.backend, frontend=args.frontend, ollama=args.ollama,
        skip_pipeline=args.skip_pipeline, skip_frontend=args.skip_frontend,
        include_live_ingest=args.include_live_ingest,
    )
    results = suite.run_all()
    payload = {
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
        },
        "results": [r.to_dict() for r in results],
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0 if payload["summary"]["failed"] == 0 else 1
    return print_human_report(results)


if __name__ == "__main__":
    sys.exit(main())
