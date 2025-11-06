from django.contrib import admin
from .models import Post, Reaction, PostShare

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'views', 'created_at', 'updated_at')
    list_filter = ('status', 'author', 'created_at')
    search_fields = ('title', 'content')
    raw_id_fields = ('author',) # For large number of users, use raw ID input
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'author', 'status')
        }),
        ('Categorization', {
            'fields': ('tags', 'scripture_refs')
        }),
        ('Moderation & Statistics', {
            'fields': ('views', 'ai_moderation_feedback')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('views', 'created_at', 'updated_at', 'ai_moderation_feedback')

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'type', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('post__title', 'user__username')
    raw_id_fields = ('post', 'user')


@admin.register(PostShare)
class PostShareAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'platform', 'created_at')
    list_filter = ('platform', 'created_at')
    search_fields = ('post__title', 'user__username', 'platform')
    raw_id_fields = ('post', 'user')