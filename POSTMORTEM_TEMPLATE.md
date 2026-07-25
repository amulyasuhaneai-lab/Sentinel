# Postmortem Template

This is the structure Sentinel fills in automatically after every incident it
handles. Every field must be backed by a real number or real tool result from the
run — no placeholder/guessed values. If a field can't be filled from real data,
the agent should say "not determined" rather than invent a figure.

---

## Postmortem: {incident_title}

**Service:** {service_name}
**Detected:** {alert_fired_timestamp} (SigNoz alert: `{alert_rule_name}`)
**Resolved:** {fix_verified_timestamp}
**Total incident duration:** {duration}
**Severity:** {severity — derived from peak error rate / affected request volume}

### 1. Summary

One or two sentences: what broke, what caused it, what fixed it. No jargon dump —
this is the part a non-on-call reader skims first.

### 2. Impact

- Peak error rate: {value}% (source: SigNoz alert/traces query)
- Affected requests (estimate): {value}
- Duration of degraded service: {value}
- Affected endpoint(s)/service(s): {value}

### 3. Root Cause

- What the investigation found (cite the actual span/log data, e.g.
  "`db.pool.exhausted: true` on {n}% of `db.pool.acquire` spans during the
  incident window").
- The correlated deploy: {deploy_id}, author {author}, timestamp {timestamp},
  description: {deploy_description}.
- Why this deploy is the likely trigger (timestamp alignment + what it changed).

### 4. Fix Applied

- Action taken: {action, e.g. "reset_connection_pool called with size=20"}
- Approved by: {human approver, via Claude Desktop permission dialog}
- Timestamp of fix: {value}

### 5. Verification

- Re-query performed: {what was checked post-fix, e.g. error rate over next
  N minutes, pool status endpoint}
- Result: {value, e.g. "error rate returned to 0% within X minutes of fix"}
- Confidence: {"confirmed recovered" / "partially recovered, monitoring" /
  "could not confirm — escalate to human"}

### 6. Prevention

- Immediate: {e.g. "tighter alert threshold created on X metric"}
- Suggested follow-up (needs human review, not auto-applied): {e.g. "add
  pre-deploy check that blocks pool-size changes below a minimum floor"}

### 7. Timeline

| Time | Event |
|---|---|
| {t0} | Deploy #{n} shipped |
| {t1} | Alert fired |
| {t2} | Sentinel began investigation |
| {t3} | Fix proposed |
| {t4} | Fix approved by human |
| {t5} | Fix applied |
| {t6} | Recovery verified |

---

## Notes for implementation

- Every `{field}` above should map directly to a real value pulled from either
  the SigNoz MCP tool results or the `sentinel-tools` MCP results during that
  run — the postmortem-generation prompt should be instructed to refuse to
  fill a field it can't source, rather than fabricate a plausible-looking
  number. This mirrors the existing system-prompt rule in `agent.py`
  ("cite real numbers, don't guess").
- Output format: generate as Markdown (matches this template), so it can be
  saved directly as a file or dropped into a chat artifact without
  reformatting.
- The "Prevention" section's "immediate" line should only describe an action
  the agent actually took via a tool call (e.g. it really did create a new
  alert rule) — don't let the agent describe an action it merely suggested
  as if it happened.
