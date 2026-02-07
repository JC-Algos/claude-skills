---
name: stripe-backend
description: Use when building or debugging Stripe payment backends with webhooks, subscription billing, free trials, coupons, or customer portal integration. Use when webhooks return 400/signature errors or users not upgraded after payment.
---

# Stripe Backend Development

## Overview

Build Flask/Python backends that handle Stripe subscriptions, trials, and webhooks. The critical insight: **Stripe communicates via webhooks** — your backend must listen for events and update your database accordingly.

## When to Use

- Building subscription/payment flow
- Free trial implementation
- Coupon/discount codes
- Webhook returns 400 errors
- Users not upgraded after payment
- "Invalid signature" errors

## Core Architecture

```
User → Your Frontend → Stripe Checkout → Stripe
                                            ↓
Your Database ← Your Backend ← Stripe Webhooks
```

## Required Webhook Events

**Enable ALL 5 in Stripe Dashboard → Developers → Webhooks:**

| Event | When It Fires | Your Action |
|-------|---------------|-------------|
| `checkout.session.completed` | Payment/signup done | Upgrade user (fallback) |
| `customer.subscription.created` | **Trial starts** ⚠️ | Upgrade to premium |
| `customer.subscription.updated` | Status changes | Sync status |
| `customer.subscription.deleted` | Cancelled | Downgrade to free |
| `invoice.payment_failed` | Payment fails | Notify user |

⚠️ **Most common mistake:** Missing `customer.subscription.created` — trials never upgrade users!

## Minimal Backend Template

```python
import os
import stripe
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Config from environment
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')  # Must include whsec_ prefix!
supabase = create_client(
    os.environ.get('SUPABASE_URL'),
    os.environ.get('SUPABASE_SERVICE_KEY')
)

@app.route('/api/stripe/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400  # Wrong WEBHOOK_SECRET!
    
    data = event['data']['object']
    user_id = data.get('metadata', {}).get('user_id')
    
    if event['type'] == 'customer.subscription.created':
        # CRITICAL: Handles trials!
        if user_id and data['status'] in ['active', 'trialing']:
            supabase.table('users').update({
                'status': 'premium'
            }).eq('id', user_id).execute()
    
    elif event['type'] == 'customer.subscription.deleted':
        if user_id:
            supabase.table('users').update({
                'status': 'free'
            }).eq('id', user_id).execute()
    
    return jsonify({'received': True})

if __name__ == '__main__':
    app.run(port=5007)
```

## Stripe Dashboard Setup

### 1. Create Webhook Endpoint

1. Go to **Developers → Webhooks**
2. Click **Add endpoint**
3. URL: `https://your-api.com/api/stripe/webhook`
4. Select events (all 5 above)
5. Click **Add endpoint**

### 2. Get Webhook Secret

1. Click on your endpoint
2. Click **Reveal** next to "Signing secret"
3. Copy the `whsec_...` value
4. Add to your `.env`: `STRIPE_WEBHOOK_SECRET=whsec_xxxxx`

### 3. Enable Trial/Coupon Events

In webhook settings, ensure these are checked:
- ☑️ `customer.subscription.created`
- ☑️ `customer.subscription.updated`
- ☑️ `customer.subscription.deleted`
- ☑️ `checkout.session.completed`

## Required .env Variables

```bash
STRIPE_SECRET_KEY=sk_live_...      # From Stripe Dashboard → API keys
STRIPE_WEBHOOK_SECRET=whsec_...    # MUST include whsec_ prefix!
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

## Adding Free Trial

In checkout session creation:

```python
checkout_session = stripe.checkout.Session.create(
    # ... other params ...
    subscription_data={
        'trial_period_days': 7,
        'metadata': {'user_id': user_id}
    }
)
```

**Important:** Trial fires `customer.subscription.created` with `status: 'trialing'`, NOT `checkout.session.completed`!

## Adding Coupon/Discount

### 1. Create Coupon in Stripe Dashboard

Stripe Dashboard → Products → Coupons → Create

### 2. Apply in Checkout

```python
checkout_session = stripe.checkout.Session.create(
    # ... other params ...
    discounts=[{'coupon': 'YOUR_COUPON_ID'}],
    # OR allow user promo codes:
    allow_promotion_codes=True  # Can't use both!
)
```

⚠️ **Cannot combine `discounts` and `allow_promotion_codes`** — choose one.

## Common Issues & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| Webhook returns 400 | Wrong webhook secret | Check `whsec_` prefix in .env |
| Users not upgraded | Missing event | Enable `customer.subscription.created` |
| "Invalid signature" | Secret mismatch | Re-copy from Stripe Dashboard |
| Trial not working | Wrong handler | Handle `trialing` status |
| Backend won't start | Missing deps | Use venv with all packages |

## Debugging Commands

```bash
# Check if backend is healthy
curl https://your-api.com/api/stripe/health

# Check backend logs
tail -100 /path/to/stripe_backend.log | grep -E "(webhook|subscription|✅|🆕)"

# Check recent Stripe events
curl -s "https://api.stripe.com/v1/events?limit=5" \
  -H "Authorization: Bearer sk_live_xxx" | jq '.data[].type'

# Test webhook manually
stripe trigger customer.subscription.created
```

## Deployment Checklist

- [ ] All 5 webhook events enabled in Stripe
- [ ] Webhook secret has `whsec_` prefix
- [ ] SUPABASE_URL is real (not placeholder)
- [ ] Backend accessible via HTTPS
- [ ] Health endpoint returns 200
- [ ] Test with real subscription flow
