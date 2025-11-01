from django.urls import path

from .views import CommunityStatsView

urlpatterns = [
    path("stats/", CommunityStatsView.as_view(), name="community-stats"),
]

