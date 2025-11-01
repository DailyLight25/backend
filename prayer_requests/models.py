import uuid

from django.db import models
from django.db.models import JSONField

from users.models import User


class PrayerRequest(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        FRIENDS = "friends", "Friends"
        ANONYMOUS = "anonymous", "Anonymous"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ANSWERED = "answered", "Answered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prayer_requests",
    )
    short_description = models.CharField(max_length=200, default="")
    category = models.CharField(max_length=50, blank=True, default="")
    visibility = models.CharField(
        max_length=12,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    answered_note = models.CharField(max_length=200, blank=True, default="")
    answered_scripture = models.CharField(max_length=120, blank=True, default="")
    answered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        display_name = (
            self.user.username
            if self.user and self.visibility != self.Visibility.ANONYMOUS
            else "Anonymous"
        )
        return f"Prayer Request by {display_name}: {self.short_description[:50]}..."


class PrayerInteraction(models.Model):
    class InteractionType(models.TextChoices):
        PRAYED = "prayed", "Prayed"
        ENCOURAGE = "encourage", "Encourage"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prayer_request = models.ForeignKey(
        PrayerRequest,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prayer_interactions",
    )
    interaction_type = models.CharField(
        max_length=12,
        choices=InteractionType.choices,
        default=InteractionType.PRAYED,
    )
    message = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["prayer_request", "user", "interaction_type"],
                condition=models.Q(interaction_type="prayed"),
                name="unique_prayer_per_user",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} {self.interaction_type} {self.prayer_request_id}"


class PrayerNotification(models.Model):
    class NotificationType(models.TextChoices):
        PRAYED = "prayed", "Prayed"
        ANSWERED = "answered", "Answered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prayer_notifications",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_prayer_notifications",
    )
    prayer_request = models.ForeignKey(
        PrayerRequest,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
    )
    payload = JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification to {self.recipient} about {self.prayer_request_id}"