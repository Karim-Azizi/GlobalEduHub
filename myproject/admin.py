from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from .models import AccountCreation, Course


class AccountCreationAdmin(UserAdmin):
    model = AccountCreation
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


# Register models in admin
admin.site.register(AccountCreation, AccountCreationAdmin)
admin.site.register(Course)
admin.site.register(Permission)

# Customize the admin interface appearance
admin.site.site_header = "Global Learning Platform Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the Admin Dashboard"