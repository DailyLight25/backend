from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .models import Post, Reaction
from .serializers import PostSerializer, ReactionSerializer
from .permissions import IsAuthorOrReadOnly, IsAdminUserOrReadOnly # Custom permissions (define below)
from django.db import models # <--- ADD THIS LINE!
from django.db.models import Count


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.filter(status='published') # Only show published posts by default
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        # Allow authors/admins to see their draft/pending posts
        if self.request.user.is_authenticated:
            if self.request.user.is_staff: # Admin can see all
                return Post.objects.all()
            else: # Author can see their own drafts/pending posts
                return Post.objects.filter(models.Q(status='published') | models.Q(author=self.request.user))
        return super().get_queryset()

    def perform_create(self, serializer):
        # Set the author automatically to the current user
        serializer.save(author=self.request.user)
        # In a real scenario, this would likely trigger an async AI moderation task
        # For now, let's set it to 'pending'
        serializer.instance.status = 'pending'
        serializer.instance.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        post = self.get_object()
        reaction_type = request.data.get('type')
        if not reaction_type:
            return Response({'detail': 'Reaction type is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure reaction type is valid
        if reaction_type not in [choice[0] for choice in Reaction.REACTION_CHOICES]:
            return Response({'detail': 'Invalid reaction type.'}, status=status.HTTP_400_BAD_REQUEST)

        # Toggle reaction (add if not exists, remove if exists)
        reaction, created = Reaction.objects.get_or_create(
            post=post, user=request.user, type=reaction_type
        )
        if not created:
            reaction.delete()
            return Response({'detail': f'Reaction "{reaction_type}" removed.'}, status=status.HTTP_200_OK)
        return Response({'detail': f'Reaction "{reaction_type}" added.'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        # Implement trending logic based on views, reactions, etc.
        # Cache this heavily as it's a frequently accessed endpoint
        trending_posts = cache.get('trending_posts')
        if not trending_posts:
            # Example: Posts with most views in the last 7 days
            from django.utils import timezone
            from datetime import timedelta
            seven_days_ago = timezone.now() - timedelta(days=7)
            trending_posts = (
    self.get_queryset()
    .filter(created_at__gte=seven_days_ago)
    .annotate(reaction_count=Count('reactions'))
    .order_by('-views', '-reaction_count')[:10]
)
            serializer = self.get_serializer(trending_posts, many=True)
            trending_posts = serializer.data
            cache.set('trending_posts', trending_posts, timeout=60 * 60) # Cache for 1 hour

        return Response(trending_posts)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def moderation_feedback(self, request, pk=None):
        post = self.get_object()
        return Response(post.ai_moderation_feedback)

class ReactionViewSet(viewsets.ModelViewSet):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


