from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': (
                'role',
                'phone',
                'telegram_id',
            )
        }),
    )

    list_display = (
        'username',
        'email',
        'role',
        'phone',
        'is_staff',
    )

    list_filter = (
        'role',
        'is_staff',
        'is_superuser',
    )