# notifications/models.py
from django.db import models
from django.conf import settings
# If using GenericForeignKeys for linking to Posts/Prayers later:
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True) # Who triggered it
    verb = models.CharField(max_length=255) # e.g., "liked your post"
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Generic relation to target object (Post, Comment, etc.) - Optional for MVP but recommended
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    # object_id = models.PositiveIntegerField(null=True)
    # content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor} {self.verb} {self.recipient}"