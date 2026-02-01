---
name: jc-n8n
description: Use when building, debugging, or managing n8n workflows on this VPS. Covers Docker networking, API gotchas, webhook setup, connecting to host services, and workflow management via mcporter.
---

# JC n8n Workflow Management

## Overview

n8n runs **inside Docker** while backend services run on the **host**. This architecture requires specific networking patterns. This skill covers deployment best practices, common pitfalls, and fixes.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Docker Network: n8n_default                            │
│  Gateway: 172.18.0.1                                    │
│  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  n8n-n8n-1      │  │  n8n-n8n-worker-1           │  │
│  │  (main)         │  │  (worker)                   │  │
│  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ 172.18.0.1
┌─────────────────────────────────────────────────────────┐
│  HOST                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │Flask:5002│ │Flask:5003│ │RSS:1200  │ │RSS:1201   │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Critical: Docker → Host Networking

**Inside n8n (Docker), `localhost` = the container, NOT the host!**

| ❌ DON'T USE | ✅ USE |
|-------------|--------|
| `localhost:PORT` | `172.18.0.1:PORT` |
| `127.0.0.1:PORT` | `172.18.0.1:PORT` |
| `host.docker.internal:PORT` | `172.18.0.1:PORT` |

**Example:** Flask API on host at port 5002
- n8n workflow URL: `http://172.18.0.1:5002/endpoint`

## Access Points

| Service | Local | External |
|---------|-------|----------|
| n8n Web UI | `http://localhost:5678` | `https://n8n.srv1295571.hstgr.cloud` |
| n8n API | `http://localhost:5678/api/v1` | Same external + `/api/v1` |
| Webhooks | N/A | `https://n8n.srv1295571.hstgr.cloud/webhook/{path}` |

**API requires:** `X-N8N-API-KEY` header

## MCP Tools (via mcporter)

Configured in `/root/clawd/config/mcporter.json`. 11 tools available:

```bash
# List all workflows
mcporter call n8n.list_workflows

# List active only
mcporter call n8n.list_workflows active:true

# Get workflow details
mcporter call n8n.get_workflow workflowId:"xxx"

# List executions
mcporter call n8n.list_executions limit:5

# Run webhook
mcporter call n8n.run_webhook workflowName:"workflow-name" data:'{"key":"value"}'
```

**Available tools:** list_workflows, get_workflow, create_workflow, update_workflow, delete_workflow, activate_workflow, deactivate_workflow, list_executions, get_execution, delete_execution, run_webhook

## Webhook Setup Gotchas

### 1. webhookId Must Be Generated

When copying workflows, n8n won't auto-generate `webhookId`. Generate manually:

```python
import uuid
new_webhook_id = str(uuid.uuid4())
```

### 2. Webhook Path Conflicts

Each webhook needs a unique path. Copying a workflow? Change the path!

### 3. Activation Dance

After changing webhook path:
1. **Deactivate** workflow
2. **Update** workflow via API
3. **Reactivate** workflow

Without this sequence, webhook returns 404.

### 4. Webhook Returns 404

Check:
- Is `webhookId` null? → Generate one
- Is workflow active? → Activate it
- Did you reactivate after path change? → Do the dance

## Workflow API Update Payload

**Minimal payload that works:**

```python
update_payload = {
    "name": workflow.get("name"),
    "nodes": workflow.get("nodes"),
    "connections": workflow.get("connections"),
    "settings": {"executionOrder": "v1"}
}
```

**Don't include:** `id`, `createdAt`, `updatedAt`, `versionId`, or other read-only fields.

## Workflow Connections

- All trigger paths must connect through shared config nodes
- `$json.pair` (or any variable) only exists if previous node provides it
- Check node connections in n8n UI or via API

## Docker Commands

```bash
# Check n8n containers
docker ps | grep n8n

# View n8n logs
docker logs n8n-n8n-1 --tail 100

# Restart n8n
cd /docker/n8n && docker compose restart n8n

# Full recreate (if config changed)
cd /docker/n8n && docker compose up -d --force-recreate
```

