from django.db import models
from django.contrib.postgres.fields import JSONField # For PostgreSQL JSONB field
from users.models import User # Import the custom User model

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Moderation'),
        ('published', 'Published'),
        ('flagged', 'Flagged by AI'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = JSONField(default=list, blank=True, null=True) # e.g., ["faith", "prayer"]
    scripture_refs = JSONField(default=list, blank=True, null=True) # e.g., ["John 3:16", "Romans 8:28"]
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_moderation_feedback = JSONField(default=dict, blank=True, null=True) # e.g., {"status": "flagged", "reason": "Potential hate speech"}

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Reaction(models.Model):
    REACTION_CHOICES = [
        ('heart', 'Heart'),
        ('pray', 'Pray'),
        # Add more reactions as needed
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user', 'type'] # A user can only add one of each reaction type to a post