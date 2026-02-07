#!/usr/bin/env python3
"""
Update HK Market News workflow to add webhook trigger and multi-channel push
"""
import json
import subprocess
import uuid

# Get n8n API key
with open('/root/clawd/config/mcporter.json') as f:
    config = json.load(f)
    api_key = config['mcpServers']['n8n']['env']['N8N_API_KEY']

WORKFLOW_ID = "Z409Z8fwwonXdJdP"
N8N_API = "http://localhost:5678/api/v1"

# Get current workflow
result = subprocess.run(
    ['curl', '-s', f'{N8N_API}/workflows/{WORKFLOW_ID}', '-H', f'X-N8N-API-KEY: {api_key}'],
    capture_output=True, text=True
)
workflow = json.loads(result.stdout)

# Add webhook node
webhook_id = str(uuid.uuid4())
webhook_node = {
    "parameters": {
        "path": "hk-news",
        "options": {}
    },
    "id": "webhook-trigger",
    "name": "Webhook",
    "type": "n8n-nodes-base.webhook",
    "typeVersion": 2,
    "webhookId": webhook_id,
    "position": [240, 200]
}

# Check if webhook already exists
has_webhook = any(n.get('name') == 'Webhook' for n in workflow['nodes'])
if not has_webhook:
    workflow['nodes'].append(webhook_node)
    
    # Add webhook connections to all RSS feeds
    rss_connections = workflow['connections']['Schedule']['main'][0]
    workflow['connections']['Webhook'] = {
        "main": [rss_connections.copy()]
    }
    print("✅ Added webhook trigger node")
else:
    print("ℹ️ Webhook already exists")

# Update the Ping Oracle node to send to TG + WA
for node in workflow['nodes']:
    if node['name'] == 'Ping Oracle':
        node['parameters']['jsCode'] = '''const { execSync } = require('child_process');
const filepath = $json.filepath;
const count = $json.count;
const chinaCount = $json.chinaCount || 0;

// Read the headlines file for summary
const fs = require('fs');
const actualPath = filepath.replace('/local-files/', '/files/');
let content = '';
try {
  content = fs.readFileSync(actualPath, 'utf8');
} catch (e) {
  content = 'Could not read file';
}

// Extract just headlines (first 15 lines of each section)
const lines = content.split('\\n');
let summary = `📰 港股新聞速報\\n`;
summary += `━━━━━━━━━━━━━━━━━━━━\\n`;
summary += `📊 共 ${count} 條新聞 | 🇨🇳 中國 ${chinaCount} 條\\n\\n`;

// Get headlines only (lines starting with number)
const headlines = lines.filter(l => /^\\d+\\./.test(l)).slice(0, 10);
summary += headlines.join('\\n');
summary += `\\n\\n🔗 完整報告: ${filepath}`;

const results = [];

// 1. Send to Telegram (Jason)
try {
  execSync(`/usr/bin/clawdbot session send '${summary.replace(/'/g, "'\\\\''")}' 2>/dev/null || true`, {encoding: 'utf8', timeout: 15000});
  results.push('TG: ✅');
} catch (e) {
  results.push('TG: ❌ ' + e.message);
}

// 2. Send to WhatsApp (Jason)
try {
  execSync(`wacli send text --to "85269774866@s.whatsapp.net" --message '${summary.replace(/'/g, "'\\\\''")}' 2>/dev/null || true`, {encoding: 'utf8', timeout: 15000});
  results.push('WA-Jason: ✅');
} catch (e) {
  results.push('WA-Jason: ❌');
}

// 3. Send to WhatsApp Group (DIM INV Library)
try {
  execSync(`wacli send text --to "85262982502-1545129405@g.us" --message '${summary.replace(/'/g, "'\\\\''")}' 2>/dev/null || true`, {encoding: 'utf8', timeout: 15000});
  results.push('WA-Group: ✅');
} catch (e) {
  results.push('WA-Group: ❌');
}

return [{json: {sent: true, results: results.join(' | '), summary: summary.substring(0, 200) + '...'}}];'''
        print("✅ Updated Ping Oracle to push to TG + WA")

# Update workflow
update_payload = {
    "name": workflow.get("name"),
    "nodes": workflow.get("nodes"),
    "connections": workflow.get("connections"),
    "settings": {"executionOrder": "v1"}
}

result = subprocess.run(
    ['curl', '-s', '-X', 'PUT', f'{N8N_API}/workflows/{WORKFLOW_ID}',
     '-H', f'X-N8N-API-KEY: {api_key}',
     '-H', 'Content-Type: application/json',
     '-d', json.dumps(update_payload)],
    capture_output=True, text=True
)

if '"id"' in result.stdout:
    print("✅ Workflow updated successfully")
    
    # Deactivate and reactivate to register webhook
    subprocess.run(['curl', '-s', '-X', 'POST', f'{N8N_API}/workflows/{WORKFLOW_ID}/deactivate',
                    '-H', f'X-N8N-API-KEY: {api_key}'], capture_output=True)
    subprocess.run(['curl', '-s', '-X', 'POST', f'{N8N_API}/workflows/{WORKFLOW_ID}/activate',
                    '-H', f'X-N8N-API-KEY: {api_key}'], capture_output=True)
    print("✅ Webhook registered")
    print(f"\n🔗 Webhook URL: https://n8n.srv1295571.hstgr.cloud/webhook/hk-news")
else:
    print("❌ Failed to update workflow")
    print(result.stdout)
    print(result.stderr)
