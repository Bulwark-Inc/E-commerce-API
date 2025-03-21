from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),  # Add role field in edit view
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),  # Add role field in add view
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')  # Display role in user list
    list_filter = ('role', 'is_staff', 'is_active')  # Allow filtering by role

admin.site.register(CustomUser, CustomUserAdmin)