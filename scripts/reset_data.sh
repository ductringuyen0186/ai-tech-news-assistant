#!/usr/bin/env bash
# scripts/reset_data.sh
# ---------------------------------------------------------------
# Wipe + clean re-ingest. Single command that resets the data layer
# of either the local backend (default) or a deployed VPS instance
# (--prod). After this script returns 0, the target deploy has a
# fresh news.db with a real articles + summaries (subject to RSS
# health on the day).
#
# Modes:
#   ./scripts/reset_data.sh          local mode -> http://localhost:8000
#   ./scripts/reset_data.sh --prod   prod  mode -> $PROD_URL
#                                    (refuses unless user types
#                                     literally "WIPE PROD")
#
# Steps (in order):
#   1. Confirm Ollama is reachable (skipped in --prod where Ollama
#      lives behind the backend container).
#   2. POST /api/admin/wipe?confirm=WIPE  - clears DB rows
#   3. POST /api/ingest/   foreground, auto_summarize=true
#   4. Poll /api/ingest/status (foreground call already returned)
#   5. GET  /api/news/stats  -> require total_articles >= 50
#
# Exit codes:
#   0  success (>=50 articles after re-ingest)
#   1  user aborted prod confirmation
#   2  precondition failed (Ollama, backend unreachable, env missing)
#   3  wipe / ingest / verify failure
#
# Idempotent. Safe to re-run. The wipe is the only destructive step
# and it's gated behind the literal confirm string both here and on
# the server.
# ---------------------------------------------------------------
set -u

# ---- options --------------------------------------------------
PROD=0
SKIP_OLLAMA_CHECK=0
MIN_ARTICLES=${MIN_ARTICLES:-50}
INGEST_TIMEOUT=${INGEST_TIMEOUT:-600}  # 10 min; slow VPS CPUs can be slow

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prod)
            PROD=1
            shift
            ;;
        --skip-ollama-check)
            SKIP_OLLAMA_CHECK=1
            shift
            ;;
        --min-articles)
            MIN_ARTICLES="$2"
            shift 2
            ;;
        -h|--help)
            cat <<HLP
Usage: $0 [--prod] [--skip-ollama-check] [--min-articles N]

  --prod                Target \$PROD_URL with extra confirm prompt.
                        Refuses unless user types: WIPE PROD
  --skip-ollama-check   Skip the local Ollama reachability probe.
  --min-articles N      Fail if final total_articles < N (default 50).

Env:
  PROD_URL              Required when --prod is set. e.g.
                        https://news.example.com
  OLLAMA_URL            Default http://127.0.0.1:11434
HLP
            exit 0
            ;;
        *)
            echo "[reset_data] unknown arg: $1" >&2
            exit 2
            ;;
    esac
done

# ---- target URL ----------------------------------------------
if [[ $PROD -eq 1 ]]; then
    if [[ -z "${PROD_URL:-}" ]]; then
        echo "[reset_data] PROD_URL env var is required for --prod" >&2
        exit 2
    fi
    BACKEND_URL="${PROD_URL%/}"
    echo "[reset_data] mode: PROD"
    echo "[reset_data] target: $BACKEND_URL"
    echo ""
    echo "  !!  This will WIPE every article on the live deploy.  !!"
    echo "      Type the literal phrase  WIPE PROD  to continue."
    echo "      Anything else aborts."
    echo ""
    printf "confirm> "
    read -r confirmation
    if [[ "$confirmation" != "WIPE PROD" ]]; then
        echo "[reset_data] aborted: confirmation phrase did not match"
        exit 1
    fi
else
    BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
    echo "[reset_data] mode: LOCAL"
    echo "[reset_data] target: $BACKEND_URL"
fi

OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"

# ---- helpers --------------------------------------------------
fail() {
    echo "[reset_data] FAIL: $*" >&2
    exit 3
}

# Require curl + python3 (used for json parsing). python is fine if
# python3 isn't on PATH (some Windows Git Bash setups).
if ! command -v curl >/dev/null 2>&1; then
    echo "[reset_data] curl is required" >&2
    exit 2
fi

