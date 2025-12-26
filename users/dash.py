from rest_framework import serializers
from posts.serializers import PostSerializer
from notifications.serializers import NotificationSerializer
from prayer_requests.serializers import PrayerRequestSerializer

class DashboardUserSerializer(serializers.Serializer):
    """
    This serializer aggregates data from multiple models to power the User Dashboard.
    It expects a dictionary of data, not a single model instance.
    """
    # --- 1. Profile Identity ---
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField(allow_blank=True)
    avatar = serializers.ImageField(allow_null=True) 
    is_verified = serializers.BooleanField(default=False)
    current_streak = serializers.IntegerField(default=0)
    
    # --- 2. Engagement Stats ---
    followers_count = serializers.IntegerField(default=0)
    following_count = serializers.IntegerField(default=0)
    unread_notifications_count = serializers.IntegerField(default=0)
    
    # --- 3. Content Feeds ---
    # We reuse existing serializers here to ensure the data looks exactly like it does in other API calls. 
    notifications_preview = serializers.SerializerMethodField()
    recommended_content = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()

    def get_recent_activity(self, obj):
        posts = obj.get("recent_activity", [])
        return PostSerializer(posts, many=True, context=self.context).data
    
    def get_notifications_preview(self, obj):
        notifications = obj.get("notifications_preview", [])
        return NotificationSerializer(
            notifications,
            many=True,
            context=self.context
        ).data
    def get_recommended_content(self, obj):
        recommended_posts = obj.get("recommended_content", [])
        return PostSerializer(recommended_posts, many=True, context=self.context).data
class DashboardStatsSerializer(serializers.Serializer):
    totalPosts = serializers.IntegerField()
    totalPrayers = serializers.IntegerField()
    totalComments = serializers.IntegerField()
    totalViews = serializers.IntegerField()
    totalReactions = serializers.IntegerField()
    joinDate = serializers.DateTimeField()
    lastActive = serializers.DateTimeField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    user = DashboardUserSerializer()
    stats = DashboardStatsSerializer()
    posts = PostSerializer(many=True)
    prayerRequests = PrayerRequestSerializer(many=True)