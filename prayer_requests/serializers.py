from typing import Any, Dict, Optional

from rest_framework import serializers

from users.serializers import UserProfileSerializer  # Optional for displaying author info

from .models import PrayerInteraction, PrayerRequest


class PrayerEncouragementSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = PrayerInteraction
        fields = ["id", "message", "created_at", "user"]
        read_only_fields = ["id", "created_at", "user"]

    def get_user(self, obj: PrayerInteraction) -> Optional[Dict[str, Any]]:
        if not obj.user_id:
            return None
        avatar = None
        profile_picture = getattr(obj.user, "profile_picture", None)
        if profile_picture and hasattr(profile_picture, "url"):
            try:
                avatar = profile_picture.url
            except Exception:
                avatar = None
        return {
            "id": obj.user_id,
            "username": obj.user.username,
            "display_name": getattr(obj.user, "get_full_name", lambda: "")() or obj.user.username,
            "avatar": avatar,
        }


class PrayerRequestSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()
    prayer_count = serializers.SerializerMethodField()
    encouragement_count = serializers.SerializerMethodField()
    is_prayed_by_current_user = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    recent_encouragements = serializers.SerializerMethodField()

    class Meta:
        model = PrayerRequest
        fields = [
            "id",
            "short_description",
            "category",
            "visibility",
            "status",
            "answered_note",
            "answered_scripture",
            "answered_at",
            "created_at",
            "updated_at",
            "user_profile",
            "prayer_count",
            "encouragement_count",
            "is_prayed_by_current_user",
            "is_owner",
            "recent_encouragements",
        ]
        read_only_fields = [
            "id",
            "answered_at",
            "created_at",
            "updated_at",
            "user_profile",
            "prayer_count",
            "encouragement_count",
            "is_prayed_by_current_user",
            "is_owner",
            "recent_encouragements",
        ]

    def get_user_profile(self, obj: PrayerRequest) -> Optional[Dict[str, Any]]:
        if obj.visibility == PrayerRequest.Visibility.ANONYMOUS or not obj.user:
            return None
        return UserProfileSerializer(obj.user).data

    def get_prayer_count(self, obj: PrayerRequest) -> int:
        annotated_value = getattr(obj, "prayer_count", None)
        if annotated_value is not None:
            return int(annotated_value)
        return obj.interactions.filter(
            interaction_type=PrayerInteraction.InteractionType.PRAYED
        ).count()

    def get_encouragement_count(self, obj: PrayerRequest) -> int:
        annotated_value = getattr(obj, "encouragement_count", None)
        if annotated_value is not None:
            return int(annotated_value)
        return obj.interactions.filter(
            interaction_type=PrayerInteraction.InteractionType.ENCOURAGE
        ).count()

    def get_is_prayed_by_current_user(self, obj: PrayerRequest) -> bool:
        annotated_value = getattr(obj, "has_prayed", None)
        if annotated_value is not None:
            return bool(annotated_value)
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.interactions.filter(
            user=request.user,
            interaction_type=PrayerInteraction.InteractionType.PRAYED,
        ).exists()

    def get_is_owner(self, obj: PrayerRequest) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user_id == request.user.id

    def get_recent_encouragements(self, obj: PrayerRequest):
        encouragements = getattr(obj, "_recent_encouragements", None)
        if encouragements is None:
            encouragements = list(
                obj.interactions.filter(
                    interaction_type=PrayerInteraction.InteractionType.ENCOURAGE
                )[:5]
            )
        serializer = PrayerEncouragementSerializer(encouragements, many=True)
        return serializer.data

    def validate_short_description(self, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise serializers.ValidationError("Prayer request cannot be empty.")
        if len(normalized) > 200:
            raise serializers.ValidationError("Prayer request must be 200 characters or fewer.")
        return normalized

    def validate_answered_note(self, value: str) -> str:
        if value and len(value.strip()) > 200:
            raise serializers.ValidationError("Thank-you note must be 200 characters or fewer.")
        return value.strip() if value else ""

    def validate_answered_scripture(self, value: str) -> str:
        if value and len(value.strip()) > 120:
            raise serializers.ValidationError("Scripture reference must be 120 characters or fewer.")
        return value.strip() if value else ""

    def create(self, validated_data: Dict[str, Any]) -> PrayerRequest:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Authentication required to submit a prayer request."}
            )

        validated_data["user"] = request.user
        return PrayerRequest.objects.create(**validated_data)

    def update(self, instance: PrayerRequest, validated_data: Dict[str, Any]) -> PrayerRequest:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance