# Django Imports
from django.conf import settings
import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.utils.timezone import now
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

# Logging
import logging

# Utilities
import re
from datetime import datetime

# Third-Party Imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

# Project Models
from myproject.models import (
    AccountCreation, PersonalInformation, EducationalBackground,
    CourseSelection, AddressDetails, RegistrationStatus,
    RegistrationStep, Payment, Country, City, Course
)

# Project Serializers
from myproject.serializers import (
    PersonalInformationSerializer, EducationalBackgroundSerializer,
    AddressDetailsSerializer, CourseSelectionSerializer, PaymentSerializer
)

# Utility Views
from myproject.views.utility_views import (
    fetch_countries_from_api, fetch_cities_from_nominatim,
    fetch_states_from_nominatim, fetch_and_save_cities,
    get_countries, get_cities, update_countries_and_cities,
    get_phone_code
)

# Payment Views and Utilities
from myproject.views.payment_views import (
    ProcessPaymentView
)
from myproject.views.payment_helpers import (
    handle_stripe_payment, handle_paypal_payment, handle_google_pay
)
from myproject.views.payment_utils import (
    save_payment_data, update_payment_status
)

# Initialize logger
logger = logging.getLogger(__name__)

# Disable SSL verification for local development
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


# Check Email Availability
def check_email_availability(request):
    """
    Check if an email is already registered.
    """
    try:
        email = request.GET.get('email', '').strip()
        if not email:
            return JsonResponse({"available": False, "error": "Email parameter is missing."}, status=400)

        # Check email existence in database
        is_available = not AccountCreation.objects.filter(email=email).exists()
        return JsonResponse({"available": is_available}, status=200)

    except Exception as e:
        logger.error(f"Error checking email availability: {e}")
        return JsonResponse(
            {"available": False, "error": "An unexpected error occurred."}, status=500
        )


