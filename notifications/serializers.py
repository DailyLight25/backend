# notifications/serializers.py
from rest_framework import serializers
from .models import Notification
from users.serializers import UserProfileSerializer # Optional: if you want full actor profile

class NotificationSerializer(serializers.ModelSerializer):
    # Flatten the 'actor' to just their username/avatar for the notification
    actor_name = serializers.ReadOnlyField(source='actor.username')
    actor_avatar = serializers.ImageField(source='actor.profile_picture', read_only=True)
    
    # Create a computed field for a human-readable message
    message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 
            'actor_name', 
            'actor_avatar', 
            'verb', 
            'target_id', 
            'is_read', 
            'created_at', 
            'message'
        ]

    def get_message(self, obj):
        # Example: "JohnDoe liked your post"
        return f"{obj.actor.username} {obj.verb}"