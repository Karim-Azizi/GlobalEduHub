from django.contrib.auth.backends import BaseBackend
from .models import CustomUser  # Import the CustomUser model

class EmailBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Use CustomUser instead of User
            user = CustomUser.objects.get(email=username)  # Use email as the username field
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:  # Handle exception for CustomUser
            return None

    def get_user(self, user_id):
        try:
            # Use CustomUser instead of User
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:  # Handle exception for CustomUser
            return None