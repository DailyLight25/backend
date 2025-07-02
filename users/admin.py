from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Salt & Light Custom Fields', {'fields': ('language', 'premium_status', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Salt & Light Custom Fields', {'fields': ('language', 'premium_status')}),
    )
    list_display = ('username', 'email', 'is_staff', 'premium_status', 'language')
    list_filter = ('premium_status', 'language', 'is_staff')
    search_fields = ('username', 'email')