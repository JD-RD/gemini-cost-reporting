import json
import sys
import requests
from pathlib import Path
from datetime import datetime, timedelta
import argparse

PRICING_FILE = "openclaw_pricing.json"
FX_FILE = "fx_rates.json"


def get_usd_cad():
    fx_path = Path(FX_FILE)
    if fx_path.exists():
        data = json.load(open(FX_FILE))
        last = datetime.fromisoformat(data["updated"])
        if datetime.now() - last < timedelta(hours=24):
            return data["USD_CAD"]
    r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=CAD")
    rate = r.json()["rates"]["CAD"]
    json.dump(
        {"USD_CAD": rate, "updated": datetime.now().isoformat()},
        open(FX_FILE, "w"),
        indent=2
    )
    return rate


def load_pricing():
    pricing_path = Path(PRICING_FILE)
    if not pricing_path.exists():
        print(f"Pricing file not found: {PRICING_FILE}")
        sys.exit(1)
    return json.load(pricing_path.open())


def calculate_cost(model, input_tokens, output_tokens, pricing):
    if model not in pricing:
        print(f"Unknown model: {model}")
        sys.exit(1)
    p = pricing[model]["pricing"]
    input_price = p.get("input_cost_per_million", 0)
    output_price = p.get("output_cost_per_million", 0)
    input_cost = input_tokens / 1_000_000 * input_price
    output_cost = output_tokens / 1_000_000 * output_price
    return input_cost + output_cost


def list_models(pricing):
    print("Available Gemini models:")
    for m in pricing.keys():
        print(f"- {m}")
    sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description="Gemini Token Cost CLI")
    parser.add_argument("model", nargs="?", help="Gemini model ID")
    parser.add_argument("input_tokens", type=int, nargs="?", help="Number of input tokens")
    parser.add_argument("output_tokens", type=int, nargs="?", help="Number of output tokens")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--cad-only", action="store_true", help="Show only CAD cost")
    return parser.parse_args()


def main():
    args = parse_args()
    pricing = load_pricing()

    if args.list:
        list_models(pricing)

    if not args.model or args.input_tokens is None or args.output_tokens is None:
        print("Usage: python cost_cli.py <model> <input_tokens> <output_tokens> [--cad-only]")
        sys.exit(1)

    usd_cost = calculate_cost(args.model, args.input_tokens, args.output_tokens, pricing)
    rate = get_usd_cad()
    cad_cost = usd_cost * rate

    print("\n--- Gemini Token Cost Estimation ---")
    print(f"Model: {args.model}")
    print(f"Input tokens: {args.input_tokens}")
    print(f"Output tokens: {args.output_tokens}\n")

    if args.cad_only:
        print(f"CAD cost: ${cad_cost:.4f}\n")
    else:
        print(f"USD cost: ${usd_cost:.4f}")
        print(f"CAD cost: ${cad_cost:.4f}\n")


if __name__ == "__main__":
    main()
