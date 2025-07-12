from django.db import models
from users.models import User
from posts.models import Post # Optional link to a specific post
from django.db.models import JSONField

class PrayerRequest(models.Model):
    # If anonymous, author will be null or point to a default anonymous user
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='prayer_requests')
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_prayer_requests')
    content = models.TextField()
    prayer_count = models.PositiveIntegerField(default=0)
    ai_moderation_feedback = JSONField(default=dict, blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] # Show newest first

    def __str__(self):
        return f"Prayer Request by {self.author.username if self.author and not self.is_anonymous else 'Anonymous'}: {self.content[:50]}..."