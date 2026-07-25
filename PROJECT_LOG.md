# Sentinel — Project Log & Context

**Purpose of this file:** running record of every decision made, file created, and step completed on this project. If you switch to a different AI agent/assistant, paste this whole file as context so they can pick up exactly where we left off — no re-explaining needed.

**Hackathon:** WeMakeDevs x SigNoz — Track 01 (AI & Agent Observability)
**Project:** Sentinel — self-diagnosing, self-healing incident response agent
**Status as of last update:** 🎉 **ENGINEERING BUILD FULLY COMPLETE.** Every capability proven live in a real Claude Desktop conversation: diagnose → correlate deploy → propose fix → human approval → apply fix → verify recovery (0% failure) → create prevention alert (real SigNoz rule). Now shifting entirely into demo prep: backup recording, README polish with real numbers, rehearsal.

**Session resumed (new agent picking up context):** Direct `"type": "http"` syntax for wiring SigNoz's MCP server into `claude_desktop_config.json` **failed** (as flagged as a risk in the prior entry). Confirmed fallback path now in progress: wrap SigNoz's HTTP MCP server using the `mcp-remote` npm bridge package, spawned the same `wsl.exe` + `bash -c` way as `sentinel-tools`. Full new config block prepared, pending: (1) confirm Node.js present in WSL, (2) full config file replace, (3) paste real SigNoz API key, (4) full Claude Desktop restart + Connectors check.

**Session resumed again (2026-07-24, third agent picking up context):** The Claude Desktop instance being used for live rehearsal **hit its usage limits mid-session** — no ability to run further live tests tonight. Picking up strictly from the last thing that Claude Desktop actually did (per screenshots), not re-deciding anything upstream of that.

**Session resumed yet again (2026-07-24, fourth agent picking up context, via screenshots handoff):** Confirmed the 403 fix is real (new key, `HTTP 200`, correct `signoz-admin` role). Picking up exactly at the config-file step the prior agent specified — server-side env var, not inline header — and continuing to build/polish while live-testing stays deferred to tomorrow, per standing plan below.

**Config step closed out (2026-07-24, same session):** `claude_desktop_config.json` edited and saved with the env-var version of the `signoz` block, confirmed correct via screenshot (quoting, substitution syntax, comma placement, `sentinel-tools` untouched). **Not restarted on purpose** — Desktop restart + live verification is tomorrow's task.

**Session resumed yet again (2026-07-24, fifth agent picking up context, via chat handoff — previous Claude Desktop session hit its message limit mid-build):** Confirmed via screenshots that the no-Desktop build queue was in progress in this order: README → postmortem template → verify-recovery logic → engineering polish → prevention-step logic. Verified the three uploaded files are actually complete (not partial): `README.md`, `POSTMORTEM_TEMPLATE.md`, `verify_recovery_tool.py`. Picking up exactly at "engineering polish," which is where the prior session's message got cut off.
- [x] **Drafted `create_alert_rule_tool.py`** (Phase 5, prevention-step logic) — same drop-in pattern as `verify_recovery_tool.py`. Builds a targeted SigNoz alert rule (e.g. on `db.pool.exhausted` directly, not just downstream error rate) as the "Prevention → Immediate" action the postmortem cites. **Not live-tested** — SigNoz Rules API request shape is drafted from documented schema, needs a real curl/live test tomorrow before demo. Flagged clearly in the file's own docstring so nobody mistakes it for verified.
- **← YOU ARE HERE:** Engineering polish is the one remaining pre-Desktop item, and it needs the actual repo files (`app.py`, `agent.py`, `gemini_agent.py`, `sentinel_mcp_server.py`, `casting.yaml`, `claude_desktop_config.json`, `requirements.txt`) to do the secret-scrub and folder-cleanup safely — none of these were in this session's uploads. **Decision made now, not deferred:** `agent.py` and `gemini_agent.py` are KEPT in the repo, documented as an alternate/fallback path in the README (not the primary path), not deleted — cutting working code under a tight deadline for polish reasons alone is a bad trade, and they already demonstrate MOCK_MODE + multi-provider thinking, which is judge-visible engineering depth, not clutter.

- [x] **First live rehearsal actually ran.** Agent called SigNoz MCP tools (`Signoz list services`, `Signoz search logs`) — **all failed** with `403: only viewers/editors/admins can access this resource`. This is a SigNoz-side auth/role issue on the connector, not a bad query, not an MCP wiring problem (wiring was already confirmed live in the prior session).
- [x] `get_deploy_history` (our own `sentinel-tools` server) worked correctly and the agent correctly surfaced deploy #47 (`devops-bot`, pool 20→3, "cost-optimization", JIRA-1182, Jul 23 15:05) as the standout suspicious change — exactly the root-cause story it was designed to find. Deploy #48 (`arjun.k`, new `/checkout/gift-wrap` endpoint, Jul 24 08:30) also came through, unremarkable/no red flag.
- **✅ SigNoz 403 RESOLVED.** Created a new SigNoz Service Account (`sentinel-mcp`) with role `signoz-admin`, generated a new API key (`w6Rr1EA9tuOi9VgOTsOMCUrfhsVNPQccfgIIFGGsV8=`). Verified standalone via `curl -i -H "SIGNOZ-API-KEY: w6Rr1EA9tuOi9VgOTsOMCUrfhsVNPQccfgIIFGGsV8=" http://localhost:8080/api/v1/service_accounts/me` → **HTTP 200**, response confirms key belongs to `sentinel-mcp` with role `signoz-admin` (full admin transaction groups on `auth-domain`, `cloud-integration`, `factor-api-key`, etc.). **The key itself is no longer the problem** — old key/role was the root cause of the 403, now fixed at the SigNoz side.
- **← YOU ARE HERE, for real:** Key is validated. Remaining step is purely local config: wire this new key into `claude_desktop_config.json` for the `signoz` MCP entry — **as a server-side env var, not inline in the `--header` flag** (moving away from the earlier `--header 'SIGNOZ-API-KEY:PASTE_YOUR_REAL_KEY'` inline-secret approach for cleanliness/security), then a full Claude Desktop restart. Restart + live verification is deferred to tomorrow (no Desktop access tonight — hit usage limits mid-rehearsal), but the config file edit itself can and should happen now.
- **Tonight's plan (no live-testing dependency):**
  1. ~~Diagnose/fix the SigNoz 403~~ — **DONE**, see above.
  2. ~~Update `claude_desktop_config.json`~~ — **DONE**, see above.
  3. **Active now — in parallel, no-Desktop-required build queue (priority order):**
     1. Draft submission README (Problem/Solution/Architecture/SigNoz usage/Impact/Demo/Setup) — highest priority, judged deliverable, zero dependencies
     2. Draft postmortem template/format (structure the agent will fill in post-fix — headline, root cause, cost/impact, fix applied, verification, prevention step)
     3. Write the "verify recovery" step logic (agent re-queries SigNoz after fix — can write the tool-call/prompt logic now, test live tomorrow)
     4. Engineering polish: scrub secrets from all config examples/committed files, decide fate of `agent.py`/`gemini_agent.py` (keep as documented "alternative path" or cut), clean repo folder structure
     5. Sketch the "creates a tighter alert rule" prevention-step logic (Phase 5) — can be drafted as MCP tool-call spec now, tested tomorrow
  4. **Explicitly deferred to tomorrow:** full Claude Desktop restart + re-running the actual live rehearsal once Desktop access is available again — do NOT attempt to fake/mock this step tonight, keep it real for tomorrow.

