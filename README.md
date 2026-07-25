# Sentinel — Self-Diagnosing, Self-Healing Incident Response Agent

**Hackathon:** WeMakeDevs x SigNoz — Track 01 (AI & Agent Observability)

---

## Problem

When an incident hits production, the loop looks the same everywhere: an alert fires,
an engineer gets paged, they open a dashboard, manually correlate metrics/logs/traces
with recent deploys, form a hypothesis, apply a fix, watch to confirm it worked, and —
if there's time — write up what happened. That loop is slow, manual, and the
postmortem step is usually the first thing to get skipped under pressure, which means
the same class of incident recurs.

Sentinel closes that loop end-to-end, autonomously, with a human approval gate before
any write action.

## Solution

Sentinel is an agent that sits on top of SigNoz and a target service. When an incident
is detected, it:

1. **Investigates** — pulls real trace/log/metric data from SigNoz for the affected
   service (error rates, latency, span attributes).
2. **Correlates with deploy history** — cross-references the incident window against
   recent deploys to find the likely triggering change, instead of just describing
   symptoms.
3. **Proposes a fix** — states its hypothesis and the specific remediation action it
   wants to take, citing the real numbers it found (not guessed).
4. **Waits for human approval** — no write action happens without an explicit yes.
   This is a hard requirement, not a suggestion.
5. **Applies the fix** — calls the actual remediation tool against the running service.
6. **Verifies recovery** — re-queries the system after the fix to confirm the incident
   is actually resolved, not just assumed resolved.
7. **Writes the postmortem** — root cause, cost/impact, fix applied, verification
   evidence, and a concrete prevention step, generated automatically from the real
   data gathered during the run.

## Architecture

```
                       ┌─────────────────────┐
   Incident fires ───▶ │   Claude Desktop     │
   (SigNoz alert)      │  (chat-driven agent) │
                       └──────────┬───────────┘
                                  │  MCP (stdio, via wsl.exe)
                 ┌────────────────┴─────────────────┐
                 ▼                                   ▼
      ┌─────────────────────┐            ┌───────────────────────┐
      │  signoz MCP server    │            │  sentinel-tools MCP    │
      │  (SigNoz's own MCP,   │            │  server (ours, FastMCP)│
      │  via mcp-remote       │            │  - get_deploy_history  │
      │  bridge, read-only    │            │  - reset_connection_pool│
      │  investigation tools) │            │  (write, needs approval)│
      └──────────┬────────────┘            └───────────┬────────────┘
                 │                                       │
                 ▼                                       ▼
         SigNoz (traces/logs/metrics)          Demo app (Flask checkout API,
         self-hosted via Foundry               simulated breakable connection pool)
```

Human approval happens through Claude Desktop's **native** per-tool permission
dialog — every call to a write-capable tool (`reset_connection_pool`) requires
explicit user approval before it executes. No custom approval UI was needed.

## SigNoz Usage

- **Instrumentation:** OpenTelemetry auto-instrumentation (`opentelemetry-instrument`)
  plus manual spans (`db.pool.acquire`, `db.query`) added directly around the
  connection-pool logic, so the agent can point at real span attributes
  (`db.pool.exhausted`, `db.pool.in_use`) instead of only generic HTTP timing.
- **Alerting:** a SigNoz alert rule (`checkout-service-high-error-rate`) fires on
  `service.name = 'checkout-service' AND hasError = true`, count > 5 in a rolling
  5-minute window, checked every minute.
- **MCP server:** SigNoz's own MCP server exposes read-only investigation tools
  (list services, search logs/traces) directly to the agent via a local
  `mcp-remote` bridge — this is the "agent observability" surface the track is
  built around.

## Impact

A connection-pool exhaustion incident that would normally take an on-call engineer
several minutes of manual dashboard-hopping to diagnose, correlate with a deploy,
and fix — Sentinel does in a single approved conversational turn, with a written
postmortem as a byproduct instead of an afterthought.

## Demo

**This was run live, start to finish, in a real Claude Desktop conversation — not simulated.** Full recording available (see submission).

