# Tailscale VPS Access Guide

## What is Tailscale?

Tailscale creates a secure private network between your devices using WireGuard. Once set up, you can access your VPS from anywhere like it's on the same local network.

**Benefits:**
- Access VPS from phone/laptop anywhere in the world
- Encrypted connection (like a VPN but easier)
- No need to expose ports publicly
- Access internal services (Clawdbot dashboard, n8n, etc.)

---

## Setup Steps

### 1. Login on VPS (First Time)

```bash
# On the VPS (as root)
tailscale up
```

This will give you a login URL. Open it in your browser and sign in with your Tailscale account (Google, Microsoft, GitHub, or email).

### 2. Install Tailscale on Your Devices

**iPhone/Android:**
1. Download "Tailscale" app from App Store / Play Store
2. Open app and sign in with the same account

**Mac/Windows:**
1. Download from https://tailscale.com/download
2. Install and sign in

**Linux/Other:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

### 3. Verify Connection

Once logged in on both devices, check the Tailscale admin panel:
https://login.tailscale.com/admin/machines

You should see:
- **srv1295571** (your VPS)
- Your phone/laptop

Each device gets a Tailscale IP (usually `100.x.x.x`).

---

## Using Tailscale to Access VPS

### Find Your VPS IP

```bash
# On VPS
tailscale ip -4
```

Example output: `100.101.102.103`

You can also find it in the Tailscale admin panel.

### SSH from Phone/Laptop

**Option 1: Use Tailscale IP**
```bash
ssh root@100.101.102.103
```

**Option 2: Use MagicDNS (easier to remember)**
```bash
ssh root@srv1295571
```

Tailscale automatically creates DNS names for your devices!

### Access Web Services

Once connected to Tailscale, you can access internal services:

| Service | URL (via Tailscale) |
|---------|---------------------|
| Clawdbot Dashboard | `http://100.101.102.103:18789` or `http://srv1295571:18789` |
| n8n | `http://100.101.102.103:5678` or `http://srv1295571:5678` |
| TA API | `http://100.101.102.103:5003` or `http://srv1295571:5003` |

**From your phone:** Just open Safari/Chrome and type the URL while connected to Tailscale.

---

## Useful Commands

### On VPS

```bash
# Check status
tailscale status

# Show your Tailscale IP
tailscale ip -4

# Logout
tailscale logout

# Reconnect
tailscale up
```

### On Phone/Laptop

Just toggle the Tailscale app ON/OFF.

---

## Clawdbot + Tailscale Integration

Clawdbot has built-in Tailscale support. To enable:

```bash
clawdbot config
# Navigate to: gateway → tailscale → mode: "on"
```

Or edit config directly:
```json
{
  "gateway": {
    "tailscale": {
      "mode": "on"
    }
  }
}
```

This makes the Clawdbot dashboard accessible ONLY via Tailscale (more secure).

---

## Troubleshooting

**VPS shows "Logged out":**
```bash
tailscale up
```
Follow the login URL.

**Can't connect from phone:**
1. Check Tailscale app is ON
2. Verify both devices are in the same Tailscale network (admin panel)
3. Try pinging: `ping 100.101.102.103`

**SSH still asks for password:**
Tailscale doesn't handle SSH keys. You still need:
- Password authentication, or
- SSH key in `~/.ssh/authorized_keys`

---

## Security Tips

1. **Enable MFA** on your Tailscale account (Settings → Security)
2. **Use ACLs** to restrict which devices can access what (advanced)
3. **Never share** your Tailscale login with anyone
4. **Expire unused devices** in the admin panel

---

## Quick Start (TL;DR)

**On VPS:**
```bash
tailscale up
# Follow login URL
```

**On Phone:**
1. Install Tailscale app
2. Sign in
3. Toggle ON
4. SSH: `ssh root@srv1295571`
5. Dashboard: `http://srv1295571:18789`

Done! 🐷

---

## Links

- Tailscale Dashboard: https://login.tailscale.com/admin
- Download: https://tailscale.com/download
- Docs: https://tailscale.com/kb
