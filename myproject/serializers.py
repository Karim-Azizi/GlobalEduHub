from rest_framework import serializers
from .models import (
    AccountCreation,
    Course,
    PersonalInformation,
    AddressDetails,
    EducationalBackground,
    CourseSelection,
    Payment,
    RegistrationStatus,
    RegistrationStep,
    Country,
    City,
)


# Account Creation Serializer
class AccountCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountCreation
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'is_active', 'date_joined']


# Step 1: Personal Information Serializer
class PersonalInformationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=AccountCreation.objects.all())

    class Meta:
        model = PersonalInformation
        fields = [
            'id', 'user', 'date_of_birth', 'gender',
            'phone_number', 'profile_picture', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified']

    def validate_date_of_birth(self, value):
        """
        Validate that the user is at least 18 years old.
        """
        from datetime import date
        age = (date.today() - value).days // 365
        if age < 18:
            raise serializers.ValidationError("You must be at least 18 years old.")
        return value


# Step 2: Address Details Serializer
class AddressDetailsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=AccountCreation.objects.all())
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), allow_null=True)

    class Meta:
        model = AddressDetails
        fields = [
            'id', 'user', 'country', 'city', 'street_address',
            'state', 'postal_code', 'phone_code', 'address_type'
        ]
        read_only_fields = ['id']


# Step 3: Educational Background Serializer
class EducationalBackgroundSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=AccountCreation.objects.all())

    class Meta:
        model = EducationalBackground
        fields = [
            'id', 'user', 'degree', 'institution', 'field_of_study',
            'graduation_year', 'honors'
        ]
        read_only_fields = ['id', 'honors']

    def validate_graduation_year(self, value):
        """
        Validate that the graduation year is not in the future.
        """
        from datetime import date
        if value > date.today().year:
            raise serializers.ValidationError("Graduation year cannot be in the future.")
        return value


# Step 4: Course Selection Serializer
class CourseSelectionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=AccountCreation.objects.all())
    courses = serializers.PrimaryKeyRelatedField(many=True, queryset=Course.objects.all())

    class Meta:
        model = CourseSelection
        fields = [
            'id', 'user', 'courses', 'study_duration', 'total_fee', 'payment_status'
        ]
        read_only_fields = ['id', 'payment_status']


# Optional: Course Serializer
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'fee', 'duration', 'is_active']
        read_only_fields = ['id']


# Step 5: Payment Serializer
class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=AccountCreation.objects.all())

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'payment_method', 'transaction_id', 'amount',
            'payment_status', 'payment_date'
        ]
        read_only_fields = ['id', 'payment_date']


# Step 6: Registration Status Serializer
class RegistrationStatusSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=AccountCreation.objects.all())

    class Meta:
        model = RegistrationStatus
        fields = ['id', 'user', 'is_completed', 'progress_notes', 'last_updated']
        read_only_fields = ['id', 'last_updated', 'progress_notes']


# Step 7: Registration Step Serializer
class RegistrationStepSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=AccountCreation.objects.all())

    class Meta:
        model = RegistrationStep
        fields = ['id', 'user', 'current_step', 'last_visited', 'progress_notes']
        read_only_fields = ['id', 'last_visited']


# Unified User Registration Progress Serializer
class RegistrationProgressSerializer(serializers.Serializer):
    """
    Combines PersonalInformation, AddressDetails, EducationalBackground, CourseSelection,
    and Payment data into a single serialized response for the review step.
    """
    personal_info = PersonalInformationSerializer()
    address_details = AddressDetailsSerializer()
    educational_background = EducationalBackgroundSerializer()
    course_selection = CourseSelectionSerializer(many=True)
    payment = PaymentSerializer()

    def to_representation(self, instance):
        """
        Customizes the response to include all data in a unified structure.
        """
        data = super().to_representation(instance)
        return {
            "personal_info": data.get("personal_info"),
            "address_details": data.get("address_details"),
            "educational_background": data.get("educational_background"),
            "course_selection": data.get("course_selection"),
            "payment": data.get("payment"),
        }


# Additional Serializer for Country and City
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'phone_code']


class CitySerializer(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = City
        fields = ['id', 'name', 'country']