# Pick a python that actually runs. Windows ships a Microsoft Store stub
# that's on $PATH but exits with an "install from Store" message when
# invoked, so `command -v` is not enough -- we have to call --version.
PY=""
for cand in python3 python py; do
    if command -v $cand >/dev/null 2>&1; then
        if "$cand" --version >/dev/null 2>&1; then
            PY=$cand
            break
        fi
    fi
done
if [[ -z "$PY" ]]; then
    echo "[reset_data] python (for json parsing) is required" >&2
    exit 2
fi

json_get() {
    # json_get <json-text> <dotted.path>
    # echoes the value or empty string if missing.
    # The JSON is passed via the JSON_TEXT env var because bash heredocs
    # already feed the python "-" stdin path (script source), so we
    # cannot also pipe the data through stdin.
    JSON_TEXT="$1" JSON_PATH="$2" "$PY" - <<'PYJSON'
import json, os, sys
text = os.environ.get("JSON_TEXT", "")
path = os.environ.get("JSON_PATH", "").split('.')
try:
    obj = json.loads(text)
except Exception:
    print(""); sys.exit(0)
cur = obj
for p in path:
    if isinstance(cur, dict) and p in cur:
        cur = cur[p]
    else:
        print(""); sys.exit(0)
print(cur if cur is not None else "")
PYJSON
}

# ---- 1. Ollama check (local only) -----------------------------
if [[ $PROD -eq 0 && $SKIP_OLLAMA_CHECK -eq 0 ]]; then
    echo "[reset_data] checking Ollama at $OLLAMA_URL ..."
    if ! curl -fsS -m 5 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
        echo "[reset_data] WARNING: Ollama not reachable at $OLLAMA_URL"
        echo "             Ingestion will still run but summarisation will fail."
        echo "             (use --skip-ollama-check to silence this)"
    else
        echo "[reset_data] Ollama OK"
    fi
fi

# ---- 2. Backend reachable -------------------------------------
echo "[reset_data] checking backend at $BACKEND_URL/health ..."
if ! curl -fsS -m 10 "$BACKEND_URL/health" >/dev/null 2>&1; then
    echo "[reset_data] backend unreachable at $BACKEND_URL/health" >&2
    exit 2
fi
echo "[reset_data] backend OK"

# ---- 3. Wipe --------------------------------------------------
echo "[reset_data] wiping DB via POST /api/admin/wipe?confirm=WIPE ..."
WIPE_RESP=$(curl -fsS -m 30 -X POST "$BACKEND_URL/api/admin/wipe?confirm=WIPE") \
    || fail "wipe call failed"
echo "[reset_data] wipe response: $WIPE_RESP"
total_deleted=$(json_get "$WIPE_RESP" "data.total_deleted")
echo "[reset_data] rows deleted: ${total_deleted:-0}"

# ---- 4. Ingest (foreground, auto_summarize) -------------------
echo "[reset_data] triggering ingest (foreground, auto_summarize=true) ..."
echo "[reset_data]   timeout: ${INGEST_TIMEOUT}s"
INGEST_BODY='{"background": false, "auto_summarize": true}'
INGEST_RESP=$(curl -fsS -m "$INGEST_TIMEOUT" \
    -X POST -H "Content-Type: application/json" \
    -d "$INGEST_BODY" \
    "$BACKEND_URL/api/ingest/") \
    || fail "ingest call failed (timeout=${INGEST_TIMEOUT}s?)"
echo "[reset_data] ingest response: $INGEST_RESP"

# ---- 5. Verify ------------------------------------------------
echo "[reset_data] checking final stats ..."
STATS_RESP=$(curl -fsS -m 10 "$BACKEND_URL/api/news/stats") \
    || fail "stats call failed"
total_articles=$(json_get "$STATS_RESP" "data.total_articles")
summarised=$(json_get "$STATS_RESP" "data.articles_with_summaries")
echo "[reset_data] total_articles=$total_articles articles_with_summaries=$summarised"

if [[ -z "$total_articles" ]]; then
    fail "could not parse total_articles from stats"
fi

if [[ "$total_articles" -lt "$MIN_ARTICLES" ]]; then
    echo "[reset_data] WARNING: total_articles=$total_articles < required $MIN_ARTICLES" >&2
    echo "             RSS feed health may be poor today; investigate before declaring success." >&2
    exit 3
fi

echo "[reset_data] DONE: $total_articles articles, $summarised summarised"
exit 0
