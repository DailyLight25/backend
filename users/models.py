from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Add custom fields here if needed, e.g., language preference, premium status
    is_verified = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en', help_text="User's preferred language for content.")
    premium_status = models.BooleanField(default=False, help_text="True if user has a premium subscription.")
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=False, help_text="User's profile picture.")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_relations",
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["follower", "following"]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F("following")),
                name="prevent_self_follow",
            )
        ]

    def __str__(self):
        return f"{self.follower} follows {self.following}"