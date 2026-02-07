#!/usr/bin/env python3
"""
BB Squeeze Command Handler for Telegram /bb command
Usage: /bb [HK/US] [1h/1d]
Examples:
  /bb HK 1h    - HK hourly scan
  /bb HK 1d    - HK daily scan
  /bb US 1h    - US hourly scan
  /bb US 1d    - US daily scan
  /bb HK       - HK daily scan (default)
  /bb US       - US hourly scan (default)
"""

import sys
import subprocess

def main():
    # Parse command arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Default values
    market = "HK"
    interval = "1d"
    
    # Parse arguments
    if len(args) >= 1:
        market = args[0].upper()
    if len(args) >= 2:
        interval = args[1].lower()
    
    # Validate market
    if market not in ["HK", "US"]:
        print(f"❌ Invalid market: {market}. Use HK or US.")
        return 1
    
    # Validate interval
    if interval not in ["1h", "1d"]:
        print(f"❌ Invalid interval: {interval}. Use 1h or 1d.")
        return 1
    
    # Route to appropriate scanner
    if market == "HK":
        if interval == "1h":
            script = "/root/clawd/hsi_hourly_scan.py"
        else:  # 1d
            script = "/root/clawd/hsi_daily_scan.py"
    else:  # US
        script = "/root/clawd/us_bb_squeeze_scanner.py"
        # US scanner needs interval as first arg
        result = subprocess.run(["python3", script, interval, "telegram"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    
    # Run HK scanner (no args needed)
    result = subprocess.run(["python3", script], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