# Step 1: Account Creation
@method_decorator(csrf_exempt, name='dispatch')
class AccountCreationView(APIView):
    """
    Handles user account creation and triggers email verification.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            email = data.get("email", "").strip()
            first_name = data.get("first_name", "").strip()
            last_name = data.get("last_name", "").strip()
            password = data.get("password", "").strip()

            # Validate required fields
            if not email or not password or not first_name or not last_name:
                return Response(
                    {"error": "Email, password, first name, and last name are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate email format
            if not self._validate_email_format(email):
                return Response(
                    {"error": "Invalid email format."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if email already exists
            if AccountCreation.objects.filter(email=email).exists():
                return Response(
                    {"error": "An account with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate password strength
            if not self._validate_password_strength(password):
                return Response(
                    {"error": (
                        "Password must be at least 8 characters long, "
                        "contain one uppercase letter, one lowercase letter, "
                        "one number, and one special character."
                    )},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the user and save to database
            user = AccountCreation.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Send email verification
            self._send_email_verification(user)

            # Initialize registration step
            RegistrationStep.objects.create(
                user=user,
                current_step=1,
                last_visited=now()
            )

            return Response(
                {"message": "Account created successfully. Verification email sent."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error during account creation: {e}")
            return Response(
                {"error": "An unexpected error occurred while creating the account."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _validate_email_format(self, email):
        """
        Validate the email format using Django's email validator.
        """
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False

    def _validate_password_strength(self, password):
        """
        Validate password strength.
        """
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):  # At least one uppercase
            return False
        if not re.search(r"[a-z]", password):  # At least one lowercase
            return False
        if not re.search(r"\d", password):  # At least one digit
            return False
        if not re.search(r"[@$!%*?&]", password):  # At least one special character
            return False
        return True

    def _send_email_verification(self, user):
        """
        Simulates sending an email verification (Disable SSL verification for local development).
        """
        try:
            email_verification_url = f"https://localhost:8000/api/verify-email?email={user.email}"
            response = requests.get(email_verification_url, verify=False)  # SSL verification disabled
            if response.status_code == 200:
                logger.info(f"Email verification sent to {user.email}")
            else:
                logger.warning(f"Failed to send email verification to {user.email}: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending email verification: {e}")
# Step 2: Personal Information
class PersonalInformationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Extract data from the request
            data = request.data
            email = data.get("email")
            date_of_birth = data.get("date_of_birth")
            gender = data.get("gender")
            nationality_name = data.get("nationality")
            phone_number = data.get("phone_number", "").strip()
            profile_picture = request.FILES.get("profile_picture")

            # Validate user existence
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                logger.error(f"User with email {email} not found.")
                return Response(
                    {"error": "User not found. Complete account creation first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate nationality
            try:
                nationality = Country.objects.get(name__iexact=nationality_name)
            except Country.DoesNotExist:
                logger.error(f"Invalid nationality name: {nationality_name}")
                return Response(
                    {"error": "Invalid nationality name."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate phone number format
            if not phone_number.startswith("+") or not phone_number[1:].isdigit():
                logger.error(f"Invalid phone number format: {phone_number}")
                return Response(
                    {"error": "Phone number must start with '+' and include only digits after."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate date of birth (user must be 18+)
            try:
                dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                age = (datetime.now().date() - dob).days // 365
                if age < 18:
                    logger.error(f"User is underage: {age} years old.")
                    return Response(
                        {"error": "User must be at least 18 years old."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                logger.error(f"Invalid date of birth format: {date_of_birth}")
                return Response(
                    {"error": "Invalid date of birth format. Use 'YYYY-MM-DD'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Use serializer for data validation and creation/update
            serializer = PersonalInformationSerializer(data={
                "user": user.id,
                "date_of_birth": date_of_birth,
                "gender": gender,
                "phone_number": phone_number,
                "profile_picture": profile_picture,
                "nationality": nationality.id,
            })

            if serializer.is_valid():
                serializer.save()  # Save valid data
                logger.info(f"Personal information saved for user: {email}")
            else:
                logger.error(f"Validation errors: {serializer.errors}")
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update registration step to Step 2
            RegistrationStep.objects.update_or_create(
                user=user, defaults={"current_step": 2, "last_visited": now()}
            )
            logger.info(f"Registration step updated for user: {email}")

            return Response(
                {"message": "Personal information saved successfully."},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception(f"Unexpected error in PersonalInformationView: {e}")
            return Response(
                {"error": "An unexpected error occurred. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        """
        Retrieve existing personal information for the user (if available).
        """
        try:
            email = request.GET.get("email")
            if not email:
                logger.error("Email parameter is missing in the request.")
                return Response(
                    {"error": "Email is required to fetch personal information."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate user existence
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                logger.error(f"User with email {email} not found.")
                return Response(
                    {"error": "User not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch personal information
            personal_info = PersonalInformation.objects.filter(user=user).first()
            if not personal_info:
                logger.info(f"No personal information found for user: {email}")
                return Response(
                    {"message": "No personal information found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Serialize and return data
            serializer = PersonalInformationSerializer(personal_info)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Unexpected error fetching personal information: {e}")
            return Response(
                {"error": "An unexpected error occurred. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
# Step 3: Address Details Step
class AddressDetailsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            email = data.get("email")
            street_address = data.get("streetAddress", "").strip()
            country_id = data.get("country")
            city_name = data.get("city")
            state = data.get("state", "").strip()
            postal_code = data.get("postalCode", "").strip()
            phone_number = data.get("phoneNumber", "").strip()

            # Validate user existence
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                return Response(
                    {"error": "User not found. Complete account creation first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate country
            try:
                country = Country.objects.get(id=country_id)
            except Country.DoesNotExist:
                return Response(
                    {"error": "Invalid country ID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate city or fetch dynamically
            city, created = City.objects.get_or_create(
                name=city_name.strip(), country=country
            )

            # If city is newly created, optionally fetch additional details (e.g., latitude/longitude)
            if created:
                logger.info(f"New city created: {city_name} in {country.name}")
                fetch_cities_from_nominatim(country.name)

            # Validate postal code format
            if not postal_code.isdigit() or len(postal_code) < 4 or len(postal_code) > 10:
                return Response(
                    {"error": "Invalid postal code format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate phone number format
            if not phone_number.startswith("+") or not phone_number[1:].isdigit():
                return Response(
                    {"error": "Phone number must start with '+' and include only digits after."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update or create address details
            address, created = AddressDetails.objects.update_or_create(
                user=user,
                defaults={
                    "street_address": street_address,
                    "city": city,
                    "country": country,
                    "state": state,
                    "postal_code": postal_code,
                    "phone_number": phone_number,
                },
            )

            # Update registration step to Step 3
            RegistrationStep.objects.update_or_create(
                user=user, defaults={"current_step": 3, "last_visited": now()}
            )

            # Log success
            logger.info(f"Address details saved for user: {user.email}")

            return Response(
                {"message": "Address details saved successfully."},
                status=status.HTTP_201_CREATED,
            )

        except AccountCreation.DoesNotExist:
            return Response(
                {"error": "User not found. Complete account creation first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Country.DoesNotExist:
            return Response(
                {"error": "Invalid country selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error in AddressDetailsView: {e}")
            return Response(
                {"error": "An unexpected error occurred while saving address details."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        # Step 4: Educational Background
class EducationalBackgroundView(APIView):
    permission_classes = [AllowAny]
    """
    Collect and manage user's educational background details.
    """

    def post(self, request):
        try:
            # Retrieve the data from the request
            data = request.data
            email = data.get("email")
            degree = data.get("degree", "").strip()
            institution = data.get("institution", "").strip()
            field_of_study = data.get("field_of_study", "").strip()
            graduation_year = data.get("graduation_year")
            honors = data.get("honors", "").strip()

            # Validate user existence
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                return Response(
                    {"error": "User not found. Complete account creation first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate required fields
            if not degree or not institution or not graduation_year:
                return Response(
                    {"error": "Degree, Institution, and Graduation Year are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate graduation year
            if not graduation_year.isdigit() or int(graduation_year) < 1900 or int(graduation_year) > now().year:
                return Response(
                    {"error": "Graduation year must be a valid year between 1900 and the current year."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update or create educational background details
            educational_background, created = EducationalBackground.objects.update_or_create(
                user=user,
                defaults={
                    "degree": degree,
                    "institution": institution,
                    "field_of_study": field_of_study,
                    "graduation_year": graduation_year,
                    "honors": honors,
                },
            )

            # Update registration step to Step 4
            RegistrationStep.objects.update_or_create(
                user=user, defaults={"current_step": 4, "last_visited": now()}
            )

            return Response(
                {"message": "Educational background saved successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in EducationalBackgroundView: {e}")
            return Response(
                {"error": "An unexpected error occurred while saving educational background."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        """
        Fetch educational background details for a user.
        """
        try:
            email = request.GET.get("email")

            # Validate user existence
            user = AccountCreation.objects.get(email=email)

            # Fetch the educational background details
            educational_background = EducationalBackground.objects.filter(user=user).first()

            if not educational_background:
                return Response(
                    {"message": "No educational background details found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Serialize and return the data
            serializer = EducationalBackgroundSerializer(educational_background)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except AccountCreation.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error in fetching EducationalBackgroundView: {e}")
            return Response(
                {"error": "An unexpected error occurred while fetching educational background."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
# Step 5: Course Selection View
class CourseSelectionView(APIView):
    permission_classes = [AllowAny]
    """
    Handles course selection for the registration process.
    Allows users to select multiple courses and calculates the total fee dynamically.
    Includes course recommendations and discounts for bundled options.
    """
    def post(self, request):
        try:
            data = request.data
            email = data.get("email")
            selected_course_ids = data.get("courses", [])
            study_duration = data.get("study_duration", 0)

            # Validate user existence
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                return Response(
                    {"error": "User not found. Complete account creation first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate course selection
            if not selected_course_ids:
                return Response(
                    {"error": "At least one course must be selected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch selected courses
            courses = Course.objects.filter(id__in=selected_course_ids)
            if courses.count() != len(selected_course_ids):
                return Response(
                    {"error": "One or more selected courses are invalid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calculate total fee with optional discounts
            total_fee = sum(course.fee for course in courses)
            discount = self._apply_discount(selected_course_ids, total_fee)

            # Create or update course selection
            course_selection, created = CourseSelection.objects.update_or_create(
                user=user,
                defaults={
                    "study_duration": study_duration,
                    "total_fee": total_fee - discount,
                },
            )
            course_selection.courses.set(courses)

            # Update registration step to Step 5
            RegistrationStep.objects.update_or_create(
                user=user, defaults={"current_step": 5, "last_visited": now()}
            )

            # Prepare response
            response_data = {
                "message": "Course selection saved successfully.",
                "selected_courses": CourseSelectionSerializer(courses, many=True).data,  # Updated
                "study_duration": study_duration,
                "total_fee": total_fee - discount,
                "discount_applied": discount,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in CourseSelectionView: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _apply_discount(self, selected_courses, total_fee):
        """
        Applies a discount for bundled courses.
        """
        discount_percentage = 0
        if len(selected_courses) > 3:  # Apply a 10% discount if 3+ courses are selected
            discount_percentage = 10
        elif len(selected_courses) > 5:  # Apply a 20% discount for 5+ courses
            discount_percentage = 20

        return (total_fee * discount_percentage) / 100


# GET All Available Courses Function
class GetCoursesView(APIView):
    permission_classes = [AllowAny]
    """
    Retrieve a list of all available courses.
    This view is used for populating the course selection step.
    """
    def get(self, request):
        try:
            # Fetch all available courses from the database
            courses = Course.objects.all()

            if not courses.exists():
                return Response(
                    {"message": "No courses available at the moment."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Serialize course data
            serialized_courses = CourseSelectionSerializer(courses, many=True).data  # Updated

            return Response(
                {"courses": serialized_courses, "message": "Courses fetched successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return Response(
                {"error": "An unexpected error occurred while fetching courses."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
# Review Summary Step
class ReviewSummaryView(APIView):
    permission_classes = [AllowAny]
    """
    Displays a summary of all collected registration data:
    - Personal Information
    - Address Details
    - Educational Background
    - Selected Courses
    - Payment Confirmation
    """
    def get(self, request, email):
        try:
            # Validate if the user exists
            user = AccountCreation.objects.get(email=email)
            
            # Fetch data from respective models
            personal_info = PersonalInformation.objects.filter(user=user).first()
            address_details = AddressDetails.objects.filter(user=user).first()
            education_background = EducationalBackground.objects.filter(user=user).first()
            course_selection = CourseSelection.objects.filter(user=user)
            payment = Payment.objects.filter(user=user).first()
            
            # Serialize the data
            personal_info_data = PersonalInformationSerializer(personal_info).data if personal_info else {}
            address_data = AddressDetailsSerializer(address_details).data if address_details else {}
            education_data = EducationalBackgroundSerializer(education_background).data if education_background else {}
            course_data = CourseSelectionSerializer(course_selection, many=True).data if course_selection else []
            payment_data = PaymentSerializer(payment).data if payment else {}

            # Combine all data into a unified structure
            review_summary = {
                "personal_information": personal_info_data,
                "address_details": address_data,
                "educational_background": education_data,
                "selected_courses": course_data,
                "payment_confirmation": payment_data,
            }

            # Return the summary
            return Response({
                "message": "Review summary fetched successfully.",
                "data": review_summary
            }, status=status.HTTP_200_OK)

        except AccountCreation.DoesNotExist:
            logger.error("User not found for review summary.")
            return Response({
                "error": "User not found. Please complete the account creation first."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error fetching review summary: {e}")
            return Response({
                "error": "An unexpected error occurred while fetching review summary."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# Confirmation Step View
class ConfirmationView(APIView):
    permission_classes = [AllowAny]
    """
    Final confirmation step for registration.
    Sends a success email and finalizes the registration process.
    """
    def post(self, request):
        try:
            email = request.data.get("email")
            if not email:
                return Response(
                    {"error": "Email is required for confirmation."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate user existence
            user = AccountCreation.objects.filter(email=email).first()
            if not user:
                return Response(
                    {"error": "User not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verify completion of all steps
            if not self._validate_steps_completion(user):
                return Response(
                    {"error": "All previous steps must be completed before confirmation."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Finalize registration
            RegistrationStep.objects.update_or_create(
                user=user,
                defaults={
                    "current_step": 8,
                    "last_visited": now(),
                    "progress_notes": "Registration successfully completed."
                },
            )

            # Send success email
            self._send_success_email(user)

            return Response(
                {"message": "Registration completed successfully!"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error in ConfirmationView: {e}")
            return Response(
                {"error": "An unexpected error occurred during confirmation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _validate_steps_completion(self, user):
        """
        Validates if all steps (1 to 7) are completed for the user.
        """
        registration_step = RegistrationStep.objects.filter(user=user).first()
        return registration_step and registration_step.current_step >= 7

    def _send_success_email(self, user):
        """
        Sends a success email after registration completion.
        """
        try:
            logger.info(f"Sending confirmation email to {user.email}")
            send_mail(
                subject="Registration Completed Successfully!",
                message=(
                    f"Hi {user.first_name} {user.last_name},\n\n"
                    "Your registration has been successfully completed.\n"
                    "You can now log in and start your journey.\n\n"
                    "Thank you for registering!"
                ),
                from_email="no-reply@yourplatform.com",
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Success email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send success email: {e}")
            raise ValueError("Failed to send confirmation email.")


# Final Submission View
class FinalSubmissionView(APIView):
    permission_classes = [AllowAny]
    """
    Handles final submission and marks the registration as completed.
    """
    def post(self, request):
        try:
            email = request.data.get("email")
            if not email:
                return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

            user = AccountCreation.objects.filter(email=email).first()
            if not user:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            # Check all registration steps are completed
            registration_step = RegistrationStep.objects.filter(user=user).first()
            if not registration_step or registration_step.current_step < 8:
                return Response(
                    {"error": "Complete all registration steps first."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify payment completion
            payment = Payment.objects.filter(user=user, payment_status=True).first()
            if not payment:
                return Response({"error": "Payment not completed."}, status=status.HTTP_400_BAD_REQUEST)

            # Mark registration as completed
            RegistrationStatus.objects.update_or_create(
                user=user,
                defaults={"is_completed": True, "last_updated": now()}
            )

            # Send completion email
            send_mail(
                subject="Registration Completed",
                message=(
                    f"Dear {user.first_name},\n\n"
                    "Your registration is now complete.\n\n"
                    "Thank you for choosing us!"
                ),
                from_email="no-reply@yourplatform.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response(
                {"message": "Registration completed successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in FinalSubmissionView: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Email Verification
def verify_email(request):
    """
    Verifies user email through a tokenized link.
    """
    if request.method == "GET":
        try:
            uidb64 = request.GET.get("uid")
            token = request.GET.get("token")

            if not uidb64 or not token:
                return JsonResponse({"error": "Invalid parameters."}, status=400)

            uid = force_str(urlsafe_base64_decode(uidb64))
            user = AccountCreation.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.email_verified = True
                user.date_joined = now()
                user.save()
                return JsonResponse({"message": "Email verified successfully."}, status=200)

            return JsonResponse({"error": "Invalid or expired token."}, status=400)

        except AccountCreation.DoesNotExist:
            return JsonResponse({"error": "User does not exist."}, status=404)
        except Exception as e:
            logger.error(f"Error in verify_email: {e}")
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)

    return JsonResponse({"error": "Invalid method."}, status=405)

# Registration Progress
class GetRegistrationProgressView(APIView):
    permission_classes = [AllowAny]
    """
    Retrieve the user's registration progress.
    Returns the current step and a summary of the progress.
    """

    def get(self, request):
        try:
            email = request.GET.get("email")

            # Validate email input
            if not email:
                return Response(
                    {"error": "Email is required to check registration progress."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the user exists
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                return Response(
                    {"error": "User not found. Complete account creation first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch registration progress
            registration_step = RegistrationStep.objects.filter(user=user).first()
            if not registration_step:
                return Response(
                    {
                        "message": "Registration has not started.",
                        "current_step": 0,
                        "progress_notes": "No progress yet.",
                    },
                    status=status.HTTP_200_OK,
                )

            # Prepare response with current step and progress notes
            progress_data = {
                "email": user.email,
                "current_step": registration_step.current_step,
                "last_visited": registration_step.last_visited.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if registration_step.last_visited
                else None,
                "progress_notes": registration_step.progress_notes
                or "In progress...",
            }

            return Response(
                {
                    "message": "Registration progress fetched successfully.",
                    "registration_progress": progress_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error fetching registration progress: {e}")
            return Response(
                {"error": "An unexpected error occurred while fetching progress."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# Registration Status 
class GetRegistrationStatusView(APIView):
    permission_classes = [AllowAny]
    """
    Retrieve the user's registration status.
    Returns the status (completed or not) and relevant progress information.
    """

    def get(self, request):
        try:
            email = request.GET.get("email")

            # Validate email input
            if not email:
                return Response(
                    {"error": "Email is required to check registration status."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the user exists
            try:
                user = AccountCreation.objects.get(email=email)
            except AccountCreation.DoesNotExist:
                return Response(
                    {"error": "User not found. Complete account creation first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch registration completion status
            registration_status = RegistrationStatus.objects.filter(user=user).first()
            if not registration_status:
                return Response(
                    {
                        "message": "Registration status is not available yet.",
                        "is_completed": False,
                        "last_updated": None,
                    },
                    status=status.HTTP_200_OK,
                )

            # Prepare response with registration status
            status_data = {
                "email": user.email,
                "is_completed": registration_status.is_completed,
                "last_updated": registration_status.last_updated.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if registration_status.last_updated
                else None,
            }

            return Response(
                {
                    "message": "Registration status fetched successfully.",
                    "registration_status": status_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error fetching registration status: {e}")
            return Response(
                {"error": "An unexpected error occurred while fetching status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class UpdateProgressNotesView(APIView):
    permission_classes = [AllowAny]
    """
    Update the progress notes for a user's registration.
    """
    def post(self, request, user_id):
        try:
            progress_notes = request.data.get("progress_notes", "").strip()

            if not progress_notes:
                return Response(
                    {"error": "Progress notes cannot be empty."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate if the user exists
            user = AccountCreation.objects.get(pk=user_id)

            # Update or create registration step
            RegistrationStep.objects.update_or_create(
                user=user,
                defaults={"progress_notes": progress_notes, "last_visited": now()}
            )

            return Response(
                {"message": "Progress notes updated successfully."},
                status=status.HTTP_200_OK
            )
        except AccountCreation.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in UpdateProgressNotesView: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )