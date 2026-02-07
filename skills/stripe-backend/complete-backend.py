"""
Complete Stripe Backend with Subscriptions, Trials, and Webhooks
================================================================

This is a production-ready template. Copy and customize for your project.

Required .env:
    STRIPE_SECRET_KEY=sk_live_...
    STRIPE_WEBHOOK_SECRET=whsec_...  (MUST include whsec_ prefix!)
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_SERVICE_KEY=eyJ...
    WEBSITE_BASE_URL=https://your-site.com

Required pip packages:
    pip install stripe flask flask-cors supabase python-dotenv

Stripe Dashboard webhook events to enable:
    - checkout.session.completed
    - customer.subscription.created  (CRITICAL for trials!)
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_failed (optional, for notifications)
"""

import os
import stripe
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment
load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================================
# CONFIGURATION
# ===========================================

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '').strip()
WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '').strip()
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '').strip()
WEBSITE_URL = os.environ.get('WEBSITE_BASE_URL', 'https://example.com')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# Price IDs from Stripe Dashboard
PRICES = {
    'monthly': os.environ.get('STRIPE_PRICE_MONTHLY', ''),
    'annual': os.environ.get('STRIPE_PRICE_ANNUAL', '')
}

# Optional: Coupon for intro offer
INTRO_COUPON = os.environ.get('STRIPE_INTRO_COUPON', '')

# Free trial days
TRIAL_DAYS = int(os.environ.get('FREE_TRIAL_DAYS', '7'))


# ===========================================
# HEALTH CHECK
# ===========================================

@app.route('/api/stripe/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'stripe_configured': bool(stripe.api_key),
        'supabase_configured': bool(supabase),
        'version': '1.0'
    })


# ===========================================
# CHECKOUT SESSION (Start subscription)
# ===========================================

@app.route('/api/stripe/create-checkout-session', methods=['POST'])
def create_checkout():
    try:
        data = request.json or {}
        email = data.get('email')
        user_id = data.get('user_id')
        price_id = data.get('price_id', PRICES['monthly'])

        if not email or not user_id:
            return jsonify({'error': 'Missing email or user_id'}), 400

        logger.info(f"Creating checkout for: {email}")

        # Subscription metadata (passed to webhooks)
        subscription_data = {
            'metadata': {'user_id': user_id}
        }

        # Add trial for new users
        subscription_data['trial_period_days'] = TRIAL_DAYS

        # Build checkout params
        params = {
            'payment_method_types': ['card'],
            'line_items': [{'price': price_id, 'quantity': 1}],
            'mode': 'subscription',
            'success_url': f'{WEBSITE_URL}/success',
            'cancel_url': f'{WEBSITE_URL}/cancelled',
            'customer_email': email,
            'subscription_data': subscription_data
        }

        # Add coupon OR allow promo codes (can't do both!)
        if INTRO_COUPON:
            params['discounts'] = [{'coupon': INTRO_COUPON}]
        else:
            params['allow_promotion_codes'] = True

        session = stripe.checkout.Session.create(**params)

        return jsonify({
            'id': session.id,
            'url': session.url
        })

    except Exception as e:
        logger.error(f"Checkout error: {e}")
        return jsonify({'error': str(e)}), 500


# ===========================================
# CUSTOMER PORTAL (Manage subscription)
# ===========================================

@app.route('/api/stripe/create-portal-session', methods=['POST'])
def create_portal():
    try:
        data = request.json or {}
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email required'}), 400

        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return jsonify({'error': 'No Stripe customer found'}), 404

        session = stripe.billing_portal.Session.create(
            customer=customers.data[0].id,
            return_url=WEBSITE_URL
        )

        return jsonify({'url': session.url})

    except Exception as e:
        logger.error(f"Portal error: {e}")
        return jsonify({'error': str(e)}), 500


# ===========================================
# WEBHOOK HANDLER (The automation!)
# ===========================================

@app.route('/api/stripe/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature')

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except ValueError:
        logger.error("Invalid payload")
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature - check STRIPE_WEBHOOK_SECRET")
        return 'Invalid signature', 400

    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Webhook received: {event_type}")

    # Get user_id from metadata
    user_id = data.get('metadata', {}).get('user_id')

    # Fallback: check subscription metadata
    if not user_id and data.get('subscription'):
        try:
            sub = stripe.Subscription.retrieve(data['subscription'])
            user_id = sub.metadata.get('user_id')
        except Exception:
            pass

    # ----------------------------------------
    # HANDLE: Checkout completed (payment done)
    # ----------------------------------------
    if event_type == 'checkout.session.completed':
        if user_id and supabase:
            logger.info(f"✅ Checkout completed for user: {user_id}")
            supabase.table('user_profiles').update({
                'subscription_status': 'active',
                'membership_status': 'premium',
                'stripe_customer_id': data.get('customer')
            }).eq('id', user_id).execute()

    # ----------------------------------------
    # HANDLE: Subscription CREATED (includes trials!)
    # ----------------------------------------
    elif event_type == 'customer.subscription.created':
        status = data.get('status')  # 'active' or 'trialing'

        if user_id and supabase and status in ['active', 'trialing']:
            logger.info(f"🆕 Subscription created for user: {user_id}, status: {status}")
            supabase.table('user_profiles').update({
                'subscription_status': status,
                'membership_status': 'premium',
                'stripe_customer_id': data.get('customer')
            }).eq('id', user_id).execute()

    # ----------------------------------------
    # HANDLE: Subscription UPDATED (status changes)
    # ----------------------------------------
    elif event_type == 'customer.subscription.updated':
        status = data.get('status')

        if user_id and supabase:
            logger.info(f"📝 Subscription updated for user: {user_id}, status: {status}")

            if status in ['active', 'trialing']:
                supabase.table('user_profiles').update({
                    'subscription_status': status,
                    'membership_status': 'premium'
                }).eq('id', user_id).execute()

    # ----------------------------------------
    # HANDLE: Subscription DELETED (cancelled)
    # ----------------------------------------
    elif event_type == 'customer.subscription.deleted':
        if user_id and supabase:
            logger.info(f"🚫 Subscription cancelled for user: {user_id}")
            supabase.table('user_profiles').update({
                'subscription_status': 'cancelled',
                'membership_status': 'free'
            }).eq('id', user_id).execute()

    # ----------------------------------------
    # HANDLE: Payment failed
    # ----------------------------------------
    elif event_type == 'invoice.payment_failed':
        customer_id = data.get('customer')
        logger.warning(f"⚠️ Payment failed for customer: {customer_id}")
        # TODO: Send email notification to user

    return jsonify({'received': True})


# ===========================================
# RUN SERVER
# ===========================================

if __name__ == '__main__':
    # Startup checks
    if not stripe.api_key:
        logger.warning("⚠️ STRIPE_SECRET_KEY not set!")
    if not WEBHOOK_SECRET:
        logger.warning("⚠️ STRIPE_WEBHOOK_SECRET not set!")
    if not supabase:
        logger.warning("⚠️ Supabase not configured!")

    logger.info(f"🚀 Starting server - Stripe: {'✅' if stripe.api_key else '❌'}, Supabase: {'✅' if supabase else '❌'}")

    app.run(host='0.0.0.0', port=5007)
