# gemini-cost-reporting

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Track and report Gemini API token usage costs in USD and CAD. Designed to run as a lightweight cron job with zero LLM overhead — no agent tokens consumed for the reporting itself.

## Features

- **Daily cost reports** — formatted summary with input/output token counts, per-token costs, and total in both USD and CAD
- **Live exchange rates** — fetches USD → CAD rate from free APIs with automatic fallback
- **Standalone CLI** — estimate cost for any model + token count combination without the full report
- **Pricing scraper** — keeps pricing data up-to-date by scraping Gemini pricing pages
- **Multiple pricing files** — supports per-million-token rate definitions in JSON
- **Telegram delivery** — sends reports via OpenClaw CLI to your messaging channel

## Project Structure

```
├── daily_cost_report.sh       # Shell entry point (cron-friendly)
├── daily_cost_report.py       # Main report generator
├── cost_cli.py                # Standalone cost estimation CLI
├── gemini_pricing_scraper.py  # Scrape Gemini pricing → JSON
├── openclaw_pricing.json      # Pricing data (per-million-token rates)
├── gemini_openclaw_pricing.json
└── token_usage.json           # Runtime-generated token data (gitignored)
```

## Installation

```bash
# Clone the repo
git clone https://github.com/JD-RD/gemini-cost-reporting.git
cd gemini-cost-reporting

# Python dependencies (minimal — stdlib + requests)
pip install requests
```

No virtualenv required for the daily report script (uses stdlib only). The CLI tool uses `requests`.

## Configuration

| Environment Variable | Description | Default |
|---|---|---|
| `OPENCLAW_SESSION_KEY` | Session key for filtering token data (e.g. `telegram:12345`) | _(none)_ |
| `NOTIFY_SCRIPT` | Path to notification script | `~/src/calendar-agent/notify.sh` |

The script expects `token_usage.json` in the same directory. This file is generated at runtime and is gitignored.

## Usage

### Daily Cost Report

```bash
# Run the full report (reads token_usage.json, fetches exchange rate, sends notification)
./daily_cost_report.sh

# Run just the Python script (prints to stdout)
python3 daily_cost_report.py
```

### Cost CLI

Estimate cost for any Gemini model:

```bash
# Calculate cost for specific token counts
python3 cost_cli.py gemini-2.5-pro 50000 10000

# List available models
python3 cost_cli.py --list

# Show CAD cost only
python3 cost_cli.py gemini-2.5-flash 100000 20000 --cad-only
```

### Pricing Scraper

Update pricing data from the web:

```bash
python3 gemini_pricing_scraper.py
```

## Cron Setup

This is designed to run as an OpenClaw cron job. Example configuration:

```bash
# Daily at 9:00 AM
openclaw cron add \
  --name "daily-cost-report" \
  --schedule "0 9 * * *" \
  --command "/path/to/gemini-cost-reporting/daily_cost_report.sh"
```

The shell script handles the full flow: run the Python report → send via the configured notify script.

## License

MIT
