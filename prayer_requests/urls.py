from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import PrayerRequestViewSet

router = DefaultRouter()
router.register(r'prayer_requests', PrayerRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]