Real results from the actual run:
- Root cause correctly identified: deploy #47 (`devops-bot`) reduced checkout-service's DB connection pool from 20 → 3 as a "cost-optimization" change — correctly distinguished from the unrelated later deploy #48
- Failure rate during the incident: **~27% of requests failing** (171/625 sampled) due to `db.pool.acquire` timeouts
- Fix applied and verified live: pool restored to 20, **0% failure rate** confirmed across 20 freshly-sampled real requests post-fix
- A new, smarter prevention alert (`checkout-service-pool-exhaustion-early-warning`) created directly in SigNoz, targeting the root-cause signal instead of just the downstream symptom
- Full postmortem generated automatically — see [`docs/checkout-service-postmortem-2026-07-25.md`](docs/checkout-service-postmortem-2026-07-25.md)

Demo script (matches what actually happened):
1. Trigger the incident (`POST /admin/break-pool`, run load generator) → SigNoz alert fires.
2. Open the conversation with Sentinel in Claude Desktop, tell it an alert fired.
3. Watch it investigate via SigNoz MCP tools, correlate with deploy #47, propose the fix with cited evidence.
4. Approve the fix via the native permission dialog.
5. Watch it call `verify_recovery` and confirm 0% failure rate on real sampled traffic.
6. Watch it create a targeted prevention alert directly in SigNoz.
7. Ask it to write the full postmortem.

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd sentinel-demo-app

# 2. Python environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
opentelemetry-bootstrap -a install

# 3. Run the demo app with OTel instrumentation
export OTEL_SERVICE_NAME=checkout-service
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_TRACES_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
opentelemetry-instrument python app.py

# 4. Stand up SigNoz locally (separate terminal)
foundryctl cast -f casting.yaml

# 5. Wire Claude Desktop's config (see docs/claude_desktop_config.example.json)
#    - sentinel-tools: local MCP server exposing get_deploy_history / reset_connection_pool /
#      verify_recovery / create_alert_rule
#    - signoz: SigNoz's MCP server via a custom lightweight proxy (sentinel_signoz_proxy.py),
#      API key passed as a server-side env var (never commit the raw key)
#    - NOTE: the example config uses "wsl.exe" as the command wrapper because this was built
#      on Windows+WSL2. On native macOS/Linux, replace the "command"/"args" wrapper with a
#      direct call, e.g.: "command": "bash", "args": ["-c", "cd ~/sentinel-demo-app && ..."]

# 6. Trigger the incident
curl -X POST http://localhost:5000/admin/break-pool -H "Content-Type: application/json" -d '{"size": 3}'
python load_generator.py --workers 40 --duration 8

# 7. Open Claude Desktop and start the conversation with Sentinel
```

## What's Next

- Wider incident library beyond connection-pool exhaustion (memory leaks, N+1 query
  regressions, dependency timeouts)
- Automatic creation of a tighter, more targeted alert rule as a prevention step,
  written directly back into SigNoz via MCP
- Slack/webhook delivery of the postmortem, not just an in-chat artifact
- Multi-service correlation (right now scoped to a single demo service)

## Alternative Approaches Explored

This repo also includes two earlier implementations we built and tested before
landing on the Claude Desktop + local MCP server approach used in the final demo:

- **`agent.py`** — a scripted agent using Anthropic's API directly with native
  remote-MCP-server support, plus a free `SENTINEL_MOCK=true` mode for zero-cost
  testing of the full flow without live API calls.
- **`gemini_agent.py`** — a port to Google's free-tier Gemini API (no credit card
  required), connecting to SigNoz's MCP server directly via the standalone `mcp`
  Python client library.

We switched to the Claude Desktop approach because it removed API billing entirely
(free plan, no card) and gave us a native human-approval gate for free (Desktop's
per-tool permission dialog), instead of building custom approval logic. Kept here
because the debugging trail — including a real bug we found and worked around in
the `mcp-remote` bridge tool (see `sentinel_signoz_proxy.py`'s docstring) — reflects
real engineering decisions made under time constraints, not just the final answer.


## AI Assistance Disclosure

This project was built, designed, and implemented by Amulya Suhane. AI assistance
(Claude) was used minimally — mainly for debugging help and polishing documentation
wording. All architecture decisions, the SigNoz integration, and the MCP servers were
conceived and built independently. The live demo and testing were run in Claude
Desktop, which also serves as the agent runtime for the project itself.

---

*Built by Amulya Suhane for WeMakeDevs x SigNoz, Track 01.*
