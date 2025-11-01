from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Follow

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


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    raw_id_fields = ('follower', 'following')
    list_filter = ('created_at',)