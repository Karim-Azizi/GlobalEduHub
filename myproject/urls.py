from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import TemplateView, RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

# Custom Error Views
from myproject.views.error_views import custom_404_view, custom_500_view

# Student Registration Views
from myproject.views.student_views import (
    AccountCreationView, check_email_availability,
    PersonalInformationView, AddressDetailsView,
    EducationalBackgroundView, CourseSelectionView,
    ReviewSummaryView, ConfirmationView, FinalSubmissionView,
    GetCoursesView, GetRegistrationProgressView,
    GetRegistrationStatusView, UpdateProgressNotesView,
)

# Admin Views
from myproject.views.admin_views import (
    admin_stats, user_growth, revenue_data, admin_notifications,
    admin_users, login_user, manage_courses,
    deactivate_course, activate_course,
)

# Payment and Utility Views
from myproject.views.payment_views import ProcessPaymentView
from myproject.views.utility_views import (
    get_countries, get_cities, get_phone_code,
)

# URL Patterns
urlpatterns = [
    # Admin URLs
    path('django-admin/', admin.site.urls),
    path('admin/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('admin/logout/', LogoutView.as_view(next_page='/login/'), name='logout'),

    # Admin Endpoints
    path('api/admin/stats/', admin_stats, name='admin_stats'),
    path('api/admin/user-growth/', user_growth, name='user_growth'),
    path('api/admin/revenue/', revenue_data, name='revenue_data'),
    path('api/admin/notifications/', admin_notifications, name='admin_notifications'),
    path('api/admin/users/', admin_users, name='admin_users'),
    path('api/admin/courses/', manage_courses, name='manage_courses'),
    path('api/admin/courses/<int:course_id>/deactivate/', deactivate_course, name='deactivate_course'),
    path('api/admin/courses/<int:course_id>/activate/', activate_course, name='activate_course'),

    # Authentication
    path('api/login/', login_user, name='login_user'),

    # Student Registration Workflow
    path('api/register/student/account-creation/', AccountCreationView.as_view(), name='student_account_creation'),
    path('api/register/student/personal-information/', PersonalInformationView.as_view(), name='student_personal_information'),
    path('api/register/student/address-details/', AddressDetailsView.as_view(), name='student_address_details'),
    path('api/register/student/education-background/', EducationalBackgroundView.as_view(), name='student_education_background'),
    path('api/register/student/course-selection/', CourseSelectionView.as_view(), name='student_course_selection'),
    path('api/register/student/review-summary/', ReviewSummaryView.as_view(), name='student_review_summary'),
    path('api/register/student/confirmation/', ConfirmationView.as_view(), name='student_confirmation'),
    path('api/register/student/final-submit/', FinalSubmissionView.as_view(), name='final_submission'),

    # Courses
    path('api/courses/', GetCoursesView.as_view(), name='get_courses'),

    # Registration Progress
    path('api/user/registration-progress/', GetRegistrationProgressView.as_view(), name='get_registration_progress'),
    path('api/user/registration-status/', GetRegistrationStatusView.as_view(), name='get_registration_status'),
    path('api/user/<int:user_id>/update-progress-notes/', UpdateProgressNotesView.as_view(), name='update_progress_notes'),

    # Payments
    path('api/register/student/payment/', ProcessPaymentView.as_view(), name='student_payment'),

    # Utilities
    path('api/countries/', get_countries, name='get_countries'),
    path('api/countries/<int:country_id>/cities/', get_cities, name='get_cities'),
    path('api/countries/<int:country_id>/phone-code/', get_phone_code, name='get_phone_code'),

    # Email Check
    path('api/check-email/', check_email_availability, name='check_email'),

    # React Frontend Routes
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    re_path(r'^(?!django-admin/).*$', TemplateView.as_view(template_name='index.html'), name='react_spa'),
]

# Static and Media during Development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom Error Handlers
handler404 = 'myproject.views.error_views.custom_404_view'
handler500 = 'myproject.views.error_views.custom_500_view'

# Key Enhancements:
# 1. **Error Handlers**:
#    - Added `handler404` and `handler500` for custom error views.
#    - Ensure the `custom_404_view` and `custom_500_view` are defined in `myproject.views.error_views`.

# 2. **React Routes**:
#    - Included `re_path` to dynamically handle React frontend routes.

# 3. **Improved Grouping**:
#    - Grouped admin, registration, and payment routes for better readability and organization.

# 4. **Static and Media Files**:
#    - Ensure static and media files are served correctly during development.

# Ensure `error_views.py` contains the proper logic for the error handling views.