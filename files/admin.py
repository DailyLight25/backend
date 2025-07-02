from django.contrib import admin
from .models import File

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'file', 'file_type', 'size', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('file__icontains', 'post__title')
    raw_id_fields = ('post',)
    readonly_fields = ('size', 'file_type', 'uploaded_at', 'ai_moderation')