**Session resumed (2026-07-25, sixth agent picking up context, via chat handoff — prior session was mid-way through log cleanup when it got interrupted):** Resumed exactly where the screenshots left off — no upstream decisions re-opened.
- [x] **Log cleanup continued and closed out.** Removed the three obsolete blocks flagged in the prior session (stray duplicate decision list, `GEMINI FALLBACK AGENT` build log, `API PAYMENT OPTIONS` section) — all three were either superseded (payment risk fully closed by the free Claude Desktop path) or already recorded elsewhere (Section 3 + README already document `gemini_agent.py`'s fallback status). 30-HOUR TIME BUDGET section kept as-is, untouched.
- [x] **`sentinel_mcp_server.py`, `verify_recovery_tool.py`, and `agent.py` uploaded** — the actual blocker from the previous entry is resolved.
- [x] **Merged both drop-in tools into `sentinel_mcp_server.py`.** `verify_recovery` and `create_alert_rule` are now real `@mcp.tool()`-decorated functions in the same `FastMCP("sentinel-tools")` instance as `get_deploy_history`/`reset_connection_pool` — no longer standalone files. Added `time` import (for `verify_recovery`'s sample-request pacing) and `SIGNOZ_BASE_URL`/`SIGNOZ_API_KEY` (for `create_alert_rule`, read from env var, not hardcoded). **Syntax-verified** (`py_compile` passes clean).
- **← YOU ARE HERE:** Merged file is ready to drop in locally. Still true and unchanged from before: `create_alert_rule` is **not live-tested** against SigNoz's real Rules API — that's tomorrow's task, same as always. `verify_recovery` has no live-API dependency (`app.py`/`pool.py` only) so it can be smoke-tested as soon as `app.py` is running, no SigNoz needed.
- **Immediate next actions:**
  1. Replace your local `sentinel_mcp_server.py` with the merged version
  2. Restart `sentinel-tools` (local MCP server restart only — not a full Claude Desktop restart) and confirm `verify_recovery` + `create_alert_rule` show up under Tool Permissions
  3. Smoke-test `verify_recovery` locally (app.py running, no SigNoz dependency)
  4. Tomorrow: curl-test `create_alert_rule` against the real SigNoz Rules API before trusting its output in a demo
  5. Then: the deferred full Claude Desktop restart + live rehearsal (signoz key + both new tools) from the earlier "Tonight's plan"

**Session resumed (2026-07-25, back to the original agent, via full log + screenshot handoff):** Read the complete uploaded log (all 327 lines) and adopted it as canonical — no upstream decisions re-opened, no re-litigating past choices. Confirmed understanding of current state: SigNoz 403 fixed (new `sentinel-mcp` service account, `signoz-admin` role), both MCP connectors verified live, `verify_recovery` + `create_alert_rule` tools merged into `sentinel_mcp_server.py` (per description, not yet re-verified against actual file — see below), README + postmortem template drafted.
- **One real gap:** I do not have the actual current file contents of `sentinel_mcp_server.py` (merged version), `README.md`, `POSTMORTEM_TEMPLATE.md`, `create_alert_rule_tool.py`, `app.py`, `casting.yaml`, or `claude_desktop_config.json` — only descriptions of what changed. Cannot safely give further line-by-line edits or run syntax checks without the real files. **Requesting these be uploaded** so I can sync and verify before the next live step.
- **Immediate next actions (unchanged from prior session, still accurate):**
  1. Upload current files (see gap above) so I can verify/sync
  2. Restart `sentinel-tools` only (not full Desktop restart) and confirm `verify_recovery` + `create_alert_rule` show up under Tool Permissions
  3. Smoke-test `verify_recovery` locally (app.py running, no SigNoz dependency)
  4. curl-test `create_alert_rule` against the real SigNoz Rules API before trusting it in a demo
  5. Then: the deferred full Claude Desktop restart + live rehearsal (new SigNoz key + both new tools)

**Files uploaded and synced (2026-07-25, same session):** `sentinel_mcp_server.py` (merged version, syntax-verified clean), `create_alert_rule_tool.py`, `POSTMORTEM_TEMPLATE.md`, `README.md`, `claude_desktop_config.json` all received and reviewed.

**🐛 KEY MISMATCH — RESOLVED, correction was backwards initially.** User verified at the source: the config file's key (`w6Rrr1EA9tuOi9VgOTsOMCUrfhsVNPQccfgIIFGGsV8=`, 44 chars, double "r") is the **correct** one. The earlier log entry recording `w6Rr1EA9...` (43 chars, single "r") was itself the typo — not the config file. **Config file confirmed correct as originally uploaded, no change needed.** Lesson: verifying against the log isn't the same as verifying against the source of truth (SigNoz itself) — good that this got checked before a wasted restart cycle.
- **Next action:** proceed with restart `sentinel-tools` → confirm 4 tools appear (`get_deploy_history`, `reset_connection_pool`, `verify_recovery`, `create_alert_rule`) → smoke-test `verify_recovery` → curl-test `create_alert_rule` → full Desktop restart + live rehearsal.

**✅ 4-tool `sentinel_mcp_server.py` confirmed deployed** — `ls -la` showed 10134 bytes (matches merged version), `py_compile` clean.

**🐛 `mcp-remote` bridge confirmed broken, root cause found, replaced entirely.** Symptom: `signoz` connector consistently showed "failed / Server disconnected" when launched BY Claude Desktop, despite a manual standalone terminal test of the exact same command succeeding cleanly once. Retry didn't help. Added `--transport http-only --auth-timeout 60` flags — didn't help either. **Real root cause found via "View Logs":** `Fatal error: ServerError: HTTP 404: Invalid OAuth error response: SyntaxError: Unexpected non-whitespace character...` at `registerClient → authInternal → auth`. `mcp-remote` was attempting **OAuth dynamic client registration** against SigNoz's MCP endpoint (which only needs a simple API-key header, no OAuth), got a plain 404 back instead of JSON, and crashed trying to parse it. This is a known rough edge in `mcp-remote`'s auth-fallback logic, not fixable via flags in the time available.
- **Decision: dropped `mcp-remote` entirely.** Built `sentinel_signoz_proxy.py` — a custom, minimal Python MCP proxy using the low-level `mcp.server.lowlevel.Server` class (not `FastMCP`, since tool schemas aren't known ahead of time — this generically forwards `list_tools`/`call_tool` to whatever SigNoz exposes). Connects to SigNoz via `mcp.client.streamable_http.streamablehttp_client` with ONLY the `SIGNOZ-API-KEY` header — no OAuth code path exists in this file at all, so the `mcp-remote` bug class is structurally impossible here.
- Verified: all MCP SDK APIs used (`Server.list_tools()`, `Server.call_tool()`, `stdio_server`, `create_initialization_options`) actually exist with matching signatures (checked via `inspect.signature`, not assumed). `py_compile` clean.
- **⚠️ NOT YET LIVE-TESTED against real Claude Desktop** — built to eliminate a confirmed bug, but this exact file has not been run end-to-end yet. Expect it may need one small fix on first real run.
- `claude_desktop_config.json`'s `signoz` block updated to run `sentinel_signoz_proxy.py` instead of the `npx mcp-remote ...` command. Same `wsl.exe` + `bash -c` wrapper pattern, same env var key-passing approach.
- **✅ MILESTONE: Both `sentinel-tools` AND `signoz` connectors confirmed live and toggled ON in Claude Desktop** — custom `sentinel_signoz_proxy.py` fix worked on first real Desktop test. **Phase 3 (MCP + Agent infrastructure) is now functionally COMPLETE.**
- **🎉 MAJOR MILESTONE: FULL LIVE INVESTIGATION SUCCEEDED, FIRST REAL RUN.** In a real Claude Desktop chat, given only "an alert just fired" as a prompt: correctly used both `signoz` and `sentinel-tools` MCP servers, correctly identified deploy #47 (not the newer #48) as root cause using real timestamp/count evidence from actual trace data, proposed a specific fix (reset pool to 20) with reasoning, and **correctly stopped and asked for explicit human approval before taking any write action** — the safety gate worked exactly as designed, unprompted.
- **🎉🎉 CORE REMEDIATION LOOP CONFIRMED WORKING END-TO-END, LIVE, REAL DATA:** `reset_connection_pool` called (approved via native permission dialog) → pool resized 3→20 → `verify_recovery` automatically called after → **confirmed 0% failure rate across 20 real sampled live `/checkout` requests**. This is the project's core "money shot" fully proven, not simulated.
- **Alert rule creation failed on first live attempt** — error: `SIGNOZ_API_KEY not set in environment`. **Root cause found:** `create_alert_rule` lives inside `sentinel_mcp_server.py` (the `sentinel-tools` MCP server process), but `SIGNOZ_API_KEY` was only set in the **`signoz`** block's environment in `claude_desktop_config.json`, not the **`sentinel-tools`** block's — two separate spawned processes, two separate environments, setting the var in one doesn't share it with the other. **Fixed:** added the same `export SIGNOZ_API_KEY=...` to the `sentinel-tools` command chain too.
- **`create_alert_rule` failed differently — real progress, real bug found.** Auth issue fully resolved (env var fix worked), but got **`400 Bad Request`** from SigNoz's Rules API this time — a genuine payload-shape mismatch, not a transient error. **Notably, the agent handled this correctly per its system prompt:** it explicitly said "No alert rule has been created," refused to fabricate a rule ID, and asked for guidance — the "cite real numbers, don't guess" rule held up under a real failure, not just in happy-path testing. Worth highlighting to judges as a feature, not hiding as a bug.
- **Root cause researched and fixed:** found a confirmed-working example payload in SigNoz's own GitHub issue tracker (a user who got real `HTTP 200, status: success`). Our drafted payload was missing several required fields: `ruleType`, `version`, `panelType`, `stepInterval`, `aggregateAttribute` object, and used an invalid `matchType` value (`"count"` instead of the correct numeric-string code `"4"`). **Fixed in `sentinel_mcp_server.py`'s `create_alert_rule` function** — rebuilt the payload to match the confirmed-working shape.
- **Known simplification made under time pressure:** rather than parsing the free-text `metric_query` string into SigNoz's structured filter-item format (which needs exact attribute key/dataType/type metadata we don't have readily available), the fix uses an **empty filter** (matches the proven-working example) and puts the human-readable intended condition into the rule's `annotations.description` field instead. This means the created rule will technically alert on "count of all traces" rather than the specific `db.pool.exhausted` condition — functional and demoable, but not semantically complete. Flagged clearly in code comments. Acceptable tradeoff given remaining time; revisit if time allows.
- **Direct curl retest of the fixed payload also failed** — response: `{"status":"error","errorType":"bad_data","error":"alert rule is not valid"}`. Generic error, no field-level detail to iterate on further.
- **PIVOT — stopped guessing at a custom payload entirely.** Realized: SigNoz's own MCP server (the `signoz` connector, already confirmed live) exposes `signoz_create_alert` as one of its ~15 built-in tools — SigNoz's own officially-maintained implementation. No reason to keep debugging our own hand-built `/api/v1/rules` payload when the correct, schema-safe version already exists and is already connected. **Decision: deprecate our custom `create_alert_rule` tool for the demo; instruct the agent to use `signoz_create_alert` (SigNoz's own tool) instead.**
- **🎉🎉🎉 FULL END-TO-END SUCCESS — ENGINEERING BUILD COMPLETE.** Pivoted to SigNoz's native `signoz_create_alert` tool → succeeded on first real attempt, with a genuinely useful validation error surfaced along the way (`invalid order by key`, self-corrected) proving SigNoz's own tool gives actionable feedback where our custom one didn't. Real rule created: `checkout-service-pool-exhaustion-early-warning` (id `019f989e-d79a-7cf3-94b4-9511575c608d`), correctly scoped to fire on the root-cause signal (`db.pool.acquire` errors) rather than just the generic downstream error rate — a smarter, earlier-warning alert than the original one. Agent also correctly flagged JIRA-1182 (the deploy that caused this) as a human follow-up item it can't act on itself, rather than overclaiming.
- **Every planned capability now proven live, in one real Claude Desktop conversation:** investigate (SigNoz MCP) → correlate with deploy history (sentinel-tools) → hypothesize with real evidence → propose fix → wait for human approval (native permission dialog) → apply fix (`reset_connection_pool`) → verify recovery (`verify_recovery`, real sampled traffic, 0% failure) → create prevention alert (`signoz_create_alert`) → full incident wrap-up summary.
- **✅ Real postmortem generated by the agent and saved to repo** at `docs/checkout-service-postmortem-2026-07-25.md` — matches the template structure closely (Summary/Root Cause/Impact/Fix/Verification/Prevention/Timeline/Action Items), cites real numbers throughout (171/625 requests failed, ~27%; 0% post-fix across 20 samples; real alert rule ID), correctly separates "done by the agent" action items from "open, needs a human" ones (JIRA-1182 re-evaluation).
- **✅ Backup video recorded by user** of the full successful live run — insurance against live-demo flakiness.
- **✅ README updated** — Demo section now shows the real proven numbers instead of a placeholder script, links directly to the real postmortem file.
- **✅ Repo-cleanliness decision made:** keeping `agent.py`, `gemini_agent.py`, `requirements-gemini.txt`, `create_alert_rule_tool.py` in the repo rather than deleting them. Added a new "Alternative Approaches Explored" README section explaining why we pivoted and what we learned — framing the debugging journey (mcp-remote bug found/fixed, payload iteration, etc.) as a sign of real engineering work, not something to hide.
- **← YOU ARE HERE:** Engineering + demo artifacts are now both complete. Remaining work is pure rehearsal/logistics:
  1. Full timed rehearsal of the live demo flow, 2-3 times
  2. Quick secrets scan before any repo push (confirm `claude_desktop_config.json` with the real API key isn't accidentally included in whatever gets submitted/pushed — it should stay a local-only file, not part of the repo)
  3. Final submission logistics (repo link, video link, any required form fields)

**PRE-SHIP REVIEW (final pass before GitHub push) — found and fixed 3 real gaps that would have broken a fresh clone:**
1. **`requirements.txt` was missing the `mcp` package** — both `sentinel_mcp_server.py` and `sentinel_signoz_proxy.py` import it; anyone cloning and running `pip install -r requirements.txt` would hit `ModuleNotFoundError` immediately. Fixed.
2. **`casting.yaml` was never actually part of the repo folder** — it lived in `~` on the dev machine, separate from `~/sentinel-demo-app`, even though the README's setup steps reference running `foundryctl cast -f casting.yaml` from the repo. Reconstructed and added `casting.yaml` to the repo root from the known-correct content established earlier in this project.
3. **README referenced `docs/claude_desktop_config.example.json` which didn't exist** — only the real, gitignored config existed. Created a proper placeholder-key example template at that path so others have something to actually copy.
- Also cleaned up stray `server.log` (325KB, leftover from early testing) and `__pycache__/` before final packaging — neither belongs in a submitted repo.
- Added a portability note in the README flagging that the `wsl.exe` command wrapper in the example config is Windows+WSL-specific, with a one-line pointer for macOS/Linux users to adjust it.
- **Cross-checked every file the README references by name against what's actually in the folder** — all confirmed present after the fixes above.
- **✅ NOW GENUINELY READY FOR GITHUB SUBMISSION.** Use `PROJECT_LOG_PUBLIC.md` (redacted) instead of `PROJECT_LOG.md` (has real key in debugging history) if including the log in the public repo. `claude_desktop_config.json` stays gitignored/local-only.

> ⚠️ **STANDING RULE — every new terminal window needs this FIRST, before any other command:**
> ```bash
> cd ~/sentinel-demo-app
> source venv/bin/activate
> ```
> Confirm the prompt shows `(venv)` before running anything else. WSL always opens new terminals in `/mnt/c/WINDOWS/system32` by default, not the project folder — this has caused repeated `command not found` / `No such file or directory` errors. Two terminals are needed simultaneously going forward (one running the app, one for curl/load commands) — both need this activation step done separately.

---

## ✅ PROGRESS CHECKLIST (master tracker — update this every step)

### Phase 1 — Foundation
- [x] Build demo app (Flask checkout API) with breakable connection pool
- [x] Manually verify: break pool + load test → real failures (~24-27% fail rate)
- [x] Manually verify: reset pool + load test → recovery (0% fail rate)
- [x] Install SigNoz locally via Foundry (`foundryctl cast`)
- [x] Confirm SigNoz UI loads (`localhost:8080`)
- [x] Create SigNoz workspace account
- [x] Add OTel manual spans to `pool.py` (`db.pool.acquire`, `db.query`)
- [x] Set up WSL environment (Python, pip, venv)
- [x] Install project dependencies + `opentelemetry-bootstrap -a install`
- [x] Fix Docker Desktop WSL integration (`docker ps` now works from WSL)
- [x] Start stopped SigNoz containers, confirm OTLP port 4317 bound correctly
- [x] First data flow confirmed (ingestion active, Services table showed real error rate/latency)
- [x] Fixed `unknown_service` naming issue (killed stale process on port 5000, clean re-run with env vars)
- [x] **Phase 1 COMPLETE:** Confirmed `checkout-service` traces in SigNoz with both `GET /checkout` (HTTP, with real status codes) and `db.pool.acquire`/`db.query` (DB) spans. `opentelemetry-instrumentation-flask` + `wsgi` confirmed installed.

### Phase 2 — Alerting
- [x] Created SigNoz alert rule on Traces tab: `service.name = 'checkout-service' AND hasError = true`, `count()`, threshold ABOVE 5 during Last 5 minutes Rolling, checked every 1 minute. Named `checkout-service-high-error-rate`.
- [x] SigNoz requires a notification channel to save any rule (no "skip" option) — created a free **webhook.site** channel (no signup needed) to satisfy this requirement for the hackathon. That tab also doubles as a live viewer to visually confirm alerts fire.
- [x] Confirmed alert fires correctly after retriggering the incident (break-pool + load test)
- [x] **Phase 2 COMPLETE**

### Phase 3 — MCP + Agent
- [x] Base `casting.yaml` confirmed (SigNoz core stack, no MCP block yet)
- [x] `mcp:` block correctly added and indented under `spec:` in `casting.yaml` (confirmed via `cat casting.yaml` — matches expected structure exactly)
- [x] Run `foundryctl cast -f casting.yaml` — succeeded, `signoz-mcp` container started (image `signoz/signoz-mcp-server:latest`)
- [x] Verified MCP server live: `curl -fsS localhost:8000/livez` → `ok OK`
- [x] Create API key (SigNoz Service Account, Admin role)
- [x] **Built `agent.py`** — the core Sentinel agent. Connects to SigNoz's MCP server (read-only diagnosis tools) + one local write-capable tool (`reset_connection_pool`, calls the app's `/admin/reset-pool` endpoint). Implements the full loop: investigate → hypothesis → propose fix → **wait for human approval (CLI prompt)** → apply fix → verify recovery → postmortem. System prompt encodes the strict order and "cite real numbers, don't guess" rule.
- [x] Get an Anthropic API key from console.anthropic.com
- [x] **Budget plan locked in for ₹500 total:**
  1. Set a hard **$5 monthly spend limit** in Anthropic console (Settings → Billing/Limits) — API simply stops working past this, cannot overspend. **User action required — only they can set this.**
  2. Added **MOCK_MODE** to `agent.py` (`export SENTINEL_MOCK=true`) — runs the entire agent flow (investigation → approval gate → real fix call → postmortem) with realistic fake reasoning text and **zero API cost**. Use this for ~90% of development/testing.
  3. Real API calls default to **Haiku** (`claude-haiku-4-5-20251001`, cheapest tier, ~$0.03-0.08/run) via `SENTINEL_MODEL` env var — used only for the small number of "does the real API actually work" checks.
  4. Reserve **Sonnet** (`claude-sonnet-5`, `export SENTINEL_MODEL=claude-sonnet-5`) for final rehearsals + the actual live demo only, where answer quality matters most.
  - Tested and confirmed: mock mode runs cleanly end-to-end with zero API key required, including the real local `reset_connection_pool` tool call (fails gracefully with a clear message if the checkout app isn't running, doesn't crash).
- [x] **Added `deploy_history.json`** — 5 fake deploy records; deploy #47 (devops-bot, timestamp matches the incident) intentionally shrinks the pool 20→3 as a "cost-optimization" change, giving the agent a real root-cause story to find, not just symptom data.
- [x] **Added `get_deploy_history` as a second local tool** in `agent.py`, alongside `reset_connection_pool`. System prompt updated with a new step 2 ("CORRELATE WITH DEPLOYS") between investigation and hypothesis. Mock mode updated to match — tested end-to-end, agent now cites the specific deploy in both its hypothesis and postmortem.
- [x] Fixed: local `requirements.txt` was outdated (missing `anthropic`/`requests`) — resolved via direct `pip install anthropic requests`
- [x] Fixed: stale local `agent.py` — re-downloaded current version
- [x] **MOCK MODE FULLY CONFIRMED WORKING END-TO-END**, including the real remediation action: investigation → deploy #47 correlation → hypothesis → proposed fix → human approval (`yes`) → **real** `reset_connection_pool` call → confirmed `{"pool_size": 20, "status": "pool resized (fixed)"}` from the actual running app → mock postmortem. This proves the whole architecture works; only the reasoning text is scripted, not live Claude output.

### PRIMARY PATH (as of last update) — Own local MCP server + Claude Desktop
- [x] Confirmed: Claude Desktop free plan requires no credit card at all (just email/Google account) — solves the payment blocker entirely. **Age note:** Anthropic's terms have a minimum age requirement (exact number not confirmed) — worth a quick check with a parent/guardian on signup terms first.
- [x] Confirmed the correct technical approach: use the **classic local MCP server** method (`claude_desktop_config.json`, stdio transport) — NOT "Custom Connectors" (that feature requires your server to be publicly reachable over the internet from Anthropic's cloud, which a localhost server isn't, without ngrok/tunneling).
- [x] **Built `sentinel_mcp_server.py`** — exposes `get_deploy_history` and `reset_connection_pool` as MCP tools via `FastMCP`, stdio transport. Syntax-checked and confirmed to start cleanly. This is our own app's tools, separate from SigNoz's own MCP server (which is already running on port 8000).
- [x] **MILESTONE: `sentinel-tools` connected successfully in Claude Desktop.** Both tools (`Get deploy history`, `Reset connection pool`) confirmed visible under Tool Permissions, set to "Needs approval" — this is Claude Desktop's **native** per-tool approval gate, which replaces the custom CLI `input()` approval step from `agent.py`/`gemini_agent.py` entirely. No custom approval UI needs to be built.
- [x] Tried direct `"type": "http"` / `"url"` / `"headers"` syntax for SigNoz's MCP server in `claude_desktop_config.json` — **FAILED**, confirmed not viable for this Desktop version.
- [x] Node.js confirmed present in WSL (`node -v` → v22.22.1, `npx -v` → 9.2.0) — no install needed.
- [x] Full `claude_desktop_config.json` replace done — `signoz` block now uses `mcp-remote` bridge (`npx -y mcp-remote http://localhost:8000/mcp --header 'SIGNOZ-API-KEY:...'`), `sentinel-tools` untouched. Verified JSON structure correct (bracket/brace nesting, key format `SIGNOZ-API-KEY:key` no space, single quotes intact).
- [x] Manual `npx mcp-remote ...` test outside Claude Desktop confirmed clean connect (`Connected to remote server`, `Local STDIO server running`, `Proxy established successfully`) — ruled out the command/URL/key itself as the problem.
- [x] Confirmed `curl localhost:8000/livez` → `ok` — SigNoz MCP server reachable from WSL.
- [~] After restart, `+` → Connectors popover showed only `sentinel-tools` toggled on, no visible `signoz` entry — **initially looked like a failure.**
- [x] **Checked `mcp-server-signoz.log` directly — this resolved it.** Log shows: server initialized, full `initialize` handshake completed with client, `tools/list`/`prompts/list`/`resources/list` all responded, and continuous healthy `ping`/`pong` heartbeats every ~20s from 14:52 through at least 14:57 with zero errors. **The `signoz` MCP connector via the `mcp-remote` bridge is confirmed actually connected and alive** — the missing entry in the small `+` popover was a UI/display issue (likely needs scrolling or is under "Manage connectors"/"Tool access" instead), not a real connection failure.
- [x] **UI-confirmed:** Connectors → Manage connectors shows both `sentinel-tools` and `signoz` toggled ON, plus an "Add from signoz" submenu confirming SigNoz's tools loaded correctly. **MILESTONE COMPLETE: both MCP servers (own local tools + SigNoz) are fully connected and live in Claude Desktop.**
- [x] Both connectors confirmed working end-to-end — `sentinel-tools` via Tool Permissions UI, `signoz` via live log inspection AND final UI confirmation in Manage Connectors. **Ready for full live rehearsal:** trigger incident, investigate via both MCP servers, approve fix via the native permission dialog, verify recovery, get postmortem.
- [x] **First live rehearsal attempted.** `sentinel-tools` (`get_deploy_history`) worked, correctly flagged deploy #47 as root cause. `signoz` MCP tools (list services, search logs) **all returned `403: only viewers/editors/admins can access this resource`** — SigNoz-side role/API-key issue on the connector, confirmed not a wiring problem (wiring already verified live in prior session).
- [x] **Fixed the SigNoz 403** — new Service Account `sentinel-mcp`, role `signoz-admin`, new key generated and standalone-verified via curl → **HTTP 200**. Key/role is confirmed no longer the problem.
- [ ] **← YOU ARE HERE:** Update `claude_desktop_config.json`'s `signoz` block — replace the new key into the config using a server-side env var (not inline in `--header`), matching the earlier security recommendation. Save file only, no restart yet.
- [ ] Full Claude Desktop restart + Connectors check to confirm `signoz` reconnects cleanly with the new key. **Deferred to tomorrow** — no Claude Desktop access left tonight (hit usage limits mid-rehearsal).
- [ ] Once restarted and confirmed: re-run full live rehearsal — trigger incident, investigate via both MCP servers (real SigNoz data this time), correlate with deploy #47, propose fix, approve via native permission dialog, verify recovery, get postmortem. **Deferred to tomorrow.**

**⚠️ WSL GOTCHA, READ BEFORE CONFIGURING:** Claude Desktop is a native **Windows** app — it cannot directly spawn a script living inside WSL's filesystem. The config's `command` must call `wsl.exe` as a wrapper. Example `claude_desktop_config.json` entry:
```json
{
  "mcpServers": {
    "sentinel-tools": {
      "command": "wsl.exe",
      "args": [
        "bash", "-c",
        "cd ~/sentinel-demo-app && source venv/bin/activate && python sentinel_mcp_server.py"
      ]
    }
  }
}
```
Config file location on Windows: `%APPDATA%\Claude\claude_desktop_config.json` (create the file/folder if it doesn't exist). Must fully restart Claude Desktop (not just close the window) after editing.

**PREVIOUS version (inline header secret — being replaced, kept here for reference only):**
```json
"signoz": {
  "command": "wsl.exe",
  "args": [
    "bash", "-c",
    "npx -y mcp-remote http://localhost:8000/mcp --header 'SIGNOZ-API-KEY:PASTE_YOUR_REAL_KEY'"
  ]
}
```

**CURRENT version (server-side env var, applying now):** pass the key as an env var to the `bash -c` shell, then reference it inside the header with `${SIGNOZ_API_KEY}` substitution instead of hardcoding the raw key string in the config file.
```json
{
  "mcpServers": {
    "sentinel-tools": {
      "command": "wsl.exe",
      "args": [
        "bash", "-c",
        "cd ~/sentinel-demo-app && source venv/bin/activate && python sentinel_mcp_server.py"
      ]
    },
    "signoz": {
      "command": "wsl.exe",
      "args": [
        "bash", "-c",
        "export SIGNOZ_API_KEY='w6Rr1EA9tuOi9VgOTsOMCUrfhsVNPQccfgIIFGGsV8=' && npx -y mcp-remote http://localhost:8000/mcp --header 'SIGNOZ-API-KEY:${SIGNOZ_API_KEY}'"
      ]
    }
  }
  // ...other existing top-level keys (coworkUserFilesPath, preferences, etc.) stay as-is, untouched
}
```
- [x] Edit the file at `%APPDATA%\Claude\claude_desktop_config.json` on Windows with this new `signoz` block. **Confirmed via screenshot** — `export SIGNOZ_API_KEY=...` + `${SIGNOZ_API_KEY}` substitution, correct quoting, correct comma placement before `coworkUserFilesPath`, `sentinel-tools` block untouched.
- [x] Saved. **Not restarted tonight on purpose** — that verification step is for tomorrow.
- [ ] Note for tomorrow: before the demo, consider moving the raw key out of the config file entirely (e.g. Windows user-level env var set outside the JSON) — this inline `export` is a step better than hardcoding it directly in the `--header` string, but it's still sitting in a plaintext file. Flagged, not blocking.

### 30-HOUR TIME BUDGET (rough, adjust as we go)
- Hours 0-2: Get local MCP server connected to Claude Desktop, confirm tools visible and callable in a live chat
- Hours 2-4: Full live rehearsal: trigger incident → chat with Claude Desktop → investigate via SigNoz MCP + our tools → approve → fix → verify → postmortem, using BOTH MCP servers together
- Hours 4-6: Fix whatever breaks in that first live run (expect at least one real issue, first live test of this exact setup)
- Hours 6-8: Write submission README (can happen in parallel/by teammate if any)
- Hours 8-10: Polish — clean repo, remove secrets, remove dead code paths (decide whether to keep agent.py/gemini_agent.py in the repo as "alternative implementations" or cut them for clarity)
- Hours 10-12: Full dry-run rehearsal of the live demo, timed
- Remaining hours: buffer for sleep, unexpected issues, final rehearsal, submission logistics — **do not schedule new features into this buffer**

> **Note:** the stray duplicate decision list, the "GEMINI FALLBACK AGENT" build log, and the "API PAYMENT OPTIONS" section that used to sit here have been removed as obsolete — payment risk is fully closed (Claude Desktop free plan needs no card), and `gemini_agent.py`'s status (kept in repo, documented as fallback, not primary) is already recorded in Section 3 and the README. Nothing here was still-open or unique to those sections.

### Phase 4 — Remediation loop
- [x] Build `/admin/reset-pool` endpoint (done early, already tested)
- [x] Give agent a tool definition to call this endpoint (`reset_connection_pool`, both in `agent.py` and as an MCP tool in `sentinel_mcp_server.py`)
- [x] Human-approval gate — superseded by Claude Desktop's native per-tool permission dialog (PRIMARY PATH decision above), not a custom chat UI
- [x] Add "verify recovery" step — `verify_recovery` merged into `sentinel_mcp_server.py` as an MCP tool; samples real post-fix `/checkout` requests + `/admin/pool-status`, no SigNoz dependency

### Phase 5 — Reporting & polish
- [x] Postmortem doc template drafted (`POSTMORTEM_TEMPLATE.md`) — agent fills real values in, refuses to guess a field it can't source. **Not yet wired to actually run inside agent.py/sentinel_mcp_server.py flow — that wiring is still open, see "Still open" below.**
- [x] Prevention-step logic drafted (`create_alert_rule_tool.py`) — creates a targeted new alert rule via SigNoz's Rules API. **Not live-tested, needs real curl test tomorrow.**
- [ ] Build real chat UI (reasoning / data / action / approval / report sections) — **not needed**: Claude Desktop's native chat + native per-tool permission dialog already covers this (see PRIMARY PATH decision), so this item is superseded, not pending.
- [ ] Rehearse full demo flow 3x — blocked on tomorrow's Desktop restart/live rehearsal, can't be done tonight.
- [x] Submission README drafted (`README.md`) — Problem/Solution/Architecture/SigNoz usage/Impact/Demo script/Setup all present. Demo recording link still a placeholder, to be added closer to submission.

### Engineering quality checklist (from original plan, do before submission)
- [ ] Clean repo structure (folders for demo app / agent / UI) — **deliberately skipped**, low value for time cost given everything's demo-proven; flat structure with a `docs/` folder for postmortem is good enough
- [x] Proper root README — done, real numbers, links real postmortem
- [x] Error handling in agent's tool-calling loop — **reviewed, confirmed adequate**: every tool in `sentinel_mcp_server.py` and `sentinel_signoz_proxy.py` wraps its external calls in try/except and returns a clear error dict rather than crashing; confirmed live during the actual demo run (agent correctly reported failures instead of crashing when `create_alert_rule` hit real errors)
- [ ] Basic tests around remediation endpoint — **deliberately skipped**, real time cost vs. low judging value; the endpoint was manually verified extensively throughout this whole build (see all the break-pool/load-test cycles above) — that's real coverage, just not automated
- [x] No hardcoded secrets committed — **verified via actual `grep` scan**, not assumed: no `.py` file contains the real key, all use `os.environ.get()`. Added `.gitignore` excluding `claude_desktop_config.json` (the one local file with the real key). Also created `PROJECT_LOG_PUBLIC.md` — a redacted copy of this log with all real/typo key strings replaced, safe to include in a public repo if desired (this internal working copy should NOT be pushed as-is)
- [x] Code comments on non-obvious parts — reviewed: every file has docstrings explaining the "why," especially the tricky bits (WSL/wsl.exe wrapper, mcp-remote bug workaround, payload simplification tradeoffs)
- [x] **Decision closed:** `agent.py`/`gemini_agent.py` stay in the repo, documented in the README as an alternate/fallback path (not primary) — not cut.

### Still open (needs the actual repo files to act on — not resolvable from chat alone)
- [x] `agent.py` and `sentinel_mcp_server.py` uploaded (plus `verify_recovery_tool.py`). Still missing for the full polish pass: `app.py`, `gemini_agent.py`, `casting.yaml`, `claude_desktop_config.json`, `requirements.txt`.
- [x] Copied `verify_recovery_tool.py`'s function into `sentinel_mcp_server.py` — merged, syntax-verified.
- [x] Copied `create_alert_rule_tool.py`'s function into `sentinel_mcp_server.py` the same way — merged, syntax-verified. Still needs its live SigNoz Rules API test tomorrow.

---

## 1. The Core Idea (locked, not up for debate)

Closed-loop agent: **Alert → Diagnose → Quantify Cost → Propose Fix → Human Approves → Agent Fixes It → Verify Recovery → Auto-Write Postmortem.**

Full original plan is in `incident-response-agent-plan.md` (the source document this project is built from). That doc has the full demo script, judging angle, risks/mitigations, and README structure — refer to it for anything not covered in this log.

## 2. Tech stack decisions made so far

| Layer | Decision |
|---|---|
| Demo app language | **Python** (Flask) |
| "DB" for the demo | **Simulated** connection pool (not a real Postgres) — a `threading.Semaphore`-based pool class. Chosen deliberately to avoid any external DB dependency that could break during the hackathon. Fully controllable. |
| Observability backend | **SigNoz**, self-hosted via Docker using the new **Foundry** tool (`foundryctl` + `casting.yaml`), not the old `install.sh` script |
| Instrumentation | **OpenTelemetry** — auto-instrumentation via `opentelemetry-instrument` wrapper + a few **manual spans** added by hand around the pool logic (see below) |

## 3. Files created so far (all in project folder `sentinel-demo-app/`)

- **`app.py`** — Flask API. Endpoints:
  - `GET /checkout` — the main simulated business endpoint, uses the pool
  - `GET /health` — liveness check
  - `POST /admin/break-pool` — manually shrink pool size (used by us to seed the incident)
  - `POST /admin/reset-pool` — restore pool size (this is the endpoint the AGENT will call later as its remediation action)
  - `GET /admin/pool-status` — see current pool size / in-use / stats
  - Threaded mode enabled (`threaded=True`) — required for concurrent load to actually stress the pool
- **`pool.py`** — `ConnectionPool` class simulating a real DB connection pool (bounded, blocking acquire, timeout, release). Default `checkout_timeout=0.5s` (tuned down from initial 2.0s because 2.0s was too forgiving to produce visible failures under test load).
  - **Manually instrumented with OTel spans**: `db.pool.acquire` (has `db.pool.size`, `db.pool.in_use`, `db.pool.exhausted` attributes) and `db.query` (has `db.statement`, `db.latency_ms`). This is deliberate — it's what will let the agent later point at real trace data and say "42% of spans show pool exhaustion" instead of only seeing generic HTTP timing.
- **`load_generator.py`** — concurrent load generator script to reproduce the incident on demand. `--workers`, `--duration`, `--url` args. Sleep between requests tuned to `0.01s` (down from `0.05s`) to generate enough pressure to actually exceed pool capacity.
- **`requirements.txt`** — `flask`, `opentelemetry-distro`, `opentelemetry-exporter-otlp`, `anthropic`, `requests`
- **`agent.py`** — the Sentinel agent. Uses `client.beta.messages.create()` with `mcp_servers=[...]` (SigNoz MCP, url-type, `authorization_token`) and `extra_headers={"anthropic-beta": "mcp-client-2025-04-04"}`. Has two local tools: `get_deploy_history` (reads `deploy_history.json`) and `reset_connection_pool` (calls the checkout app's `/admin/reset-pool` endpoint via `requests`). Human approval is a simple CLI `input()` prompt for now — good enough for hackathon demo, could become a real UI button later (Phase 5). Includes `MOCK_MODE` (`SENTINEL_MOCK=true`) for zero-cost full-flow testing, and `SENTINEL_MODEL` env var to switch between Haiku (default, cheap) and Sonnet (final demo only).
- **`deploy_history.json`** — 5 fake deploy records for the agent to correlate against. Deploy #47 is the "smoking gun" — timestamp matches the incident, commit message describes shrinking the pool as a cost-cutting change.
- **`sentinel_mcp_server.py`** — **PRIMARY PATH.** Local MCP server (stdio transport, via `FastMCP`) exposing our two tools directly to Claude Desktop. No API key, no billing. Requires `mcp` + `requests` installed.
- **`verify_recovery_tool.py`** — original standalone drop-in source for the `verify_recovery` tool. **Now merged into `sentinel_mcp_server.py`** as a real `@mcp.tool()` function; this file is kept for reference but is no longer what's actually running.
- **`create_alert_rule_tool.py`** — original standalone drop-in source for the `create_alert_rule` tool. **Now merged into `sentinel_mcp_server.py`** as a real `@mcp.tool()` function. **Still not live-tested against SigNoz's real Rules API** — that test happens tomorrow, before this can be trusted in the demo.
- **`POSTMORTEM_TEMPLATE.md`** — the exact structure the agent fills in after every incident (summary, impact, root cause, fix applied, verification, prevention, timeline). Hard rule baked in: unsourced fields say "not determined," never a guessed number.
- **`README.md`** — submission README (Problem/Solution/Architecture/SigNoz usage/Impact/Demo script/Setup/What's next). This is the primary judged deliverable.

## 4. Steps completed so far (chronological)

1. ✅ Built the Flask checkout app with simulated, breakable connection pool
2. ✅ Verified manually: broke pool (size 3) + ran load (40 workers) → **24-27% failure rate**, real "connection pool exhausted" errors in logs
3. ✅ Verified the fix path: called `/admin/reset-pool` → re-ran load → **0% failure rate**. Full before/after loop confirmed working end-to-end, locally, without any observability tooling yet.
4. ✅ Installed SigNoz locally via Foundry (`foundryctl cast -f casting.yaml`, Docker Compose mode). Confirmed container running in Docker Desktop.
5. ✅ Confirmed SigNoz UI loads at `http://localhost:8080`
6. ✅ Added OTel instrumentation to the app (manual spans in `pool.py` + auto-instrumentation via `opentelemetry-instrument` wrapper)
7. ✅ Resolved WSL setup issues (missing pip, wrong working directory, misplaced venv) — see Section 7 (Environment notes) for the full troubleshooting trail
8. ✅ Installed dependencies in a proper venv inside the project folder: `pip install -r requirements.txt` + `opentelemetry-bootstrap -a install`
9. ⏳ **In progress:** run app with `opentelemetry-instrument`, generate load, verify trace/log/metric data lands in SigNoz UI

## 5. Key config values (so nothing has to be re-derived)

```bash
# OTel env vars used to run the app
OTEL_SERVICE_NAME=checkout-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp

# Run command
opentelemetry-instrument python app.py
```

```bash
# Reproducing the incident
curl -X POST http://localhost:5000/admin/break-pool -H "Content-Type: application/json" -d '{"size": 3}'
python load_generator.py --workers 40 --duration 8

# Fixing it
curl -X POST http://localhost:5000/admin/reset-pool -H "Content-Type: application/json" -d '{"size": 20}'
```

SigNoz ports: `8080` (UI), `4317`/`4318` (OTLP ingestion), `8000` (MCP server, not enabled yet).

## 6. Next steps (not done yet)

- [ ] Confirm `checkout-service` appears in SigNoz's Services tab
- [ ] Confirm a broken-pool trace shows the `db.pool.acquire` span with `exhausted: true`
- [ ] Confirm Flask logs are landing in SigNoz's Logs tab (may need extra logging-exporter config — flagged as a possible follow-up)
- [ ] **Phase 2:** Create a SigNoz alert rule (error rate or p99 latency threshold) that fires when the bug is active
- [ ] **Phase 3:** Enable SigNoz MCP server (Step 5 from SigNoz docs — deliberately deferred until now), connect an agent script using the Anthropic API + MCP tool calling
- [ ] Write the agent's system prompt (investigation order, cost reasoning, hypothesis phrasing, approval flow, postmortem writing)
- [ ] Add fake deploy-history file for the agent to correlate "regression started after deploy #47"
- [ ] Build human-approval gate + chat UI (Phase 5)
- [ ] Postmortem generation + auto-create tighter alert rule as prevention step

## 7. Environment notes

- **Dev environment is WSL (Windows Subsystem for Linux)**, Ubuntu, running under Windows. Terminal defaults into `/mnt/c/WINDOWS/system32` — always `cd ~` first before doing project work, don't work from system32.
- Ubuntu on WSL does **not** ship `pip` by default — needed `sudo apt install python3-pip`.
- Ubuntu 24+ enforces PEP 668 (externally-managed-environment) — plain `pip install` may be blocked. **Fix: use a venv** (`python3 -m venv venv && source venv/bin/activate`) rather than `--break-system-packages`, so the environment stays clean and reproducible.
- **Project files are distributed as a zip** (`sentinel-demo-app.zip`) for one-shot download instead of individual files, to avoid WSL path confusion.
- **Recurring issue (fixed):** commands were repeatedly run from the wrong directory (system32, then home `~` instead of `~/sentinel-demo-app`, then a fresh terminal defaulting back to system32). **Standing rule now in place at top of this doc: always `cd ~/sentinel-demo-app && source venv/bin/activate` first in any new terminal, confirm `(venv)` appears in the prompt before running anything else.**
- **Docker Desktop WSL integration was initially off for the specific distro** (master toggle alone wasn't enough — had to also enable the per-distro toggle in Settings → Resources → WSL Integration, then `wsl --shutdown` from PowerShell + reopen terminal for it to take effect). `docker ps` now runs successfully from WSL.
- **Root cause of the original `4317` connection-refused error, finally found:** SigNoz's Docker containers (7 total: clickhouse, postgres, keeper, otel-collector/ingester, signoz core, migrator, user-scripts) were simply **not running** — `docker ps -a` showed them all `Exited`. Fixed with `docker start $(docker ps -a --filter "name=signoz" --format "{{.Names}}")`. Confirmed port binding afterward: `signoz-ingester-1` correctly shows `0.0.0.0:4317-4318->4317-4318/tcp`.
- **First successful end-to-end data flow confirmed:** ran app with OTel env vars + `opentelemetry-instrument`, ran load test (0% → 29.6% failure rate on broken pool), and SigNoz Home page showed "Logs/Traces/Metrics ingestion is active" with real numbers in the Services table (P99 568ms, error rate 14.03%).
- **Two follow-up issues found when checking the Explorer UI:**
  1. Traces/Logs Explorer defaulted to "Last 30 minutes" and showed empty because enough time had passed since the load test — **not a real bug**, just need to widen the time range (Last 6 hours / Last 1 day) to see historical data.
  2. Service name showed as **`unknown_service`** instead of `checkout-service` in the Services table — meaning `OTEL_SERVICE_NAME` wasn't set in whichever terminal session produced that data (recurrence of the "new terminal, forgot env vars" pattern). Fix: redo the full env-var-export + run + load-test sequence in one clean session, then re-check the Services table shows `checkout-service`.
- Final known-good sequence:
  ```bash
  cp /mnt/c/Users/hp/Downloads/sentinel-demo-app.zip ~/
  cd ~ && unzip sentinel-demo-app.zip && cd sentinel-demo-app
  python3 -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  opentelemetry-bootstrap -a install
  ```

## 8. Open questions / things to decide later

- None blocking right now — flag anything undecided here as we hit it.

---
*This file should be re-downloaded/updated after each major decision or completed step. Ask the assistant to "update the project log" and it will refresh this file.*
