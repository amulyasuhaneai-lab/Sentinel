"""
create_alert_rule_tool.py

Drop-in addition to sentinel_mcp_server.py — adds a `create_alert_rule` MCP tool.
NOTE: this logic is already merged into sentinel_mcp_server.py as a real
@mcp.tool() function. This standalone file is kept for reference and for its
independent smoke-test entry point (see bottom of file), not as what's
actually running.

⚠️ NOT LIVE-TESTED YET — the exact SigNoz Rules API request shape below
(`POST /api/v1/rules`) is written from SigNoz's documented alert-rule schema,
but has not been fired against the actual running SigNoz instance. Needs a
real curl/live test before demo day.
"""

import os
import requests

SIGNOZ_BASE_URL = "http://localhost:8080"
SIGNOZ_API_KEY = os.environ.get("SIGNOZ_API_KEY")


def create_alert_rule(
    rule_name: str,
    metric_query: str,
    threshold: float,
    eval_window_minutes: int = 5,
    notification_channel: str = None,
) -> dict:
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
        "condition": {
            "compositeQuery": {
                "queryType": "builder",
                "builderQueries": {
                    "A": {
                        "queryName": "A",
                        "dataSource": "traces",
                        "aggregateOperator": "count",
                        "filters": {
                            "items": [
                                {"key": "query", "value": metric_query, "op": "="}
                            ]
                        },
                    }
                },
            },
            "op": "1",
            "target": threshold,
            "matchType": "count",
        },
        "evalWindow": f"{eval_window_minutes}m0s",
        "frequency": "1m0s",
        "labels": {"severity": "warning"},
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
    print("Running create_alert_rule() standalone against local SigNoz...")
    print("Requires: SigNoz running on localhost:8080, SIGNOZ_API_KEY env var set")
    print()
    output = create_alert_rule(
        rule_name="checkout-service-pool-exhaustion-early-warning",
        metric_query="service.name = 'checkout-service' AND db.pool.exhausted = true",
        threshold=3,
        eval_window_minutes=5,
    )
    import json
    print(json.dumps(output, indent=2))
