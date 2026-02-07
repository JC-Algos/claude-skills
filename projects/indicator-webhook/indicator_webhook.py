#!/usr/bin/env python3
"""
Indicator Subscription Webhook Handler
Receives Stripe webhooks for indicator subscriptions and:
1. Saves to Supabase indicator_subscriptions table
2. Sends Telegram notification to Jason
"""

import os
import json
import stripe
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Config
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.environ.get('STRIPE_INDICATOR_WEBHOOK_SECRET')
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://nwhyoravkuyiuewlfgfw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8500544907:AAHHt-h4H3PbikKqUYPFsHGKoJ9iI9wIxZg')
JASON_CHAT_ID = '1016466977'

# Initialize Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram(message):
    """Send notification to Jason via Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            'chat_id': JASON_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'indicator-webhook'})

@app.route('/webhook/indicator', methods=['POST'])
def indicator_webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature')
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except ValueError as e:
        print(f"Invalid payload: {e}")
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {e}")
        return 'Invalid signature', 400
    
    event_type = event['type']
    data = event['data']['object']
    
    print(f"📥 Received event: {event_type}")
    
    # Handle checkout.session.completed (new subscription)
    if event_type == 'checkout.session.completed':
        handle_new_subscription(data)
    
    # Handle subscription cancelled
    elif event_type == 'customer.subscription.deleted':
        handle_cancellation(data)
    
    return jsonify({'received': True})

def handle_new_subscription(session):
    """Handle new indicator subscription"""
    try:
        email = session.get('customer_email') or session.get('customer_details', {}).get('email')
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        # Get TradingView username from custom fields
        tv_username = None
        custom_fields = session.get('custom_fields', [])
        for field in custom_fields:
            if 'tradingview' in field.get('key', '').lower() or 'tradingview' in field.get('label', {}).get('custom', '').lower():
                tv_username = field.get('text', {}).get('value')
                break
        
        # Fallback: check all custom fields
        if not tv_username and custom_fields:
            tv_username = custom_fields[0].get('text', {}).get('value', 'UNKNOWN')
        
        if not tv_username:
            tv_username = 'NOT_PROVIDED'
        
        # Get indicator_id from product metadata
        indicator_id = 'trend_momentum'  # Default
        if subscription_id:
            try:
                sub = stripe.Subscription.retrieve(subscription_id, expand=['items.data.price.product'])
                for item in sub.get('items', {}).get('data', []):
                    product = item.get('price', {}).get('product', {})
                    if isinstance(product, dict):
                        indicator_id = product.get('metadata', {}).get('indicator_id', indicator_id)
            except Exception as e:
                print(f"Error getting product metadata: {e}")
        
        print(f"✅ New subscription: {email} | TV: {tv_username} | Indicator: {indicator_id}")
        
        # Save to Supabase
        if supabase:
            supabase.table('indicator_subscriptions').insert({
                'email': email,
                'tv_username': tv_username,
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id,
                'indicator_id': indicator_id,
                'status': 'active'
            }).execute()
            print("💾 Saved to Supabase")
        
        # Send Telegram notification
        msg = f"""🎉 <b>New Indicator Subscription!</b>

📧 Email: {email}
📺 TradingView: <code>{tv_username}</code>
📊 Indicator: {indicator_id}

⚡ <b>Action needed:</b> Add <code>{tv_username}</code> to Pine Script access"""
        
        send_telegram(msg)
        
    except Exception as e:
        print(f"❌ Error handling new subscription: {e}")
        send_telegram(f"⚠️ Webhook error: {e}")

def handle_cancellation(subscription):
    """Handle subscription cancellation"""
    try:
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        
        # Update Supabase
        if supabase and subscription_id:
            result = supabase.table('indicator_subscriptions').update({
                'status': 'cancelled',
                'cancelled_at': datetime.utcnow().isoformat()
            }).eq('stripe_subscription_id', subscription_id).execute()
            
            # Get the record for notification
            record = supabase.table('indicator_subscriptions').select('*').eq('stripe_subscription_id', subscription_id).execute()
            
            if record.data:
                r = record.data[0]
                msg = f"""❌ <b>Indicator Subscription Cancelled</b>

📧 Email: {r.get('email')}
📺 TradingView: <code>{r.get('tv_username')}</code>
📊 Indicator: {r.get('indicator_id')}

⚡ <b>Action needed:</b> Remove <code>{r.get('tv_username')}</code> from Pine Script access"""
                
                send_telegram(msg)
                print(f"🚫 Cancelled: {r.get('email')}")
        
    except Exception as e:
        print(f"❌ Error handling cancellation: {e}")

if __name__ == '__main__':
    print("🚀 Indicator Webhook Server starting...")
    print(f"   Supabase: {'✅ Connected' if supabase else '❌ Not configured'}")
    app.run(host='0.0.0.0', port=5010)
