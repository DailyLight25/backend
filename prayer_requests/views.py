from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .models import PrayerRequest
from .serializers import PrayerRequestSerializer
from posts.permissions import IsAuthorOrReadOnly # Re-use permission for updating own requests
from django.db import models

class PrayerRequestViewSet(viewsets.ModelViewSet):
    queryset = PrayerRequest.objects.all()
    serializer_class = PrayerRequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow anyone to read, auth to create/update

    def get_queryset(self):
        # Allow filtering by post_id or current user (for their own requests)
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # Admins can see all, regular users only see non-anonymous or their own anonymous requests
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.filter(models.Q(is_anonymous=False) | models.Q(author=self.request.user))
        elif not self.request.user.is_authenticated:
            queryset = queryset.filter(is_anonymous=False) # Guests only see public requests

        return queryset

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only author or admin can update/delete their own prayer request
            self.permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
        elif self.action == 'create':
            # Authentication is required to create a prayer request
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'pray':
            # Anyone can increment prayer count
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()


    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def pray(self, request, pk=None):
        prayer_request = self.get_object()
        prayer_request.prayer_count += 1
        prayer_request.save()
        # Invalidate cache for this prayer request if it was cached
        cache.delete(f'prayer_request_{pk}')
        return Response({'detail': 'Prayer count incremented.', 'prayer_count': prayer_request.prayer_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        # Simple trending based on prayer_count
        trending_requests = cache.get('trending_prayer_requests')
        if not trending_requests:
            trending_requests = self.get_queryset().order_by('-prayer_count')[:10]
            serializer = self.get_serializer(trending_requests, many=True)
            trending_requests = serializer.data
            cache.set('trending_prayer_requests', trending_requests, timeout=60 * 30) # Cache for 30 min
        return Response(trending_requests)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def moderation_feedback(self, request, pk=None):
        prayer_request = self.get_object()
        return Response(prayer_request.ai_moderation_feedback)