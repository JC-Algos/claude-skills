# ==========================================
# UPDATED CONFIGURATION
# ==========================================

PRICE_IDS = {
    'basic_monthly': 'price_1SnjiK1JIZhXOZpFl8dhRnTu',
    'basic_annual': 'price_1Strgb1JIZhXOZpFoZZWjhrr'
}

# Intro offer coupon (create this in Stripe Dashboard)
# HKD 100 off for 3 months = HKD 199/mo instead of 299
INTRO_COUPON_ID = 'YOUR_COUPON_ID_HERE'  # Replace after creating coupon

# Free trial days for new users
FREE_TRIAL_DAYS = 7


# ==========================================
# UPDATED CHECKOUT ENDPOINT
# ==========================================
@app.route('/api/stripe/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.json or {}
        user_email = data.get('email')
        user_id = data.get('user_id')
        price_id = data.get('price_id', PRICE_IDS['basic_monthly'])
        
        logger.info(f"Attempting Checkout for: {user_email}, price: {price_id}")

        if not user_email or not user_id:
            return jsonify({'error': 'Missing email or user_id'}), 400

        # Check if user is new (no previous subscription)
        is_new_user = True
        try:
            customers = stripe.Customer.list(email=user_email, limit=1)
            if customers.data:
                # Check if they had a subscription before
                subs = stripe.Subscription.list(customer=customers.data[0].id, limit=1)
                if subs.data:
                    is_new_user = False
        except Exception as e:
            logger.warning(f"Error checking customer history: {e}")

        # Build subscription data
        subscription_data = {
            'metadata': {'user_id': user_id}
        }

        # Apply intro offer for new monthly subscribers only
        discounts = []
        if is_new_user and price_id == PRICE_IDS['basic_monthly']:
            # 7-day free trial
            subscription_data['trial_period_days'] = FREE_TRIAL_DAYS
            # HKD 199 for first 3 months (HKD 100 off coupon)
            if INTRO_COUPON_ID and INTRO_COUPON_ID != 'YOUR_COUPON_ID_HERE':
                discounts = [{'coupon': INTRO_COUPON_ID}]

        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': [{'price': price_id, 'quantity': 1}],
            'mode': 'subscription',
            'success_url': f'{WEBSITE_BASE_URL}/index.html?subscription=success',
            'cancel_url': f'{WEBSITE_BASE_URL}/subscribe.html?cancelled=true',
            'customer_email': user_email,
            'subscription_data': subscription_data,
            'allow_promotion_codes': True  # Allow manual promo codes too
        }

        # Add discounts if applicable
        if discounts:
            checkout_params['discounts'] = discounts

        checkout_session = stripe.checkout.Session.create(**checkout_params)

        return jsonify({
            'id': checkout_session.id, 
            'url': checkout_session.url,
            'is_new_user': is_new_user,
            'has_trial': is_new_user and price_id == PRICE_IDS['basic_monthly']
        })

    except Exception as e:
        logger.error(f"CRITICAL STRIPE ERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500
