from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'post', 'author', 'created_at', 'updated_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'post__title', 'author__username')
    raw_id_fields = ('post', 'author')
    readonly_fields = ('reactions', 'ai_moderation_feedback', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('post', 'author', 'content')
        }),
        ('Moderation & Engagement', {
            'fields': ('reactions', 'ai_moderation_feedback')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )