# Core Django imports
from django.conf import settings  # Access project settings
from django.db import models  # Django ORM models
from django.utils.timezone import now  # Current timezone-aware datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin  # For custom user models
from django.utils.translation import gettext_lazy as _  # Translation and internationalization

# Validators and utilities
from django.core.validators import RegexValidator  # Validate input formats (e.g., phone numbers, email)
from django.core.mail import send_mail  # For sending emails
from django.utils.http import urlsafe_base64_encode  # Encode data for email verification
from django.utils.encoding import force_bytes  # Encoding helper for token generation
from django.contrib.auth.tokens import default_token_generator  # Default token generator for email/password tokens
from django.db.models import JSONField  # For storing JSON data (Django >= 3.1)

# Python standard library
from datetime import date  # For date comparisons (e.g., age calculations)

# Custom Manager for Account Creation
class AccountCreationManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not password:
            raise ValueError("The Password field must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("email_verified", False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# Account Creation Model
class AccountCreation(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=50, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=50, verbose_name=_("Last Name"))
    password_reset_token = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Password Reset Token"))
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Is Staff"))
    date_joined = models.DateTimeField(default=now, editable=False, verbose_name=_("Date Joined"))
    email_verified = models.BooleanField(default=False, verbose_name=_("Email Verified"))
    verification_token = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Verification Token"))

    objects = AccountCreationManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")

    def __str__(self):
        return self.email

    def send_verification_email(self):
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        verification_link = f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"

        send_mail(
            subject="Verify Your Email Address",
            message=(
                f"Hi {self.first_name},\n\n"
                f"Please verify your email by clicking the link below:\n{verification_link}\n\n"
                "Thank you for signing up!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )

        self.verification_token = token
        self.save()

    def set_password_reset_token(self):
        from django.contrib.auth.tokens import default_token_generator
        self.password_reset_token = default_token_generator.make_token(self)
        self.save()


# Country Model
class Country(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100, unique=True)
    phone_code = models.CharField(max_length=20, blank=True, null=True)
    flag_url = models.URLField(blank=True, null=True)
    population = models.BigIntegerField(default=0)
    region = models.CharField(max_length=100, blank=True, null=True)
    subregion = models.CharField(max_length=100, blank=True, null=True)
    currency_name = models.CharField(max_length=50, blank=True, null=True)
    currency_code = models.CharField(max_length=3, blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# City Model
class City(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    is_capital = models.BooleanField(default=False)

    class Meta:
        unique_together = ("name", "country")
        verbose_name = "City"
        verbose_name_plural = "Cities"

    def __str__(self):
        return f"{self.name}, {self.country.name}"


# Personal Information Model
class PersonalInformation(models.Model):
    user = models.OneToOneField(
        AccountCreation, on_delete=models.CASCADE, related_name="personal_info"
    )
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    nationality = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Personal Information"

    def is_adult(self):
        if not self.date_of_birth:
            return False
        today = date.today()
        age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        return age >= 18


# Address Details Model
class AddressDetails(models.Model):
    user = models.OneToOneField(
        AccountCreation, on_delete=models.CASCADE, related_name="address_details"
    )
    street_address = models.CharField(max_length=255)
    apartment_suite = models.CharField(max_length=50, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name="addresses")
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, related_name="addresses")
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=12)
    phone_number = models.CharField(max_length=15)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Address Detail"
        verbose_name_plural = "Address Details"
        indexes = [
            models.Index(fields=["city", "country"]),
            models.Index(fields=["postal_code"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.street_address}"

# Educational Background
class EducationalBackground(models.Model):
    DEGREE_CHOICES = [
        ('High School', 'High School'),
        ('Bachelor\'s', 'Bachelor\'s'),
        ('Master\'s', 'Master\'s'),
        ('Ph.D.', 'Ph.D.'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(
        'AccountCreation', 
        on_delete=models.CASCADE, 
        related_name="educational_background"
    )
    degree = models.CharField(max_length=50, choices=DEGREE_CHOICES)
    institution = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.IntegerField()
    certifications_honors = models.TextField(blank=True, null=True)  # Optional field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Educational Background"
        verbose_name_plural = "Educational Backgrounds"

    def __str__(self):
        return f"{self.user.email} - {self.degree}"


# Course Model
class Course(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)  # Supports large fees
    duration = models.CharField(max_length=50)  # e.g., '3 Months', '1 Year'
    discount_percentage = models.PositiveIntegerField(default=0, help_text="Discount percentage, e.g., 10 for 10%")  # Optional discount
    is_active = models.BooleanField(default=True)  # Active course status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def discounted_fee(self):
        """Calculate the fee after applying the discount."""
        if self.discount_percentage > 0:
            return self.fee - (self.fee * self.discount_percentage / 100)
        return self.fee


# Course Selection
class CourseSelection(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
    ]

    user = models.ForeignKey(AccountCreation, on_delete=models.CASCADE, related_name="course_selections")
    courses = models.ManyToManyField(Course, related_name="selected_courses")
    study_duration = models.PositiveIntegerField(default=0, help_text="Duration in months")
    total_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course Selection"
        verbose_name_plural = "Course Selections"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - Course Selection"

    def calculate_total_fee(self):
        """Calculate total fee based on selected courses and apply any discounts."""
        total = sum(course.discounted_fee for course in self.courses.all())
        return total

    def save(self, *args, **kwargs):
        """Override save method to automatically calculate total fee."""
        self.total_fee = self.calculate_total_fee()
        super(CourseSelection, self).save(*args, **kwargs)


# Payment Model
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("Credit Card", "Credit Card"),
        ("PayPal", "PayPal"),
        ("Google Pay", "Google Pay"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]

    user = models.ForeignKey(
        AccountCreation, on_delete=models.CASCADE, related_name="payments"
    )
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHOD_CHOICES, verbose_name="Payment Method"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Payment Amount"
    )
    transaction_id = models.CharField(
        max_length=255, blank=True, null=True, unique=True, verbose_name="Transaction ID"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending",
        verbose_name="Payment Status",
    )
    billing_address = models.TextField(
        blank=True, null=True, verbose_name="Billing Address"
    )
    payment_date = models.DateTimeField(default=now, verbose_name="Payment Date")
    payment_gateway_response = models.JSONField(
        blank=True, null=True, verbose_name="Payment Gateway Response"
    )

    def __str__(self):
        return f"{self.user.email} - {self.payment_method} - {self.payment_status}"

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-payment_date"]


# Registration Status
class RegistrationStatus(models.Model):
    user = models.OneToOneField(
        AccountCreation,
        on_delete=models.CASCADE,
        related_name="registration_status",
        verbose_name="User"
    )
    is_completed = models.BooleanField(
        default=False, verbose_name="Registration Completed"
    )
    progress_notes = models.TextField(
        blank=True, null=True, verbose_name="Progress Notes"
    )
    last_updated = models.DateTimeField(
        auto_now=True, verbose_name="Last Updated"
    )
    completion_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Completion Date"
    )

    def save(self, *args, **kwargs):
        # Automatically set completion_date if registration is completed
        if self.is_completed and not self.completion_date:
            self.completion_date = now()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user.email} - {status}"

    class Meta:
        verbose_name = "Registration Status"
        verbose_name_plural = "Registration Statuses"
        ordering = ["-last_updated"]


# Registration Step
class RegistrationStep(models.Model):
    user = models.OneToOneField(
        AccountCreation,
        on_delete=models.CASCADE,
        related_name="registration_step",
        verbose_name="User"
    )
    current_step = models.IntegerField(
        default=1, verbose_name="Current Registration Step"
    )
    last_visited = models.DateTimeField(
        default=now, verbose_name="Last Visited"
    )
    progress_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0, verbose_name="Progress Percentage"
    )

    def save(self, *args, **kwargs):
        # Auto-update progress percentage based on current_step (assuming 8 steps)
        self.progress_percentage = round((self.current_step / 8) * 100, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - Step {self.current_step} ({self.progress_percentage}%)"

    class Meta:
        verbose_name = "Registration Step"
        verbose_name_plural = "Registration Steps"
        ordering = ["user__email"]