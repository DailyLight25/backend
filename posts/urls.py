from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import PostViewSet, ReactionViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet)
router.register(r'reactions', ReactionViewSet) # If you want a separate endpoint for managing reactions directly

urlpatterns = [
    path('', include(router.urls)),
]