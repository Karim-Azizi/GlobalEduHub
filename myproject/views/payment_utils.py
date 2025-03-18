from django.conf import settings
import logging
from django.utils.timezone import now
from myproject.models import Payment, CourseSelection, RegistrationStep

# Initialize logger
logger = logging.getLogger(__name__)

def save_payment_data(user, payment_method, transaction_id, amount):
    """
    Saves payment details into the database.
    """
    try:
        logger.info(f"Saving payment data for user: {user.email}")
        Payment.objects.create(
            user=user,
            payment_method=payment_method,
            transaction_id=transaction_id,
            amount=amount,
            payment_status=True,
            payment_date=now()
        )
        logger.info("Payment data saved successfully.")
    except Exception as e:
        logger.error(f"Error saving payment data: {str(e)}")
        raise ValueError("Failed to save payment data.")

def update_payment_status(user, message, amount):
    """
    Updates the payment status and registration progress.
    """
    try:
        logger.info(f"Updating payment status for user: {user.email}")
        
        # Update payment status
        Payment.objects.update_or_create(
            user=user,
            defaults={
                "payment_status": True,
                "payment_date": now(),
                "amount": amount,
            }
        )
        # Update CourseSelection
        CourseSelection.objects.filter(user=user).update(payment_status="Completed")

        # Update Registration Progress
        RegistrationStep.objects.update_or_create(
            user=user,
            defaults={
                "current_step": 7,  # Assuming Payment step is step 6
                "last_visited": now(),
                "progress_notes": message,
            }
        )
        logger.info("Payment status updated successfully.")
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")
        raise ValueError("Failed to update payment status.")