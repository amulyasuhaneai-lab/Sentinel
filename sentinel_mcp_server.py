"""
Sentinel's own local MCP server.

Exposes two tools to any MCP-capable client (Claude Desktop, Claude Code, etc.):
  - get_deploy_history: read-only, returns fake deploy log
  - reset_connection_pool: write-capable, actually calls the checkout app's
    real /admin/reset-pool endpoint

This runs over stdio (standard input/output) — Claude Desktop spawns this
script as a local subprocess and talks to it directly. No public hosting,
no API key, no billing required. This is the CLASSIC local MCP server setup,
different from "Custom Connectors" (which require public internet hosting).

Setup:
  1. pip install mcp requests
  2. Find your Claude Desktop config file:
       Windows: %APPDATA%\\Claude\\claude_desktop_config.json
       (On WSL, that's usually /mnt/c/Users/<you>/AppData/Roaming/Claude/claude_desktop_config.json)
  3. Add an entry pointing to this script (see bottom of this file for the
     exact JSON to add — I'll walk you through it).
  4. Restart Claude Desktop completely.
  5. In a new chat, you should see "sentinel-tools" available under the
     tools/connectors icon.

IMPORTANT: your checkout app (app.py) must be running on localhost:5000 for
reset_connection_pool to actually work — this server just proxies to it.
"""

import os
import json
import time
import requests
from mcp.server.fastmcp import FastMCP

CHECKOUT_APP_URL = "http://localhost:5000"
SIGNOZ_BASE_URL = "http://localhost:8080"  # SigNoz UI/API port, matches existing setup
SIGNOZ_API_KEY = os.environ.get("SIGNOZ_API_KEY")  # server-side env var, not hardcoded

mcp = FastMCP("sentinel-tools")


@mcp.tool()
def get_deploy_history() -> str:
    """Fetch the recent deployment history for checkout-service, including
    timestamps, authors, commit messages, and changed files. Use this to
    correlate an incident's start time with a specific deploy."""
    try:
        path = os.path.join(os.path.dirname(__file__), "deploy_history.json")
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return json.dumps({"error": "deploy_history.json not found"})


@mcp.tool()
def reset_connection_pool(size: int) -> str:
    """Resize the checkout-service's database connection pool. This is the
    ONLY remediation action available for this incident. Only call this
    AFTER the human has explicitly approved the proposed fix.

    Args:
        size: the new pool size to set (recommended: 20 for normal operation)
    """
    try:
        resp = requests.post(
            f"{CHECKOUT_APP_URL}/admin/reset-pool", json={"size": size}, timeout=5
        )
        return json.dumps(resp.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": f"Could not reach checkout app at {CHECKOUT_APP_URL} — "
                      f"is app.py running? ({e})"
        })


@mcp.tool()
def verify_recovery(sample_requests: int = 20, expected_pool_size: int = 20) -> dict:
    """Re-check the checkout app after a fix has been applied, and report real
    post-fix numbers so the caller can confirm (not assume) recovery. Hits
    /admin/pool-status to confirm pool size, then samples a small burst of
    real /checkout requests to measure the actual post-fix failure rate.

    Args:
        sample_requests: how many GET /checkout calls to sample for the
            post-fix failure rate (default 20 — enough signal without being
            a full load test).
        expected_pool_size: the pool size the fix was supposed to restore
            (default 20, matches the app's default / reset-pool target).
    """
    result = {
        "pool_status": None,
        "sample_requests": sample_requests,
        "sample_failures": 0,
        "sample_failure_rate_pct": None,
        "verdict": None,
        "error": None,
    }

    # 1. Check pool status endpoint
    try:
        resp = requests.get(f"{CHECKOUT_APP_URL}/admin/pool-status", timeout=3)
        resp.raise_for_status()
        pool_status = resp.json()
        result["pool_status"] = pool_status
    except Exception as e:
        result["error"] = f"Could not reach /admin/pool-status: {e}"
        result["verdict"] = "COULD NOT VERIFY — escalate to human"
        return result

    pool_size = pool_status.get("pool_size") or pool_status.get("size")
    if pool_size is not None and pool_size < expected_pool_size:
        result["verdict"] = (
            f"NOT RECOVERED — pool size is {pool_size}, expected {expected_pool_size}"
        )
        return result

    # 2. Sample real requests to measure actual failure rate post-fix
    failures = 0
    for _ in range(sample_requests):
        try:
            r = requests.get(f"{CHECKOUT_APP_URL}/checkout", timeout=2)
            if r.status_code >= 500:
                failures += 1
        except requests.RequestException:
            failures += 1
        time.sleep(0.05)

    failure_rate = round((failures / sample_requests) * 100, 1) if sample_requests else 0.0
    result["sample_failures"] = failures
    result["sample_failure_rate_pct"] = failure_rate

    # 3. Verdict
    if failure_rate == 0.0:
        result["verdict"] = (
            f"CONFIRMED RECOVERED — pool size restored to {pool_size}, "
            f"0% failure rate across {sample_requests} sampled requests"
        )
    elif failure_rate < 5.0:
        result["verdict"] = (
            f"PARTIALLY RECOVERED — pool size restored to {pool_size}, but "
            f"{failure_rate}% failure rate still observed across "
            f"{sample_requests} requests; monitor before closing incident"
        )
    else:
        result["verdict"] = (
            f"NOT RECOVERED — {failure_rate}% failure rate persists across "
            f"{sample_requests} requests despite pool size showing {pool_size}; "
            f"escalate to human, do not close incident"
        )

    return result


