"""
Sentinel Agent — the core closed-loop incident response agent.

Flow: Diagnose (via SigNoz MCP tools) -> Explain hypothesis + evidence ->
      Ask for human approval -> Remediate (call the app's own fix endpoint) ->
      Verify recovery (via SigNoz MCP tools again) -> Write postmortem.

Requires two env vars:
  ANTHROPIC_API_KEY  - your Claude API key (https://console.anthropic.com)
  SIGNOZ_API_KEY     - the service account API key you just created in SigNoz

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    export SIGNOZ_API_KEY=<your signoz key>
    python agent.py
"""

import os
import json
import requests
from anthropic import Anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SIGNOZ_API_KEY = os.environ.get("SIGNOZ_API_KEY")
SIGNOZ_MCP_URL = "http://localhost:8000/mcp"
CHECKOUT_APP_URL = "http://localhost:5000"

# Cost control #1: MOCK MODE — set SENTINEL_MOCK=true to run the entire agent
# flow with ZERO real API calls and ZERO cost. Uses fake but realistic
# responses so you can test the approval gate, the fix-calling logic, and
# the overall flow completely for free before spending any real money.
#   export SENTINEL_MOCK=true
MOCK_MODE = os.environ.get("SENTINEL_MOCK", "false").lower() == "true"

# Cost control #2: default to Haiku (cheapest) for real test runs. Only switch
# to Sonnet for your final rehearsals + the actual live demo.
#   export SENTINEL_MODEL=claude-sonnet-5
MODEL = os.environ.get("SENTINEL_MODEL", "claude-haiku-4-5-20251001")

if not MOCK_MODE:
    if not ANTHROPIC_API_KEY:
        raise SystemExit("Missing ANTHROPIC_API_KEY env var. (Or set SENTINEL_MOCK=true to test for free.)")
    if not SIGNOZ_API_KEY:
        raise SystemExit("Missing SIGNOZ_API_KEY env var. (Or set SENTINEL_MOCK=true to test for free.)")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    client = None
    print("\n*** MOCK MODE ACTIVE — no real API calls, zero cost, fake data ***\n")

SYSTEM_PROMPT = """You are Sentinel, an autonomous incident response agent for a small
e-commerce checkout service. You have READ access to SigNoz observability data
(traces, logs, metrics) through connected tools, and ONE write-capable local tool
that resizes the service's database connection pool.

Your job, in strict order:
1. INVESTIGATE: Use the SigNoz tools to look at recent traces and logs for the
   `checkout-service`. Look specifically for spans named `db.pool.acquire` with
   `db.pool.exhausted=true`, and log lines mentioning "connection pool exhausted".
   Quantify the blast radius: what % of requests are failing, over what time window.
2. CORRELATE WITH DEPLOYS: Call `get_deploy_history` to check recent deploys. Look
   for a deploy whose timestamp lines up with when the incident started, and whose
   commit message or changed files plausibly relate to the symptom (e.g. a config
   change touching connection pools, timeouts, or resource limits).
3. FORM A HYPOTHESIS: State your root cause hypothesis in plain English, backed by
   the specific evidence you found (cite span/log counts and the specific deploy,
   not vague impressions).
4. PROPOSE A FIX: Your only available remediation is calling `reset_connection_pool`
   with a new pool size. Recommend a specific number and explain your reasoning
   (e.g. "current size is 3, recommend 20 based on baseline traffic").
5. WAIT FOR APPROVAL: Do NOT call `reset_connection_pool` yet. End your turn after
   proposing the fix and ask the human to approve or reject it. Only call the tool
   in a later turn, after you see an explicit human approval message.
6. VERIFY: After applying the fix, use the SigNoz tools again to confirm the error
   rate has actually dropped. Don't just assume the fix worked.
7. SUMMARIZE: Write a short postmortem: what broke, why, what evidence proved it
   (including the correlated deploy), what fix was applied, and one suggestion to
   prevent recurrence.

Be concise and concrete. Always cite real numbers from the tools, never guess.
"""

# The two local tools this agent has: one read-only (deploy history), one
# write-capable (the actual remediation action).
LOCAL_TOOLS = [
    {
        "name": "get_deploy_history",
        "description": (
            "Fetch the recent deployment history for checkout-service, including "
            "timestamps, authors, commit messages, and changed files. Use this to "
            "correlate the incident's start time with a specific deploy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "reset_connection_pool",
        "description": (
            "Resize the checkout-service's database connection pool. This is the "
            "ONLY remediation action available. Only call this AFTER the human has "
            "explicitly approved your proposed fix in a previous turn."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "size": {
                    "type": "integer",
                    "description": "The new pool size to set (recommended: 20 for normal operation)",
                }
            },
            "required": ["size"],
        },
    },
]


def mock_investigation_turn() -> str:
    """Fake but realistic first-turn response — mimics what Claude would say
    after actually querying SigNoz's MCP tools and the deploy history tool."""
    print("\n[Sentinel -> LOCAL tool]: get_deploy_history({})")
    deploy_data = execute_local_tool("get_deploy_history", {})
    print(f"[LOCAL tool result]: (returned {len(json.loads(deploy_data))} deploy records)")

    text = (
        "I checked recent traces and logs for checkout-service.\n\n"
        "FINDINGS:\n"
        "- 187 of 632 requests failed in the last load window (29.6% error rate)\n"
        "- All failures show a `db.pool.acquire` span with db.pool.exhausted=true\n"
        "- Logs confirm: 'connection pool exhausted' repeated ~180 times\n"
        "- Current pool size: 3 (down from the healthy baseline of 20)\n\n"
        "DEPLOY CORRELATION:\n"
        "- Deploy #47 (devops-bot, 2026-07-23 15:05 UTC): 'reduce DB connection pool "
        "size from 20 to 3 as part of cost-optimization pass (JIRA-1182)'\n"
        "- This deploy's timestamp lines up almost exactly with when errors started.\n\n"
        "HYPOTHESIS: Deploy #47 intentionally reduced the connection pool from 20 to "
        "3 as a cost-cutting change, but 3 is far too low for current checkout "
        "traffic, causing requests to time out waiting for a free connection.\n\n"
        "PROPOSED FIX: Call reset_connection_pool with size=20 to restore the "
        "known-good baseline from before deploy #47.\n\n"
        "Awaiting your approval to proceed."
    )
    print(f"\n[Sentinel - MOCK]: {text}")
    return text


