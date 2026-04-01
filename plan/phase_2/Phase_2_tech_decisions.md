# Phase 2 — Technical Decisions and Research

Technical details and research results referenced by the
[Phase 2 Plan](Phase_2_Plan.md). Kept separate to keep the main plan accessible
to non-technical readers.

---

## Embedding model

**Current model:** `qwen3-embedding:8b`, scoring 70.58 on the
[MTEB benchmark](https://huggingface.co/spaces/mteb/leaderboard) — the best
embedding model available on Ollama as of March 2026. The only models scoring
higher (NVIDIA's NV-Embed-v2 at 72.31 and Llama-Embed-Nemotron-8B) are not on
Ollama yet.

**Why we keep using it:** Even though we are moving from Ollama to OpenAI-compatible
cloud providers, there are two good reasons to stay with `qwen3-embedding:8b`:
1. **No database regeneration.** Switching embedding models would require regenerating
   the entire vector database — every document would need to be re-embedded.
2. **Ollama compatibility.** We can still use Ollama (local or self-hosted) as a
   fallback if needed.

Re-check model availability in mid-2026 — watch for NVIDIA models landing on Ollama
and Ollama Cloud adding embedding support. Tracked in
[issue #40](https://github.com/garyseconomics/chatbot/issues/40).

## Cloud embedding providers

Several providers offer `qwen3-embedding:8b` via OpenAI-compatible APIs at
negligible cost:

| Provider | Price | API |
|----------|-------|-----|
| [OpenRouter](https://openrouter.ai/qwen/qwen3-embedding-8b) | $0.01 / M tokens | OpenAI-compatible |
| [SiliconFlow](https://www.siliconflow.com/models/qwen-qwen3-embedding-8b) | Pay-as-you-go ($1 free) | OpenAI-compatible |
| [DeepInfra](https://deepinfra.com/Qwen/Qwen3-Embedding-8B/api) | Pay-as-you-go (free credits) | OpenAI-compatible |
| [Alibaba DashScope](https://qwen.ai/apiplatform) | Pay-as-you-go (free quota) | OpenAI-compatible |

At $0.01 per million tokens, the cost is negligible for our use case. All use the
OpenAI-compatible API.

**Model name mapping:** The Ollama model name `qwen3-embedding:8b` maps to
`qwen/qwen3-embedding-8b` on OpenRouter (and similar formats on other providers).

## Ollama Cloud

**Current tier:** Free — 2 concurrent active requests + 5 queued. This caused a
~10% failure rate on the busiest Phase 1 day (10 out of 97 queries rejected).

**Pro tier:** $20/month — 50x more usage and 3 concurrent models.

After upgrading, re-run `python -m analytics.test_cloud_limits` to check whether
the concurrency limits also increase on Pro.

Ollama Cloud does not support embedding models (as of March 2026).

See [latency_report_chat_model.md](../phase_1/latency_report_chat_model.md) for
Phase 1 data and the full analysis of Ollama Cloud limits.

## Server hosting options

**Paid hosting** (recommended for production):

| Provider | Plan | vCPU | RAM | Disk | Price | Notes |
|---|---|---|---|---|---|---|
| [Hetzner](https://www.hetzner.com/cloud/) | CX22 | 2 | 4 GB | 40 GB SSD | **~$3.60/mo** | Best value; EU + US datacenters; developer-friendly |
| [OVHcloud](https://www.ovhcloud.com/en/vps/) | VPS Starter | 1 | 2 GB | 20 GB SSD | **~$3.50–4.50/mo** | Unmetered bandwidth; clunky interface |
| [Contabo](https://contabo.com/en/vps/) | Cloud VPS S | 4 | 8 GB | 50 GB NVMe | **~$4.90/mo** | Huge specs on paper; can oversell; slow support |
| [Hostinger](https://www.hostinger.com/vps-hosting) | KVM 1 | 1 | 4 GB | 50 GB NVMe | **~$5/mo** (promo) | Requires 48-mo commitment; renewal ~$9/mo; Docker templates |
| [Vultr](https://www.vultr.com/pricing/) | Regular | 1 | 1 GB | 25 GB SSD | **$5/mo** | Simple; many locations |
| [AWS Lightsail](https://aws.amazon.com/lightsail/pricing/) | Micro | 1 | 1 GB | 40 GB SSD | **$5/mo** | 3 months free; simple AWS interface |
| [DigitalOcean](https://www.digitalocean.com/pricing) | Basic Droplet | 1 | 1 GB | 25 GB SSD | **$6/mo** | $200 credit for 60 days for new accounts |

**Free options** (for development/testing only):

| Provider | Plan | vCPU | RAM | Disk | Price | Limitation |
|---|---|---|---|---|---|---|
| [Oracle Cloud](https://www.oracle.com/cloud/free/) | Always Free ARM | up to 4 | up to 24 GB | 200 GB | **$0 forever** | Hard to provision; may reclaim idle instances |
| [Google Cloud](https://cloud.google.com/free) | e2-micro | 0.25 (burst to 2) | 1 GB | 30 GB | **$0 forever** | Very constrained; US only; egress costs |
| AWS | t3.micro | 1 | 1 GB | 30 GB | **$0 for 12 months** | Free tier expires, then ~$8–9/mo |

Hostinger prices are from mid-2025 data — verify at their website.
