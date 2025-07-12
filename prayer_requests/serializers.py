from rest_framework import serializers
from .models import PrayerRequest
from users.serializers import UserProfileSerializer # Optional for displaying author info

class PrayerRequestSerializer(serializers.ModelSerializer):
    # Only show author if not anonymous
    author_info = serializers.SerializerMethodField()

    class Meta:
        model = PrayerRequest
        fields = ['id', 'post', 'content', 'prayer_count', 'ai_moderation_feedback',
                  'is_anonymous', 'created_at', 'updated_at', 'author_info']
        read_only_fields = ['prayer_count', 'ai_moderation_feedback', 'created_at', 'updated_at', 'author_info']

    def get_author_info(self, obj):
        if obj.is_anonymous or not obj.author:
            return None
        return UserProfileSerializer(obj.author).data

    def create(self, validated_data):
        request = self.context.get('request')
        is_anonymous = validated_data.get('is_anonymous', False)

        if is_anonymous:
            # If anonymous, set author to None or a specific 'anonymous' user if you have one
            validated_data['author'] = None
        else:
            # If not anonymous, set author to the current authenticated user
            validated_data['author'] = request.user if request and request.user.is_authenticated else None
            if not validated_data['author']:
                 raise serializers.ValidationError({"author": "Authentication required for non-anonymous prayer requests."})

        prayer_request = PrayerRequest.objects.create(**validated_data)
        # TODO: Trigger AI moderation for prayer requests
        prayer_request.ai_moderation_feedback = {"status": "pending", "reason": "Awaiting moderation"}
        prayer_request.save()
        return prayer_request