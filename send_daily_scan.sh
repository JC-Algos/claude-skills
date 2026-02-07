#!/bin/bash
# Run daily HSI scan and send to Telegram via Clawdbot

cd /root/clawd

# Run the scan
SCAN_OUTPUT=$(python3 hsi_daily_scan.py 2>&1)

# Use clawdbot CLI to send message to the main session/telegram
# This will send the message back to Jason on Telegram
echo "$SCAN_OUTPUT" | clawdbot msg --channel telegram --to 1016466977
