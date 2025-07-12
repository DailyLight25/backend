from django.contrib import admin
from .models import PrayerRequest

@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'is_anonymous', 'prayer_count', 'created_at')
    list_filter = ('is_anonymous', 'created_at')
    search_fields = ('content', 'author__username')
    raw_id_fields = ('author', 'post')
    readonly_fields = ('prayer_count', 'ai_moderation_feedback', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('content', 'post', 'author', 'is_anonymous')
        }),
        ('Engagement & Moderation', {
            'fields': ('prayer_count', 'ai_moderation_feedback')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )