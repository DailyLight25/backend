from django.utils import timezone
from django.contrib.sessions.models import Session
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from posts.models import Post
from prayer_requests.models import PrayerInteraction, PrayerRequest
from comments.models import Comment


class CommunityStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        active_believers = User.objects.filter(is_active=True).count()
        partner_ministries = User.objects.filter(is_active=True, premium_status=True).count()
        prayers_shared = PrayerInteraction.objects.filter(
            interaction_type=PrayerInteraction.InteractionType.PRAYED
        ).count()
        community_care = Comment.objects.count()
        stories_shared = Post.objects.filter(status="published").count()

        metrics = [
            {
                "key": "active_believers",
                "label": "Active believers",
                "value": active_believers,
            },
            {
                "key": "partner_ministries",
                "label": "Partner ministries",
                "value": partner_ministries,
            },
            {
                "key": "prayers_shared",
                "label": "Prayers shared",
                "value": prayers_shared,
            },
            {
                "key": "community_care",
                "label": "Community care",
                "value": community_care + stories_shared,
            },
        ]

        return Response(
            {
                "metrics": metrics,
                "online_users": self.get_online_user_count(),
                "generated_at": timezone.now(),
            }
        )

    @staticmethod
    def get_online_user_count():
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_ids = set()

        for session in active_sessions.iterator():
            data = session.get_decoded()
            user_id = data.get("_auth_user_id")
            if user_id:
                user_ids.add(user_id)

        if not user_ids:
            return 0

        return User.objects.filter(id__in=user_ids, is_active=True).count()
