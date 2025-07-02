from django.db import models
from posts.models import Post
from django.contrib.postgres.fields import JSONField # For AI moderation feedback

class File(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_type = models.CharField(max_length=50, help_text="e.g., 'image/jpeg', 'application/pdf'")
    size = models.PositiveIntegerField(help_text="File size in bytes")
    # Store AI moderation results for the file content
    ai_moderation = JSONField(default=dict, blank=True, null=True, help_text="AI moderation feedback for the file.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} ({self.size} bytes)"

    # Method to check if file size is within limits (5MB)
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.file.size > 5 * 1024 * 1024:  # 5 MB
            raise ValidationError("File size cannot exceed 5MB.")