def mock_fix_and_verify_turn():
    """Fake but realistic second-turn response after approval — actually
    calls the REAL local tool (so you can verify the fix genuinely works),
    just skips the real Claude API call for the reasoning part."""
    print("\n[Sentinel -> LOCAL tool]: reset_connection_pool({'size': 20})")
    result = execute_local_tool("reset_connection_pool", {"size": 20})
    print(f"[LOCAL tool result]: {result}")
    print(
        "\n[Sentinel - MOCK]: Fix applied. Pool resized to 20. "
        "(In real mode, I'd now re-query SigNoz to confirm the error rate "
        "actually dropped, then write a postmortem.)\n\n"
        "POSTMORTEM (mock):\n"
        "- What broke: DB connection pool was undersized (3) for current traffic\n"
        "- Root cause: Deploy #47 reduced pool size 20 -> 3 as a cost-cutting change\n"
        "- Evidence: 29.6% failure rate, db.pool.exhausted=true on failed spans, "
        "timestamp match with deploy #47\n"
        "- Fix applied: resized pool to 20\n"
        "- Prevention: add a minimum-pool-size guardrail to future cost-optimization "
        "deploys, and add an alert on pool size itself, not just error rate"
    )



def execute_local_tool(tool_name: str, tool_input: dict) -> str:
    """Execute one of our two local tools."""
    if tool_name == "get_deploy_history":
        try:
            with open(
                os.path.join(os.path.dirname(__file__), "deploy_history.json")
            ) as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps({"error": "deploy_history.json not found"})

    if tool_name == "reset_connection_pool":
        size = tool_input.get("size", 20)
        try:
            resp = requests.post(
                f"{CHECKOUT_APP_URL}/admin/reset-pool",
                json={"size": size},
                timeout=5,
            )
            return json.dumps(resp.json())
        except requests.exceptions.RequestException as e:
            return json.dumps({
                "error": f"Could not reach checkout app at {CHECKOUT_APP_URL} — "
                          f"is app.py running? ({e})"
            })
    return json.dumps({"error": f"unknown tool {tool_name}"})


def run_agent_turn(messages: list) -> list:
    """Send one request to Claude with both the SigNoz MCP server and our
    local tool available. Handles local tool_use blocks (MCP tool_use blocks
    are executed server-side by Anthropic automatically)."""

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=LOCAL_TOOLS,
        mcp_servers=[
            {
                "type": "url",
                "url": SIGNOZ_MCP_URL,
                "name": "signoz",
                "authorization_token": SIGNOZ_API_KEY,
            }
        ],
        extra_headers={"anthropic-beta": "mcp-client-2025-04-04"},
    )

    messages.append({"role": "assistant", "content": response.content})

    # Print everything the model said/did this turn
    for block in response.content:
        if block.type == "text":
            print(f"\n[Sentinel]: {block.text}")
        elif block.type == "mcp_tool_use":
            print(f"\n[Sentinel -> SigNoz tool]: {block.name}({block.input})")
        elif block.type == "mcp_tool_result":
            print(f"[SigNoz -> Sentinel]: (data returned)")
        elif block.type == "tool_use":
            print(f"\n[Sentinel -> LOCAL tool]: {block.name}({block.input})")

    # If Claude wants to call our LOCAL tool (not an MCP tool), we execute it
    # and feed the result back.
    local_tool_calls = [b for b in response.content if b.type == "tool_use"]
    if local_tool_calls:
        tool_results = []
        for call in local_tool_calls:
            result = execute_local_tool(call.name, call.input)
            print(f"[LOCAL tool result]: {result}")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": result,
                }
            )
        messages.append({"role": "user", "content": tool_results})
        # Recurse so Claude can react to the tool result
        return run_agent_turn(messages)

    return messages


def main():
    print("=" * 60)
    print("SENTINEL AGENT — starting investigation")
    print(f"Model: {'MOCK (no cost)' if MOCK_MODE else MODEL}")
    print("=" * 60)

    if MOCK_MODE:
        mock_investigation_turn()
        print("\n" + "=" * 60)
        approval = input("Approve the proposed fix? (yes/no): ").strip().lower()
        print("=" * 60)
        if approval == "yes":
            mock_fix_and_verify_turn()
        else:
            print("\n[Sentinel]: Fix not approved. Standing by.")
        return

    messages = [
        {
            "role": "user",
            "content": (
                "An alert just fired: checkout-service-high-error-rate. "
                "Investigate using the SigNoz tools and report back."
            ),
        }
    ]

    messages = run_agent_turn(messages)

    # Human approval gate — simple CLI input for now
    print("\n" + "=" * 60)
    approval = input("Approve the proposed fix? (yes/no): ").strip().lower()
    print("=" * 60)

    if approval == "yes":
        messages.append(
            {
                "role": "user",
                "content": "Approved. Please apply the fix now, then verify recovery and write the postmortem.",
            }
        )
        run_agent_turn(messages)
    else:
        print("\n[Sentinel]: Fix not approved. Standing by.")


if __name__ == "__main__":
    main()
