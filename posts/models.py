from django.db import models
# Change the import:
from django.db.models import JSONField # <--- CHANGE THIS LINE!
from users.models import User # Import the custom User model
from .ai_moderate import ai_moderate_content


class EngagementQuerySet(models.QuerySet):
    def with_reaction_counts(self):
        return self.annotate(reaction_total=models.Count("reactions"))

class Post(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Moderation'),
        ('published', 'Published'),
        ('flagged', 'Flagged by AI'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    tags = JSONField(default=list, blank=True, null=True) # e.g., ["faith", "prayer"]
    scripture_refs = JSONField(default=list, blank=True, null=True) # e.g., ["John 3:16", "Romans 8:28"]
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_moderation_feedback = JSONField(default=dict, blank=True, null=True) # e.g., {"status": "flagged", "reason": "Potential hate speech"}

    objects = EngagementQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if self.status == "pending":
            result = ai_moderate_content(self.content)
            self.status = "flagged" if result["flagged"] else "published"
            self.ai_moderation_feedback = result
        super().save(*args, **kwargs)
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Reaction(models.Model):
    REACTION_CHOICES = [
        ("like", "👍"),
        ("love", "❤️"),
        ("laugh", "😂"),
        ("sad", "😢"),
        ("fire", "🔥"),
        ("heart", "❤️"),
        ("pray", "🙏"),
        ("amen", "✝️"),
    ]

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reactions"
    )
    type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["post", "user", "type"]  # Prevent duplicate same reaction

    def __str__(self):
        return f"{self.user} reacted {self.get_type_display()} on {self.post.title}"


class PostShare(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="shares"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_shares"
    )
    platform = models.CharField(
        max_length=50, blank=True, help_text="Optional platform or channel identifier."
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["post", "user", "platform"]

    def __str__(self):
        platform = self.platform or "direct share"
        return f"{self.user} shared {self.post.title} via {platform}"