## Adding Backend Services

When creating a new Flask/FastAPI service that n8n needs to call:

1. **Run on host** (not in Docker)
2. **Bind to 0.0.0.0** or specific interface
3. **In n8n, use** `http://172.18.0.1:PORT`

Example systemd service:
```ini
[Service]
ExecStart=/usr/bin/python3 /path/to/app.py
Restart=always
```

## RSS Feeds Integration

Two RSS options available:

| Service | Port | Purpose |
|---------|------|---------|
| RSSHub (Docker) | 1200 | Self-hosted RSS generator (1000+ routes) |
| Custom RSS (Host) | 1201 | Custom scrapers (HKEJ, AAStocks) |

**In n8n workflows:**
- RSSHub: `http://172.18.0.1:1200/twitter/user/xxx`
- Custom: `http://172.18.0.1:1201/hkej/stock`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `localhost` in n8n HTTP nodes | Use `172.18.0.1` |
| Forgetting to reactivate after webhook change | Deactivate → Update → Reactivate |
| Copying workflow without new webhookId | Generate UUID for webhookId |
| Including read-only fields in API update | Use minimal payload |
| Backend service not binding to accessible interface | Bind to `0.0.0.0` |

## Debugging Workflows

```bash
# Check if workflow is active
mcporter call n8n.get_workflow workflowId:"xxx" | jq '.active'

# Check recent executions
mcporter call n8n.list_executions limit:5 | jq '.data[] | {id, finished, status}'

# Test webhook manually
curl -X POST "https://n8n.srv1295571.hstgr.cloud/webhook/your-path" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Python Script for Workflow Updates

```python
#!/usr/bin/env python3
"""Update n8n workflow programmatically."""
import requests
import json
import os

N8N_API_URL = "http://localhost:5678/api/v1"
N8N_API_KEY = os.getenv("N8N_API_KEY")  # or read from mcporter.json

headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

def get_workflow(workflow_id):
    r = requests.get(f"{N8N_API_URL}/workflows/{workflow_id}", headers=headers)
    return r.json()

def update_workflow(workflow_id, workflow):
    payload = {
        "name": workflow.get("name"),
        "nodes": workflow.get("nodes"),
        "connections": workflow.get("connections"),
        "settings": {"executionOrder": "v1"}
    }
    r = requests.put(f"{N8N_API_URL}/workflows/{workflow_id}", 
                     headers=headers, json=payload)
    return r.json()

def activate_workflow(workflow_id):
    r = requests.post(f"{N8N_API_URL}/workflows/{workflow_id}/activate", 
                      headers=headers)
    return r.json()

def deactivate_workflow(workflow_id):
    r = requests.post(f"{N8N_API_URL}/workflows/{workflow_id}/deactivate", 
                      headers=headers)
    return r.json()
```

## Files Reference

| File | Purpose |
|------|---------|
| `/docker/n8n/docker-compose.yml` | n8n Docker configuration |
| `/root/clawd/config/mcporter.json` | MCP config including n8n API key |
| `/root/clawd/scripts/update_forex_pair.py` | Example: updating workflow via API |

## Quick Checklist

Before deploying an n8n workflow:

- [ ] All HTTP nodes use `172.18.0.1` (not localhost)
- [ ] Webhook has unique path
- [ ] Webhook has valid `webhookId`
- [ ] Workflow is activated after any changes
- [ ] Backend services are running and accessible
- [ ] Test webhook endpoint returns expected response

---

## Best Practices

### 1. Workflow Design
- **Always test webhooks** after creation/modification — deactivate → update → reactivate
- **Use Set nodes** to normalize data early in the flow
- **Add Error Trigger** nodes for critical workflows to catch failures
- **Use sub-workflows** for reusable logic (call with Execute Workflow node)

### 2. n8n Performance
- **Queue mode enabled** — heavy executions offload to worker
- **Use batch processing** for large datasets (split into chunks)
- **Avoid infinite loops** — always add exit conditions
- **Set timeouts** on HTTP Request nodes (default is too long)

### 3. Docker Services
- **Always use `restart: always`** for production services
- **Mount code as volumes** — allows hot updates without rebuild
- **Use Traefik labels** for auto-SSL and routing
- **Log to stdout** — Docker captures logs automatically

### 4. API Development
- **Return JSON** with consistent structure: `{success: bool, data/error: ...}`
- **Add health endpoints** (`/health`) for monitoring
- **Use CORS** for frontend access (`flask-cors`)
- **Handle errors gracefully** — return proper HTTP codes

### 5. Security
- **Never expose n8n directly** — use Traefik reverse proxy
- **API keys in environment variables** — not in code
- **Use webhook secrets** for Stripe webhooks
- **Docker internal network** — services communicate privately

---

## Common Issues & Fixes

### 1. n8n Can't Reach Host Service
**Symptom:** HTTP Request node returns connection refused  
**Cause:** Using `localhost` instead of Docker gateway  
**Fix:** Use `http://172.18.0.1:PORT` for host services

