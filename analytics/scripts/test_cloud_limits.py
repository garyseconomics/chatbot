"""Test Ollama Cloud concurrency and rate limits.

Sends multiple concurrent requests to Ollama Cloud and reports the rate limit
headers from each response. Useful for checking whether limits change after
upgrading tiers.

Uses httpx directly (not LangChain) because we need access to the raw HTTP
response headers — LangChain's ChatOllama doesn't expose them.

Usage:
    python -m analytics.scripts.test_cloud_limits
"""

import asyncio

import httpx

# Uses the main app config (src/config.py), not analytics.config,
# because it needs settings.providers for the Ollama Cloud URL and API key.
from config import settings

CONCURRENT_REQUESTS = 10
TEST_PROMPT = "What is inflation? Answer in one sentence."

# The rate limit headers we want to capture from each response
RATE_LIMIT_HEADERS = [
    "x-ratelimit-max-concurrent",
    "x-ratelimit-queue-limit",
    "x-ratelimit-active",
    "x-ratelimit-queued",
    "retry-after",
]


async def send_request(request_id, client, url, model, api_key) -> dict:
    """Send a single chat request and return status + rate limit headers."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "stream": False,
    }
    try:
        response = await client.post(f"{url}/api/chat", json=payload, headers=headers)
        # Extract rate limit headers (present on both 200 and 429 responses)
        rate_limits = {h: response.headers.get(h) for h in RATE_LIMIT_HEADERS if response.headers.get(h)}
        return {
            "id": request_id,
            "status_code": response.status_code,
            "rate_limits": rate_limits,
        }
    except Exception as e:
        return {
            "id": request_id,
            "status_code": None,
            "error": str(e),
        }


async def run_concurrent_test() -> None:
    provider = settings.providers["ollama_cloud"]
    if not provider["api_key"]:
        print("Error: Ollama Cloud API key not configured. Set OLLAMA_CLOUD_API_KEY in .env")
        return

    url = provider["url"]
    model = provider["chat_model"]

    print(f"Sending {CONCURRENT_REQUESTS} concurrent requests to Ollama Cloud")
    print(f"  URL: {url}")
    print(f"  Model: {model}")
    print()

    # Use a single httpx client for all requests (shared connection pool)
    async with httpx.AsyncClient(timeout=60) as client:
        tasks = [send_request(i, client, url, model, provider["api_key"]) for i in range(CONCURRENT_REQUESTS)]
        results = await asyncio.gather(*tasks)

    # Report results
    successes = [r for r in results if r["status_code"] == 200]
    rejected = [r for r in results if r["status_code"] == 429]
    errors = [r for r in results if r["status_code"] not in (200, 429)]

    print(f"Results: {len(successes)} succeeded, {len(rejected)} rejected (429), {len(errors)} errors")
    print()

    # Show rate limit headers from all responses
    for r in sorted(results, key=lambda x: x["id"]):
        status = r["status_code"] or f"error: {r.get('error', '?')}"
        rate_limits = r.get("rate_limits", {})
        headers_str = ", ".join(f"{k}={v}" for k, v in rate_limits.items()) if rate_limits else "none"
        print(f"  Request {r['id']:2d}: {status} | {headers_str}")

    print()


if __name__ == "__main__":
    asyncio.run(run_concurrent_test())
