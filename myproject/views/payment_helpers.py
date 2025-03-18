from django.conf import settings
import logging
import stripe
import paypalrestsdk
# Initialize logger
logger = logging.getLogger(__name__)

# Stripe Configuration
stripe.api_key = settings.STRIPE_SECRET_KEY

# PayPal Configuration
paypalrestsdk.configure({
    "mode": "sandbox",  # Use "live" for production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET,
})

def handle_stripe_payment(user, amount):
    """
    Processes payments using Stripe and returns the PaymentIntent object.
    """
    try:
        logger.info(f"Processing Stripe payment for user: {user.email}")
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            receipt_email=user.email,
            payment_method_types=["card"]
        )
        logger.info(f"Stripe PaymentIntent created successfully: {payment_intent.id}")
        return payment_intent
    except Exception as e:
        logger.error(f"Stripe Payment Error: {str(e)}")
        raise ValueError("Failed to process Stripe payment.")

def handle_paypal_payment(amount):
    """
    Processes payments using PayPal and returns the approval URL.
    """
    try:
        logger.info("Creating PayPal payment order...")
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": f"{float(amount):.2f}", "currency": "USD"}
            }],
            "redirect_urls": {
                "return_url": settings.PAYPAL_SUCCESS_URL,
                "cancel_url": settings.PAYPAL_CANCEL_URL,
            },
        })
        if payment.create():
            approval_url = next(link["href"] for link in payment["links"] if link["rel"] == "approval_url")
            logger.info(f"PayPal Payment created: {approval_url}")
            return approval_url
        else:
            raise ValueError("Failed to create PayPal payment.")
    except Exception as e:
        logger.error(f"PayPal Payment Error: {str(e)}")
        raise ValueError("Failed to process PayPal payment.")

def handle_google_pay(token, amount):
    """
    Simulates Google Pay payment processing.
    """
    try:
        logger.info(f"Processing Google Pay payment for amount: ${amount}")
        if not token:
            raise ValueError("Google Pay token is missing.")
        return {"status": "success", "transaction_id": f"GOOGLEPAY-{token}"}
    except Exception as e:
        logger.error(f"Google Pay Error: {str(e)}")
        raise ValueError("Failed to process Google Pay payment.")