### 2. Webhook Returns 404
**Symptom:** Webhook URL not found after workflow update  
**Cause:** Webhook not re-registered after path change  
**Fix:** Deactivate workflow → Save → Reactivate workflow

### 3. Workflow Execution Stuck
**Symptom:** Execution shows "running" forever  
**Cause:** Worker not processing queue  
**Fix:** 
```bash
docker restart n8n-n8n-worker-1
```

### 4. Charts Not Displaying (TA API)
**Symptom:** Chart endpoint returns 404  
**Cause:** Chart directory not mounted or wrong path  
**Fix:** Check volume mount in docker-compose:
```yaml
volumes:
  - /root/clawd/research/charts:/app/charts
```

### 5. Chinese Characters Display as Boxes
**Symptom:** Charts show □□□ instead of Chinese  
**Cause:** CJK fonts not installed in container  
**Fix:** Add to Dockerfile/command:
```bash
apt-get update && apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra
```

### 6. SSL Certificate Not Renewing
**Symptom:** HTTPS shows expired certificate  
**Cause:** Traefik ACME challenge failed  
**Fix:**
```bash
# Check Traefik logs
docker logs n8n-traefik-1 | grep -i acme

# Force renewal by restarting
docker restart n8n-traefik-1
```

### 7. RSS Feed Returns Empty
**Symptom:** RSS server returns empty feed  
**Cause:** Source website changed structure  
**Fix:** Update scraping selectors in `/root/clawd/rss_server.py`

### 8. n8n Database Connection Lost
**Symptom:** n8n shows database error  
**Cause:** PostgreSQL container restarted  
**Fix:**
```bash
docker restart n8n-n8n-1 n8n-n8n-worker-1
```

### 9. Workflow Import Fails
**Symptom:** Imported workflow has broken connections  
**Cause:** Node IDs conflict with existing workflows  
**Fix:** Export as JSON → manually change node IDs → re-import

### 10. Container Uses Too Much Memory
**Symptom:** Container killed by OOM  
**Cause:** No memory limits set  
**Fix:** Add to docker-compose:
```yaml
deploy:
  resources:
    limits:
      memory: 512M
```

---

## Maintenance Checklist

### Weekly
- [ ] Review n8n execution logs for errors
- [ ] Check disk space (`df -h`)
- [ ] Verify RSS feeds are generating content

### Monthly
- [ ] Update Docker images (`docker compose pull`)
- [ ] Review and clean old executions
- [ ] Backup n8n workflows (export JSON)
- [ ] Check SSL certificate expiry

### Backup Commands
```bash
# Export all workflows
curl -s "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: <KEY>" | jq > n8n_workflows_backup.json

# Backup PostgreSQL
docker exec n8n-postgres pg_dump -U n8n n8ndb > n8n_db_backup.sql

# Backup Docker volumes
docker run --rm -v n8n_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/n8n_data_backup.tar.gz /data
```
