# Postmortem: checkout-service-high-error-rate

**Status:** Resolved
**Date of incident:** 2026-07-25
**Author:** Incident response (Claude + on-call)
**Severity:** High (customer-facing checkout failures)

---

## Summary

The `checkout-service-high-error-rate` alert fired due to widespread failures on `GET /checkout`. Investigation traced the errors to exhaustion of the service's database connection pool, which had been reduced from 20 connections to 3 in a prior "cost optimization" deploy. The pool size was restored and recovery was verified against live traffic. A new alert was created to detect pool exhaustion directly in the future, ahead of the generic error-rate symptom.

---

## Root Cause

Deploy **#47** (2026-07-23T15:05:00Z, author `devops-bot`), titled *"Update infra config: reduce DB connection pool size from 20 to 3 as part of cost-optimization pass (JIRA-1182)"*, modified `infra/db_pool_config.yaml` and cut checkout-service's DB connection pool from 20 connections down to 3.

A pool of 3 connections is far too small for checkout-service's concurrent traffic. Once request concurrency exceeded 3, additional requests queued for a database connection and failed to acquire one in time, surfacing as errors on the `GET /checkout` endpoint.

This was confirmed directly in trace data: error counts on the `db.pool.acquire` span matched error counts on `GET /checkout` exactly, at the same timestamps — indicating the failures were a downstream symptom of pool exhaustion, not an application logic defect.

Deploy **#48** (2026-07-24T08:30:00Z, new `/checkout/gift-wrap` endpoint) added incremental load on top of an already-undersized pool but was not the triggering change.

---

## Impact

- **Affected service:** checkout-service, `GET /checkout` endpoint
- **Symptom:** elevated error rate, triggering the `checkout-service-high-error-rate` alert
- **Mechanism:** requests failing to acquire a database connection from an exhausted pool (max 3 connections)
- **Duration:** from deploy #47 (2026-07-23T15:05 UTC) until the pool was resized during this incident response (2026-07-25)
- **Observed failure volume:** pool stats at time of investigation showed 171 failures out of 625 total requests (~27% failure rate) against the undersized pool

---

## Fix Applied

1. Resized checkout-service's database connection pool from 3 back to 20 connections (reverting the change from deploy #47).
2. This was a configuration-level fix (no code deploy required), making it fast and low-risk to apply.

---

## Verification

- Post-fix pool status confirmed: pool size = 20, 0 connections in use (i.e., not saturated).
- A live sample of 20 real `/checkout` requests was taken after the fix: **0 failures (0% failure rate)**, compared to the ~27% failure rate observed against the exhausted 3-connection pool.
- Verdict: **confirmed recovered.**

---

## Prevention

- **New alert created:** `checkout-service-pool-exhaustion-early-warning`
  - Fires on errors from the `db.pool.acquire` span for checkout-service — the root-cause signal — rather than waiting for the generic downstream error-rate alert to fire.
  - Evaluation: rolling 5-minute window, 1-minute frequency; fires when the error count goes above 1.
  - Routed to the `test-webhook` notification channel; labeled `severity: critical`, `service: checkout-service`, `team: checkout`.
  - This should surface pool-exhaustion issues earlier and more specifically than the current symptom-level error-rate alert.
- **Follow-up recommended:** JIRA-1182 (the original cost-optimization change) should be redone with actual load testing to determine a safe minimum pool size, rather than an arbitrary reduction. Cost-optimization changes to shared infra like connection pools should go through a load/capacity review before rollout.

---

## Timeline

| Time (UTC) | Event |
|---|---|
| 2026-07-23 15:05 | Deploy #47 ships, reducing checkout-service DB connection pool from 20 to 3 (JIRA-1182 cost optimization) |
| 2026-07-24 08:30 | Deploy #48 ships (new `/checkout/gift-wrap` endpoint); adds load on top of the already-undersized pool |
| 2026-07-25 | `checkout-service-high-error-rate` alert fires |
| 2026-07-25 | Investigation begins: deploy history and trace data reviewed |
| 2026-07-25 | Root cause identified: `db.pool.acquire` errors on checkout-service matching `GET /checkout` errors exactly, tracing back to deploy #47's pool size reduction |
| 2026-07-25 | Connection pool reset from 3 to 20 |
| 2026-07-25 | Recovery verified: 0% failure rate across 20 sampled live requests |
| 2026-07-25 | Prevention alert `checkout-service-pool-exhaustion-early-warning` created in SigNoz |

---

## Action Items

| Action | Owner | Status |
|---|---|---|
| Restore DB connection pool to 20 | On-call (via `reset_connection_pool`) | ✅ Done |
| Verify recovery against live traffic | On-call (via `verify_recovery`) | ✅ Done |
| Create pool-exhaustion early-warning alert | On-call (via SigNoz) | ✅ Done |
| Re-evaluate JIRA-1182 with load testing before re-attempting pool size reduction | Infra/DevOps team | ⏳ Open |
| Review other services for similarly unvalidated "cost optimization" infra changes | Infra/DevOps team | ⏳ Open |
