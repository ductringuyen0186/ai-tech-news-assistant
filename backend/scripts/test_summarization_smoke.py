"""
Smoke test for SummarizationService against a running Ollama instance.

Usage:
    # 1. Make sure Ollama is running (default http://localhost:11434)
    #    and the configured model is pulled, e.g.:
    #        ollama pull llama3.2:1b
    # 2. Run from the backend/ directory:
    #        python scripts/test_summarization_smoke.py

What it does:
    - Verifies SummarizationService can be constructed from .env config.
    - Calls health_check() and prints whether Ollama is reachable.
    - If healthy, runs a full summarize_content() round-trip on a sample
      article and prints the resulting summary + metadata.
    - Exits with code 0 on success, 1 on any failure.
"""

import asyncio
import sys
from pathlib import Path

# Make `src.*` importable when run from backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from src.core.exceptions import LLMError, ValidationError  # noqa: E402
from src.models.article import SummarizationRequest  # noqa: E402
from src.services.summarization_service import SummarizationService  # noqa: E402


SAMPLE_ARTICLE = """
NVIDIA announced its next-generation AI accelerator chip today, dubbed the
Rubin R200, claiming a 2.5x performance-per-watt improvement over the current
Blackwell B200 generation. The chip uses TSMC's 2nm process node and integrates
288GB of HBM4 memory across eight stacks. NVIDIA CEO Jensen Huang said the part
is aimed at frontier-model training and large-scale inference deployments,
with first customer shipments expected in the second half of 2026. Analysts
noted the announcement puts pressure on AMD and emerging accelerator startups,
several of which had been targeting the inference segment specifically.
""".strip()


def _hr(title: str = "") -> None:
    bar = "-" * 60
    print(f"\n{bar}\n{title}\n{bar}" if title else bar)


async def main() -> int:
    _hr("SummarizationService smoke test")

    try:
        service = SummarizationService()
    except Exception as exc:
        print(f"[FAIL] could not construct SummarizationService: {exc}")
        return 1

    print(f"  host    : {service.base_url}")
    print(f"  model   : {service.model}")
    print(f"  timeout : {service.timeout}s")

    _hr("Step 1: health_check")
    health = await service.health_check()
    for k, v in health.items():
        print(f"  {k}: {v}")

    if health.get("status") == "unhealthy":
        print("\n[FAIL] Ollama not reachable. Is it running?")
        print("       Try:  ollama serve   (and)   ollama pull " + service.model)
        return 1

    if not health.get("model_loaded"):
        print(f"\n[WARN] Model '{service.model}' is not pulled.")
        print(f"       Run: ollama pull {service.model}")
        return 1

    _hr("Step 2: summarize_content (real LLM round-trip)")
    request = SummarizationRequest(content=SAMPLE_ARTICLE, max_length=80)

    try:
        summary = await service.summarize_content(request)
    except (LLMError, ValidationError) as exc:
        print(f"[FAIL] summarize_content raised: {exc}")
        return 1

    print(f"  summary           : {summary.summary}")
    print(f"  word_count        : {summary.word_count}")
    print(f"  original_length   : {summary.original_length}")
    print(f"  summary_length    : {summary.summary_length}")
    print(f"  compression_ratio : {summary.compression_ratio}")
    print(f"  processing_time   : {summary.processing_time}s")
    print(f"  model_used        : {summary.model_used}")

    _hr("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
