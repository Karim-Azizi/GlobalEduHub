from django.conf import settings
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

# Rest Framework JWT Import
from rest_framework_simplejwt.tokens import RefreshToken

# Project-Specific Imports
from ..models import (
    AccountCreation,
    Course,
    Payment,
    AddressDetails,
    RegistrationStep,
    RegistrationStatus,
)

# Initialize Logger
logger = logging.getLogger(__name__)


# Admin Dashboard Statistics
@login_required
def admin_stats(request):
    """
    Provides statistics for the admin dashboard.
    """
    try:
        stats = {
            "total_users": AccountCreation.objects.count(),
            "active_users": AccountCreation.objects.filter(is_active=True).count(),
            "teachers": AccountCreation.objects.filter(user_type="Teacher").count(),
            "students": AccountCreation.objects.filter(user_type="Student").count(),
            "new_users": AccountCreation.objects.filter(date_joined__month=now().month).count(),
        }
        return JsonResponse(stats, status=200)
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# User Growth Data
@login_required
def user_growth(request):
    """
    Provides user growth data for admin dashboard.
    """
    try:
        growth_data = {
            "months": ["January", "February", "March", "April"],
            "new_users": [50, 100, 200, 300],  # Replace this with database query logic
        }
        return JsonResponse(growth_data, status=200)
    except Exception as e:
        logger.error(f"Error fetching user growth data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# Revenue Data
@login_required
def revenue_data(request):
    """
    Provides revenue data for admin dashboard.
    """
    try:
        revenue = {
            "months": ["January", "February", "March", "April"],
            "revenue": [1000, 2000, 3000, 4000],  # Replace with actual logic
        }
        return JsonResponse(revenue, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Payment Management
@login_required
def admin_payments(request):
    """
    Fetches payment details for the admin dashboard.
    """
    try:
        payments = Payment.objects.all().values(
            "user__email", "payment_method", "payment_status",
            "transaction_id", "amount", "payment_date"
        )
        return JsonResponse(list(payments), safe=False, status=200)
    except Exception as e:
        logger.error(f"Error fetching payments: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# Manage Courses
@login_required
def manage_courses(request):
    """
    Fetches, creates, and updates course data.
    """
    try:
        if request.method == "GET":
            courses = Course.objects.all().values(
                "id", "name", "description", "fee", "duration", "is_active"
            )
            return JsonResponse(list(courses), safe=False, status=200)

        elif request.method == "POST":
            data = json.loads(request.body)
            name = data.get("name")
            description = data.get("description", "")
            fee = data.get("fee")
            duration = data.get("duration")
            is_active = data.get("is_active", True)

            if not name or fee is None or not duration:
                return JsonResponse({"error": "Name, fee, and duration are required."}, status=400)

            Course.objects.create(
                name=name, description=description, fee=fee, duration=duration, is_active=is_active
            )
            return JsonResponse({"message": f"Course '{name}' created successfully."}, status=201)

        else:
            return JsonResponse({"error": "Invalid request method."}, status=405)
    except Exception as e:
        logger.error(f"Error managing courses: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# Deactivate Course
@login_required
def deactivate_course(request, course_id):
    """
    Allows admin to deactivate a course.
    """
    try:
        if request.method == "POST":
            course = Course.objects.get(id=course_id)
            course.is_active = False
            course.save()
            return JsonResponse({"message": f"Course '{course.name}' has been deactivated."}, status=200)
        return JsonResponse({"error": "Invalid request method."}, status=405)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found."}, status=404)
    except Exception as e:
        logger.error(f"Error deactivating course: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# Activate Course
@login_required
def activate_course(request, course_id):
    """
    Allows admin to activate a course.
    """
    try:
        if request.method == "POST":
            course = Course.objects.get(id=course_id)
            course.is_active = True
            course.save()
            return JsonResponse({"message": f"Course '{course.name}' has been activated."}, status=200)
        return JsonResponse({"error": "Invalid request method."}, status=405)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found."}, status=404)
    except Exception as e:
        logger.error(f"Error activating course: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# Admin Users Management
@login_required
def admin_users(request):
    """
    Handles admin user management: view, create, and delete users.
    """
    try:
        if request.method == "GET":
            users = AccountCreation.objects.all().values(
                'id', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined'
            )
            return JsonResponse(list(users), safe=False, status=200)

        elif request.method == "POST":
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            user_type = data.get('user_type', 'Student')

            if not email or not password:
                return JsonResponse({"error": "Email and password are required."}, status=400)

            AccountCreation.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                is_active=True
            )
            return JsonResponse({'message': f'User {email} created successfully.'}, status=201)

        elif request.method == "DELETE":
            data = json.loads(request.body)
            user_id = data.get('id')

            if not user_id:
                return JsonResponse({"error": "User ID is required."}, status=400)

            try:
                user = AccountCreation.objects.get(id=user_id)
                user.delete()
                return JsonResponse({'message': f'User with ID {user_id} deleted successfully.'}, status=200)
            except AccountCreation.DoesNotExist:
                return JsonResponse({'error': 'User not found.'}, status=404)

        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=405)

    except Exception as e:
        logger.error(f"Error managing users: {e}")
        return JsonResponse({'error': str(e)}, status=400)


# Admin Login Functionality
@csrf_exempt
def login_user(request):
    """
    Admin login with JWT tokens.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return JsonResponse({"error": "Email and password are required."}, status=400)

            user = authenticate(username=email, password=password)
            if user and user.user_type == "Admin":
                refresh = RefreshToken.for_user(user)
                login(request, user)
                return JsonResponse({
                    "message": "Login successful.",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "user": {
                        "email": user.email,
                        "is_staff": user.is_staff,
                        "is_active": user.is_active,
                    }
                }, status=200)
            return JsonResponse({"error": "Invalid credentials or access denied."}, status=401)
        except Exception as e:
            logger.error(f"Error during admin login: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Admin Notifications
@login_required
def admin_notifications(request):
    """
    Fetches admin notifications.
    """
    try:
        notifications = [
            {"type": "info", "message": "System updated successfully."},
            {"type": "warning", "message": "Check user registration errors."},
        ]
        return JsonResponse(notifications, safe=False, status=200)
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        return JsonResponse({"error": str(e)}, status=500)
    