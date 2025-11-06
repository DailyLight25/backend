from django.contrib import admin

from .models import PrayerInteraction, PrayerNotification, PrayerRequest


@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = (
        "short_description",
        "user",
        "visibility",
        "status",
        "created_at",
    )
    list_filter = ("visibility", "status", "created_at")
    search_fields = ("short_description", "user__username")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "answered_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "short_description",
                    "category",
                    "visibility",
                    "status",
                )
            },
        ),
        (
            "Answered",
            {
                "fields": ("answered_note", "answered_scripture", "answered_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(PrayerInteraction)
class PrayerInteractionAdmin(admin.ModelAdmin):
    list_display = ("prayer_request", "user", "interaction_type", "created_at")
    list_filter = ("interaction_type", "created_at")
    search_fields = ("prayer_request__short_description", "user__username")
    raw_id_fields = ("prayer_request", "user")


@admin.register(PrayerNotification)
class PrayerNotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "prayer_request", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("recipient__username", "prayer_request__short_description")
    raw_id_fields = ("recipient", "actor", "prayer_request")