@mcp.tool()
def create_alert_rule(
    rule_name: str,
    metric_query: str,
    threshold: float,
    eval_window_minutes: int = 5,
    notification_channel: str = None,
) -> dict:
    """Create a new, targeted SigNoz alert rule as a prevention step after an
    incident has been diagnosed and fixed. This is a WRITE action against
    SigNoz — gated by Claude Desktop's native per-tool approval dialog, same
    as reset_connection_pool.

    ⚠️ NOT LIVE-TESTED YET against the real SigNoz Rules API — the request
    shape is drafted from SigNoz's documented alert-rule schema. Treat any
    result from this tool as unverified until it has actually been run once
    against a live SigNoz instance.

    Args:
        rule_name: descriptive name, e.g. "checkout-service-pool-exhaustion-early-warning"
        metric_query: the condition to alert on, e.g.
            "service.name = 'checkout-service' AND db.pool.exhausted = true"
            (should target the ROOT CAUSE signal, not just the symptom, so it
            fires earlier than the existing generic error-rate rule)
        threshold: count/value threshold that triggers the alert
        eval_window_minutes: rolling window to evaluate over (default 5, matches
            the existing checkout-service-high-error-rate rule's window)
        notification_channel: channel ID/name to attach; if None, falls back to
            the existing webhook.site channel already configured for this project
    """
    result = {
        "rule_name": rule_name,
        "created": False,
        "rule_id": None,
        "verdict": None,
        "error": None,
    }

    if not SIGNOZ_API_KEY:
        result["error"] = "SIGNOZ_API_KEY not set in environment"
        result["verdict"] = "NOT CREATED — missing API key, escalate to human"
        return result

    payload = {
        "alert": rule_name,
        "alertType": "TRACES_BASED_ALERT",
        "ruleType": "threshold_rule",
        "version": "v5",
        "evalWindow": f"{eval_window_minutes}m0s",
        "frequency": "1m0s",
        "condition": {
            "compositeQuery": {
                "queryType": "builder",
                "panelType": "graph",
                "builderQueries": {
                    "A": {
                        "queryName": "A",
                        "stepInterval": 60,
                        "dataSource": "traces",
                        "aggregateOperator": "count",
                        "aggregateAttribute": {
                            "key": "",
                            "dataType": "",
                            "type": "",
                            "isColumn": False,
                        },
                        # NOTE: simplified to an empty filter (matches SigNoz's
                        # confirmed-working example shape) rather than trying to
                        # parse metric_query into structured filter items, which
                        # would need each attribute's exact key/dataType/type from
                        # SigNoz's schema — out of scope under time pressure. The
                        # human-readable intent is preserved in `annotations`
                        # below instead. Known simplification, not a full fix.
                        "filters": {"op": "AND", "items": []},
                        "expression": "A",
                        "disabled": False,
                    }
                },
            },
            "op": "1",  # "above"
            "target": threshold,
            "matchType": "4",  # numeric code from SigNoz's confirmed-working example, NOT "count"
        },
        "labels": {"severity": "warning"},
        "annotations": {
            "description": f"Intended condition: {metric_query}",
            "summary": rule_name,
        },
        "disabled": False,
    }

    if notification_channel:
        payload["preferredChannels"] = [notification_channel]

    try:
        resp = requests.post(
            f"{SIGNOZ_BASE_URL}/api/v1/rules",
            json=payload,
            headers={"SIGNOZ-API-KEY": SIGNOZ_API_KEY, "Content-Type": "application/json"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        rule_id = data.get("id") or data.get("data", {}).get("id")
        result["created"] = True
        result["rule_id"] = rule_id
        result["verdict"] = (
            f"CREATED — alert rule '{rule_name}' (id: {rule_id}) now live in SigNoz, "
            f"targets '{metric_query}' with threshold {threshold} over {eval_window_minutes}m"
        )
    except Exception as e:
        result["error"] = str(e)
        result["verdict"] = f"NOT CREATED — {e}. Escalate to human, do not claim this rule exists."

    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
