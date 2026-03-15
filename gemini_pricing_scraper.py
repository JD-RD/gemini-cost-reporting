import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from pathlib import Path

URL = "https://ai.google.dev/gemini-api/docs/pricing"

CACHE_DIR = Path("pricing-cache")
CACHE_DIR.mkdir(exist_ok=True)

def extract_price(text):
    """
    Extract $value from string
    """
    if not text:
        return None

    match = re.search(r"\$([0-9.]+)", text)
    return float(match.group(1)) if match else None


def extract_audio_price(text):
    """
    Extract audio price if present
    """
    if not text:
        return None

    match = re.search(r"\$([0-9.]+).*audio", text)
    return float(match.group(1)) if match else None


def parse_pricing_table(table):

    pricing = {
        "input_text": None,
        "input_audio": None,
        "output": None,
        "cache": None
    }

    raw_rows = []

    for row in table.find_all("tr"):

        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]

        if not cells:
            continue

        raw_rows.append(cells)

        key = cells[0].lower()
        paid = cells[-1]

        if "input price" in key:
            pricing["input_text"] = extract_price(paid)
            pricing["input_audio"] = extract_audio_price(paid)

        elif "output price" in key:
            pricing["output"] = extract_price(paid)

        elif "context caching" in key:
            pricing["cache"] = extract_price(paid)

    return pricing, raw_rows


def detect_thinking_model(section_text):
    """
    Detect models supporting thinking tokens
    """
    return "thinking" in section_text.lower()


def build_openclaw_config(model_id, pricing, thinking):

    config = {
        "provider": "google",
        "model": model_id,
        "pricing": {
            "input_cost_per_million": pricing["input_text"],
            "output_cost_per_million": pricing["output"]
        }
    }

    if pricing["cache"]:
        config["pricing"]["cache_cost_per_million"] = pricing["cache"]

    if pricing["input_audio"]:
        config["pricing"]["audio_input_cost_per_million"] = pricing["input_audio"]

    if thinking:
        config["features"] = {"thinking_tokens": True}

    return config


def scrape():

    html = requests.get(URL).text
    soup = BeautifulSoup(html, "lxml")

    models = {}

    for header in soup.find_all(["h2", "h3"]):

        header_text = header.get_text(" ", strip=True)

        code = header.find_next("code")

        if not code:
            continue

        model_id = code.get_text(strip=True)

        if not model_id.startswith("gemini"):
            continue

        table = header.find_next("table")

        if not table:
            continue

        pricing, raw_rows = parse_pricing_table(table)

        thinking = detect_thinking_model(header_text)

        models[model_id] = {
            "display_name": header_text,
            "thinking_model": thinking,
            "pricing": pricing,
            "openclaw": build_openclaw_config(model_id, pricing, thinking),
            "raw_table": raw_rows
        }

    return models


def save_output(models):

    from datetime import UTC
    now = datetime.now(UTC)

    output = {
        "provider": "google",
        "source": URL,
        "currency": "USD",
        "unit": "per_1M_tokens",
        "updated": now.isoformat(),
        "models": models
    }

    filename = CACHE_DIR / f"gemini-pricing-{now.date()}.json"

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    with open("openclaw_pricing.json", "w") as f:
        json.dump({m: models[m]["openclaw"] for m in models}, f, indent=2)

    print(f"Saved {len(models)} models")
    print(f"Cache file: {filename}")
    print("OpenClaw config: openclaw_pricing.json")


def main():

    models = scrape()

    if not models:
        print("No models detected. Page structure may have changed.")
        return

    save_output(models)


if __name__ == "__main__":
    main()
