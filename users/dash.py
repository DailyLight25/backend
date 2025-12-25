from rest_framework import serializers
from posts.serializers import PostSerializer
from notifications.serializers import NotificationSerializer

class DashboardSerializer(serializers.Serializer):
    """
    This serializer aggregates data from multiple models to power the User Dashboard.
    It expects a dictionary of data, not a single model instance.
    """
    
    # --- 1. Profile Identity ---
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField(source='get_full_name', allow_blank=True)
    avatar = serializers.ImageField(allow_null=True) 
    is_verified = serializers.BooleanField(default=False)
    current_streak = serializers.IntegerField(default=0)
    
    # --- 2. Engagement Stats ---
    followers_count = serializers.IntegerField(default=0)
    following_count = serializers.IntegerField(default=0)
    unread_notifications_count = serializers.IntegerField(default=0)
    
    # --- 3. Content Feeds ---
    # We reuse existing serializers here to ensure the data looks exactly like it does in other API calls.
    recent_activity = PostSerializer(many=True)
    notifications_preview = NotificationSerializer(many=True)
    recommended_content = PostSerializer(many=True)
    
