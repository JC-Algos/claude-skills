#!/usr/bin/env python3
"""
Update the static currency pair in the Group Forex Analyst workflow.
Usage: python3 update_forex_pair.py XAUUSD
"""
import json
import subprocess
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 update_forex_pair.py <PAIR>")
        print("Example: python3 update_forex_pair.py XAUUSD")
        sys.exit(1)
    
    new_pair = sys.argv[1].upper()
    
    API_KEY = subprocess.check_output(
        "jq -r '.mcpServers.n8n.env.N8N_API_KEY' /root/clawd/config/mcporter.json",
        shell=True, text=True
    ).strip()
    
    workflow_id = "pPbKW9He8etUBO9M"
    
    # Get current workflow
    import urllib.request
    req = urllib.request.Request(
        f"http://localhost:5678/api/v1/workflows/{workflow_id}",
        headers={"X-N8N-API-KEY": API_KEY}
    )
    with urllib.request.urlopen(req) as resp:
        workflow = json.load(resp)
    
    # Find and update "Set Currency Pair" node
    old_pair = None
    for node in workflow["nodes"]:
        if node["name"] == "Set Currency Pair":
            old_pair = node["parameters"]["assignments"]["assignments"][0]["value"]
            node["parameters"]["assignments"]["assignments"][0]["value"] = new_pair
            break
    
    if old_pair is None:
        print("❌ Could not find 'Set Currency Pair' node")
        sys.exit(1)
    
    # Prepare update payload
    update_payload = {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": workflow.get("settings", {"executionOrder": "v1"})
    }
    
    # Update workflow using PUT
    result = subprocess.run([
        "curl", "-s", "-X", "PUT",
        f"http://localhost:5678/api/v1/workflows/{workflow_id}",
        "-H", f"X-N8N-API-KEY: {API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(update_payload)
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and "message" not in result.stdout:
        print(f"✅ Group Forex Analyst updated")
        print(f"   {old_pair} → {new_pair}")
    else:
        print(f"❌ Error: {result.stdout}")
        sys.exit(1)

if __name__ == "__main__":
    main()
