from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Define the list_display to specify which fields to display in the admin list view
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "country",
        "is_verified",
    )

    # Specify the fields that you want to be searchable
    search_fields = ("email", "first_name", "last_name")

    # Specify the ordering of the items in the list view (optional)
    ordering = ("email",)

    # Specify custom fieldsets for detailed view. You can add 'birthday' and other fields if needed
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                    "username",
                    "country",
                    "is_verified",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    # Custom add_fieldsets if you want to customize the admin creation form
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "username",
                    "country",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not form.cleaned_data.get("username"):
            obj.username = obj.email
        super().save_model(request, obj, form, change)

