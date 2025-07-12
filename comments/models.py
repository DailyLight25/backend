from django.db import models
from users.models import User
from posts.models import Post
from django.db.models import JSONField


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    reactions = JSONField(default=dict, blank=True, null=True) # e.g., {"heart": 5, "pray": 2}
    ai_moderation_feedback = JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title[:30]}..."
