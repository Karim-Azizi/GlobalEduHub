from django.conf import settings
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status
from myproject.models import AccountCreation
from myproject.serializers import PaymentSerializer
from myproject.views.payment_helpers import (
    handle_stripe_payment, 
    handle_paypal_payment, 
    handle_google_pay
)
from myproject.views.payment_utils import (
    save_payment_data, 
    update_payment_status
)

# Initialize logger
logger = logging.getLogger(__name__)

class ProcessPaymentView(APIView):
    """
    API endpoint for processing payments using Stripe, PayPal, and Google Pay.
    """

    def post(self, request):
        try:
            # Parse and validate incoming data
            data = JSONParser().parse(request)
            serializer = PaymentSerializer(data=data)
            if not serializer.is_valid():
                return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            # Extract validated fields
            email = serializer.validated_data["user"]
            payment_method = serializer.validated_data["payment_method"]
            amount = serializer.validated_data["amount"]
            google_pay_token = data.get("googlePayToken")

            # Validate user existence
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                logger.error(f"User with email {email} not found.")
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            # Process payment based on payment method
            if payment_method == "Stripe":
                return self._handle_stripe_payment(user, amount)
            elif payment_method == "PayPal":
                return self._handle_paypal_payment(user, amount)
            elif payment_method == "GooglePay" and google_pay_token:
                return self._handle_google_pay_payment(user, amount, google_pay_token)
            else:
                return Response(
                    {"error": "Invalid payment method or missing Google Pay token."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            return Response(
                {"error": "Payment processing failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _handle_stripe_payment(self, user, amount):
        """
        Handles Stripe payments.
        """
        try:
            payment_intent = handle_stripe_payment(user, amount)
            save_payment_data(user, "Stripe", payment_intent.id, amount)
            update_payment_status(user, "Stripe Payment Successful", amount)
            return Response(
                {"message": "Stripe payment successful.", "client_secret": payment_intent.client_secret},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            logger.error(f"Stripe Payment Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_paypal_payment(self, user, amount):
        """
        Handles PayPal payments.
        """
        try:
            approval_url = handle_paypal_payment(amount)
            save_payment_data(user, "PayPal", None, amount)
            update_payment_status(user, "PayPal Payment Pending", amount)
            return Response(
                {"message": "PayPal payment initiated.", "approval_url": approval_url},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            logger.error(f"PayPal Payment Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_google_pay_payment(self, user, amount, token):
        """
        Handles Google Pay payments.
        """
        try:
            response = handle_google_pay(token, amount)
            if response.get("status") == "success":
                save_payment_data(user, "Google Pay", response["transaction_id"], amount)
                update_payment_status(user, "Google Pay Payment Successful", amount)
                return Response(
                    {"message": "Google Pay payment successful.", "transaction_id": response["transaction_id"]},
                    status=status.HTTP_200_OK
                )
            else:
                logger.error("Google Pay transaction failed.")
                return Response({"error": "Google Pay transaction failed."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            logger.error(f"Google Pay Payment Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)