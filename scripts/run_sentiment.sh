#!/bin/bash
cd /root/clawd/projects/market-analyzer/sentiment
python3 market_sentiment.py >> /tmp/sentiment_cron.log 2>&1
