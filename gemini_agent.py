"""
Sentinel Agent — GEMINI VERSION (free tier, no credit card required)

This is a functionally equivalent alternative to agent.py, built for Google's
Gemini API instead of Anthropic's Claude API. Use this if real Claude API
access is still blocked by payment method issues.

Key difference from agent.py: Gemini's SDK doesn't have Anthropic's built-in
"remote MCP server" feature, so this script connects to SigNoz's MCP server
directly using the standalone `mcp` Python client library, then passes that
live MCP session as a tool alongside our two local tools (get_deploy_history,
reset_connection_pool). google-genai's automatic function calling handles
the rest, including actually calling SigNoz's tools when Gemini asks for them.

Setup (all free, no card):
  1. Go to https://aistudio.google.com/apikey
  2. Sign in with a Google account, click "Create API key" — no card needed
  3. export GEMINI_API_KEY=...
  4. export SIGNOZ_API_KEY=<your existing SigNoz service account key>
  5. python gemini_agent.py

NOTE: this script has NOT yet been tested against a live Gemini + SigNoz MCP
connection (built without live API access to verify). If you hit an error,
paste it back — likely a small fix (e.g. MCP header format, model name).
"""

import os
import json
import asyncio
import requests
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SIGNOZ_API_KEY = os.environ.get("SIGNOZ_API_KEY")
SIGNOZ_MCP_URL = "http://localhost:8000/mcp"
CHECKOUT_APP_URL = "http://localhost:5000"
MODEL = os.environ.get("SENTINEL_GEMINI_MODEL", "gemini-flash-latest")

if not GEMINI_API_KEY:
    raise SystemExit(
        "Missing GEMINI_API_KEY env var. Get a free one (no card) at "
        "https://aistudio.google.com/apikey"
    )
if not SIGNOZ_API_KEY:
    raise SystemExit("Missing SIGNOZ_API_KEY env var.")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are Sentinel, an autonomous incident response agent for a small
e-commerce checkout service. You have READ access to SigNoz observability data
(traces, logs, metrics) through connected tools, a read-only deploy history
tool, and ONE write-capable tool that resizes the service's database
connection pool.

Your job, in strict order:
1. INVESTIGATE: Use the SigNoz tools to look at recent traces and logs for the
   `checkout-service`. Look specifically for spans named `db.pool.acquire` with
   `db.pool.exhausted=true`, and log lines mentioning "connection pool exhausted".
   Quantify the blast radius: what % of requests are failing, over what time window.
2. CORRELATE WITH DEPLOYS: Call get_deploy_history to check recent deploys. Look
   for a deploy whose timestamp lines up with when the incident started, and whose
   commit message or changed files plausibly relate to the symptom.
3. FORM A HYPOTHESIS: State your root cause hypothesis in plain English, backed by
   the specific evidence you found (cite span/log counts and the specific deploy).
4. PROPOSE A FIX: Your only available remediation is calling reset_connection_pool
   with a new pool size. Recommend a specific number and explain your reasoning.
5. WAIT FOR APPROVAL: Do NOT call reset_connection_pool yet. End your turn after
   proposing the fix and ask the human to approve or reject it.
6. VERIFY: After the fix is applied (in a later turn), use the SigNoz tools again
   to confirm the error rate has actually dropped.
7. SUMMARIZE: Write a short postmortem: what broke, why, what evidence proved it,
   what fix was applied, and one suggestion to prevent recurrence.

Be concise and concrete. Always cite real numbers from the tools, never guess.
"""


def get_deploy_history() -> str:
    """Fetch the recent deployment history for checkout-service, including
    timestamps, authors, commit messages, and changed files. Use this to
    correlate the incident's start time with a specific deploy."""
    try:
        with open(
            os.path.join(os.path.dirname(__file__), "deploy_history.json")
        ) as f:
            return f.read()
    except FileNotFoundError:
        return json.dumps({"error": "deploy_history.json not found"})


def reset_connection_pool(size: int) -> str:
    """Resize the checkout-service's database connection pool. This is the
    ONLY remediation action available. Only call this AFTER the human has
    explicitly approved the proposed fix.

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


async def run_investigation(mcp_session: ClientSession):
    """Turn 1: investigate + propose a fix, then stop and wait for approval."""
    chat = client.aio.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[mcp_session, get_deploy_history, reset_connection_pool],
        ),
    )
    response = await chat.send_message(
        "An alert just fired: checkout-service-high-error-rate. "
        "Investigate using the SigNoz tools and report back."
    )
    print(f"\n[Sentinel]: {response.text}")
    return chat


async def run_fix_and_verify(chat):
    """Turn 2: apply the fix (after human approval) and verify recovery."""
    response = await chat.send_message(
        "Approved. Please apply the fix now, then verify recovery and write the postmortem."
    )
    print(f"\n[Sentinel]: {response.text}")


async def main():
    print("=" * 60)
    print("SENTINEL AGENT (Gemini edition) — starting investigation")
    print(f"Model: {MODEL}")
    print("=" * 60)

    headers = {"SIGNOZ-API-KEY": SIGNOZ_API_KEY}

    async with streamablehttp_client(SIGNOZ_MCP_URL, headers=headers) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()

            chat = await run_investigation(session)

            print("\n" + "=" * 60)
            approval = input("Approve the proposed fix? (yes/no): ").strip().lower()
            print("=" * 60)

            if approval == "yes":
                await run_fix_and_verify(chat)
            else:
                print("\n[Sentinel]: Fix not approved. Standing by.")


if __name__ == "__main__":
    asyncio.run(main())
