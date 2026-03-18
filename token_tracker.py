#!/usr/bin/env python3
"""Token Tracker - Simple token usage accumulator from session transcripts."""

import json
import os
from datetime import datetime
from pathlib import Path

TOKEN_FILE = "/home/jd/gemini-pricing/token_usage.json"
SESSIONS_DIR = "/home/jd/.openclaw/agents/main/sessions"

def main():
    # Initialize token data
    token_data = {"sessions": [], "total": {"in": 0, "out": 0}}
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
    
    # Scan all session files
    sessions_dir = Path(SESSIONS_DIR)
    if not sessions_dir.exists():
        print(f"No sessions directory found")
        return
    
    for session_file in sessions_dir.glob("*.jsonl"):
        # Get date from file mtime
        mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
        date_str = mtime.strftime("%Y-%m-%d")
        
        # Skip if already processed
        existing = [s for s in token_data.get("sessions", []) 
                   if s.get("file") == str(session_file.name)]
        if existing:
            continue
        
        tokens_in = 0
        tokens_out = 0
        model = "unknown"
        
        with open(session_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # Get model info
                    if entry.get("type") == "model_change":
                        model = f"{entry.get('provider', 'unknown')}/{entry.get('modelId', 'unknown')}"
                    
                    # Extract token usage from message entries
                    if entry.get("type") == "message":
                        msg = entry.get("message", {})
                        usage = msg.get("usage", {})
                        if usage:
                            tokens_in += usage.get("promptTokens", usage.get("input", 0))
                            tokens_out += usage.get("completionTokens", usage.get("output", 0))
                except:
                    pass
        
        if tokens_in > 0 or tokens_out > 0:
            token_data["sessions"].append({
                "file": session_file.name,
                "date": date_str,
                "model": model,
                "in": tokens_in,
                "out": tokens_out
            })
            token_data["total"]["in"] += tokens_in
            token_data["total"]["out"] += tokens_out
            print(f"Added: {session_file.name} - {tokens_in} in / {tokens_out} out ({model})")
    
    token_data["lastUpdated"] = datetime.now().isoformat()
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"\nTotal: {token_data['total']['in']:,} in / {token_data['total']['out']:,} out")

if __name__ == "__main__":
    main()