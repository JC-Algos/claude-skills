#!/usr/bin/env python3
"""
HK News Scanner - Triggers n8n workflow to fetch news
The cron will then prompt Claude to summarize the results
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

def trigger_n8n_workflow():
    """Trigger n8n HK Market News workflow"""
    print("📡 Triggering n8n workflow: HK Market News...")
    try:
        result = subprocess.run(
            ['mcporter', 'call', 'n8n.run_webhook', 
             'workflowName:HK Market News - With Yahoo Finance',
             'data:{"trigger":"cron"}'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ n8n workflow triggered successfully")
            print(result.stdout)
            return True
        else:
            print(f"⚠️ Workflow trigger returned non-zero: {result.stderr}")
            # Still return True if it's just a webhook response issue
            return True
    except subprocess.TimeoutExpired:
        print("⚠️ Workflow trigger timeout (60s) - but may still be running")
        return True
    except Exception as e:
        print(f"❌ Error triggering workflow: {e}")
        return False

def find_latest_headlines():
    """Find the most recent headlines file"""
    hk_daily_dir = Path("/root/clawd/research/hk-daily")
    
    # Wait up to 120 seconds for a new headlines file
    start_time = time.time()
    for attempt in range(60):
        # Find files modified in the last 10 minutes
        headlines_files = list(hk_daily_dir.glob("headlines-*.txt"))
        if headlines_files:
            # Sort by modification time
            latest = max(headlines_files, key=lambda p: p.stat().st_mtime)
            # Check if it's recent (within last 10 minutes)
            age = time.time() - latest.stat().st_mtime
            if age < 600:  # 10 minutes
                print(f"✅ Found recent headlines: {latest.name} (age: {int(age)}s)")
                return latest
        
        # Stop if we've waited more than 2 minutes
        if time.time() - start_time > 120:
            break
            
        time.sleep(2)
    
    # If no recent headlines, use the most recent available
    headlines_files = list(hk_daily_dir.glob("headlines-*.txt"))
    if headlines_files:
        latest = max(headlines_files, key=lambda p: p.stat().st_mtime)
        age = time.time() - latest.stat().st_mtime
        print(f"⚠️ Using older headlines: {latest.name} (age: {int(age/60)}min)")
        return latest
    
    print("❌ No headlines files found at all")
    return None

def main():
    print("🔄 Starting HK news scan...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S HKT')}")
    
    # Step 1: Trigger n8n workflow
    if not trigger_n8n_workflow():
        print("❌ Failed to trigger n8n workflow")
        sys.exit(1)
    
    # Step 2: Wait for headlines file
    print("⏳ Waiting for headlines file (up to 60 seconds)...")
    headlines_file = find_latest_headlines()
    
    if not headlines_file:
        print("❌ No headlines file generated within timeout")
        sys.exit(1)
    
    # Step 3: Signal that headlines are ready
    print(f"📁 Headlines ready: {headlines_file}")
    print("✅ News scan complete - ready for summarization")
    
    # Return success - cron will trigger Claude to summarize
    return 0

if __name__ == "__main__":
    sys.exit(main())
