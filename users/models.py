from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.utils import timezone

class User(AbstractUser):
    # Add custom fields here if needed, e.g., language preference, premium status
    is_verified = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en', help_text="User's preferred language for content.")
    premium_status = models.BooleanField(default=False, help_text="True if user has a premium subscription.")
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=False, help_text="User's profile picture.")
    temp_login_token = models.CharField(max_length=64, null=True, blank=True, help_text="Temporary token for post-verification auto-login")
    verification_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the verification link expires")
    verification_code = models.CharField(max_length=6, null=True, blank=True, help_text="6-digit verification code")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username
    
    def generate_temp_login_token(self):
        """Generate a one-time use token for auto-login after verification"""
        self.temp_login_token = get_random_string(64)
        self.save()
        return self.temp_login_token
    
    def generate_verification_code(self):
        """Generate a 6-digit verification code"""
        self.verification_code = get_random_string(length=6, allowed_chars='0123456789')
        self.save()
        return self.verification_code
    
    def set_verification_expiry(self, hours=0, minutes=0):
        """Set when the verification link expires"""
        self.verification_expires_at = timezone.now() + timedelta(hours=hours, minutes=minutes)
        self.save()
        return self.verification_expires_at
    
    def is_verification_expired(self):
        """Check if verification has expired"""
        if self.is_verified:
            return False
        if not self.verification_expires_at:
            return False
        return timezone.now() > self.verification_expires_at


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