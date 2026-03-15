#!/usr/bin/env python3
"""Daily Gemini Cost Report - Standalone script (zero LLM tokens)"""

import json
import sys
import os
import re
from datetime import datetime, UTC

# Config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRICING_FILE = os.path.join(SCRIPT_DIR, "openclaw_pricing.json")
TOKEN_USAGE_FILE = os.path.join(SCRIPT_DIR, "token_usage.json")
USER_SESSION_KEY = os.environ.get("OPENCLAW_SESSION_KEY", "")


def get_usd_to_cad_rate():
    """Fetch USD to CAD exchange rate from free API"""
    import urllib.request

    apis = [
        {
            "url": "https://open.er-api.com/v6/latest/USD",
            "parser": lambda d: d.get("rates", {}).get("CAD"),
        },
        {
            "url": "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
            "parser": lambda d: d.get("usd", {}).get("cad"),
        },
    ]

    for api in apis:
        try:
            req = urllib.request.Request(api["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                rate = api["parser"](data)
                if rate and isinstance(rate, (int, float)) and rate > 0:
                    return float(rate)
        except Exception as e:
            print(f"API {api['url']} failed: {e}", file=sys.stderr)
            continue

    print("All exchange rate APIs failed, defaulting to 1.37", file=sys.stderr)
    return 1.37  # Fallback approximate rate


def get_token_usage():
    """Read token usage from the JSON file updated by Oscar"""
    try:
        with open(TOKEN_USAGE_FILE, "r") as f:
            data = json.load(f)
        return {
            "model": data.get("model", "unknown"),
            "in": data.get("tokens", {}).get("in", 0),
            "out": data.get("tokens", {}).get("out", 0),
            "lastUpdated": data.get("lastUpdated", "unknown"),
        }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Could not read token usage file: {e}", file=sys.stderr)
        return {"model": "unknown", "in": 0, "out": 0, "lastUpdated": "unknown"}


def get_pricing(model_id):
    """Read pricing info from JSON file"""
    try:
        with open(PRICING_FILE, "r") as f:
            data = json.load(f)
        result = data.get(model_id)
        if not result and "/" in model_id:
            result = data.get(model_id.split("/", 1)[1])
        return result
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Pricing file error: {e}", file=sys.stderr)
        return None


def send_telegram_message(message):
    """Send message via OpenClaw CLI"""
    import subprocess

    cmd = [
        "openclaw", "agent",
        "--message", f"Send this to jd: {message}",
        "--deliver",
        "--timeout", "30"
    ]
    try:
        subprocess.run(cmd, timeout=60, capture_output=True)
    except Exception as e:
        print(f"Failed to send via CLI: {e}", file=sys.stderr)


def main():
    # Get token usage
    usage = get_token_usage()
    model_id = usage["model"]
    input_tokens = usage["in"]
    output_tokens = usage["out"]

    # Get pricing
    pricing = get_pricing(model_id)
    if not pricing:
        print(f"No pricing found for model: {model_id}", file=sys.stderr)
        return

    input_cost_per_m = pricing["pricing"].get("input_cost_per_million", 0)
    output_cost_per_m = pricing["pricing"].get("output_cost_per_million", 0)

    # Calculate cost in USD
    input_cost_usd = (input_tokens / 1_000_000) * input_cost_per_m
    output_cost_usd = (output_tokens / 1_000_000) * output_cost_per_m
    total_cost_usd = input_cost_usd + output_cost_usd

    # Get exchange rate and convert to CAD
    rate = get_usd_to_cad_rate()
    total_cost_cad = total_cost_usd * rate

    # Build report
    message = (
        f"🦊 Good morning, jd! Here's your daily cost report:\n\n"
        f"📊 **Model:** {model_id}\n"
        f"📥 **Input Tokens:** {input_tokens:,}\n"
        f"📤 **Output Tokens:** {output_tokens:,}\n"
        f"💰 **Estimated Cost:** ~${total_cost_cad:.2f} CAD (${total_cost_usd:.2f} USD)\n"
        f"💱 **Exchange Rate:** 1 USD = {rate:.4f} CAD\n\n"
        f"_Pricing: Input ${input_cost_per_m:.2f}/M, Output ${output_cost_per_m:.2f}/M_\n"
        f"_Token data last updated: {usage['lastUpdated']}_"
    )

    print(message)

    # Send to user
    send_telegram_message(message)


if __name__ == "__main__":
    main()
