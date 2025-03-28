# Generated by Django 5.1.2 on 2024-12-23 16:05

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, unique=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('phone_code', models.CharField(blank=True, max_length=20, null=True)),
                ('flag_url', models.URLField(blank=True, null=True)),
                ('population', models.BigIntegerField(default=0)),
                ('region', models.CharField(blank=True, max_length=100, null=True)),
                ('subregion', models.CharField(blank=True, max_length=100, null=True)),
                ('currency_name', models.CharField(blank=True, max_length=50, null=True)),
                ('currency_code', models.CharField(blank=True, max_length=3, null=True)),
                ('timezone', models.CharField(blank=True, max_length=50, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Country',
                'verbose_name_plural': 'Countries',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField()),
                ('fee', models.DecimalField(decimal_places=2, max_digits=10)),
                ('duration', models.CharField(max_length=50)),
                ('discount_percentage', models.PositiveIntegerField(default=0, help_text='Discount percentage, e.g., 10 for 10%')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Course',
                'verbose_name_plural': 'Courses',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='AccountCreation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email Address')),
                ('first_name', models.CharField(max_length=50, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=50, verbose_name='Last Name')),
                ('password_reset_token', models.CharField(blank=True, max_length=255, null=True, verbose_name='Password Reset Token')),
                ('is_active', models.BooleanField(default=False, verbose_name='Is Active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Is Staff')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='Date Joined')),
                ('email_verified', models.BooleanField(default=False, verbose_name='Email Verified')),
                ('verification_token', models.CharField(blank=True, max_length=255, null=True, verbose_name='Verification Token')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Account',
                'verbose_name_plural': 'Accounts',
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('population', models.IntegerField(blank=True, null=True)),
                ('is_capital', models.BooleanField(default=False)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cities', to='myproject.country')),
            ],
            options={
                'verbose_name': 'City',
                'verbose_name_plural': 'Cities',
                'unique_together': {('name', 'country')},
            },
        ),
        migrations.CreateModel(
            name='CourseSelection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('study_duration', models.PositiveIntegerField(default=0, help_text='Duration in months')),
                ('total_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('payment_status', models.CharField(choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Failed', 'Failed')], default='Pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('courses', models.ManyToManyField(related_name='selected_courses', to='myproject.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_selections', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Course Selection',
                'verbose_name_plural': 'Course Selections',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='EducationalBackground',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('degree', models.CharField(choices=[('High School', 'High School'), ("Bachelor's", "Bachelor's"), ("Master's", "Master's"), ('Ph.D.', 'Ph.D.'), ('Other', 'Other')], max_length=50)),
                ('institution', models.CharField(max_length=255)),
                ('field_of_study', models.CharField(blank=True, max_length=255, null=True)),
                ('graduation_year', models.IntegerField()),
                ('certifications_honors', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='educational_background', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Educational Background',
                'verbose_name_plural': 'Educational Backgrounds',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method', models.CharField(choices=[('Credit Card', 'Credit Card'), ('PayPal', 'PayPal'), ('Google Pay', 'Google Pay')], max_length=50, verbose_name='Payment Method')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Payment Amount')),
                ('transaction_id', models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='Transaction ID')),
                ('payment_status', models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed'), ('Refunded', 'Refunded')], default='Pending', max_length=20, verbose_name='Payment Status')),
                ('billing_address', models.TextField(blank=True, null=True, verbose_name='Billing Address')),
                ('payment_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Payment Date')),
                ('payment_gateway_response', models.JSONField(blank=True, null=True, verbose_name='Payment Gateway Response')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-payment_date'],
            },
        ),
        migrations.CreateModel(
            name='PersonalInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=10)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nationality', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myproject.country')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='personal_info', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False, verbose_name='Registration Completed')),
                ('progress_notes', models.TextField(blank=True, null=True, verbose_name='Progress Notes')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='Last Updated')),
                ('completion_date', models.DateTimeField(blank=True, null=True, verbose_name='Completion Date')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='registration_status', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Registration Status',
                'verbose_name_plural': 'Registration Statuses',
                'ordering': ['-last_updated'],
            },
        ),
        migrations.CreateModel(
            name='RegistrationStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_step', models.IntegerField(default=1, verbose_name='Current Registration Step')),
                ('last_visited', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Last Visited')),
                ('progress_percentage', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, verbose_name='Progress Percentage')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='registration_step', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Registration Step',
                'verbose_name_plural': 'Registration Steps',
                'ordering': ['user__email'],
            },
        ),
        migrations.CreateModel(
            name='AddressDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_address', models.CharField(max_length=255)),
                ('apartment_suite', models.CharField(blank=True, max_length=50, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('postal_code', models.CharField(max_length=12)),
                ('phone_number', models.CharField(max_length=15)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='address_details', to=settings.AUTH_USER_MODEL)),
                ('city', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='addresses', to='myproject.city')),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='addresses', to='myproject.country')),
            ],
            options={
                'verbose_name': 'Address Detail',
                'verbose_name_plural': 'Address Details',
                'indexes': [models.Index(fields=['city', 'country'], name='myproject_a_city_id_8d338f_idx'), models.Index(fields=['postal_code'], name='myproject_a_postal__ba2291_idx')],
            },
        ),
    ]
