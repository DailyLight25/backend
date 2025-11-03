import mimetypes
import uuid

from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .models import Post, Reaction, PostShare
from .serializers import PostSerializer, ReactionSerializer
from .permissions import IsAuthorOrReadOnly, IsAdminUserOrReadOnly # Custom permissions (define below)
from django.db import models # <--- ADD THIS LINE!
from django.db.models import Count
from storage3.utils import StorageException

from salt_and_light.supabase_client import get_supabase_client, get_public_url, extract_response_error


class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects.filter(status='published')
        .annotate(comment_count=Count('comments'))
        .prefetch_related('reactions__user', 'shares')
    ) # Only show published posts by default
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:  # Admin can see all
                queryset = Post.objects.all().annotate(comment_count=Count('comments')).prefetch_related('reactions__user', 'shares')
            else:  # Author can see their own drafts/pending posts
                queryset = (
                    Post.objects.filter(models.Q(status='published') | models.Q(author=user))
                    .annotate(comment_count=Count('comments'))
                    .prefetch_related('reactions__user', 'shares')
                )
        else:
            queryset = super().get_queryset()

        author_param = self.request.query_params.get('author')
        if author_param:
            if author_param == 'me' and user.is_authenticated:
                queryset = queryset.filter(author=user)
            else:
                try:
                    queryset = queryset.filter(author_id=int(author_param))
                except (TypeError, ValueError):
                    queryset = queryset.none()

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    def perform_create(self, serializer):
        # Set the author automatically to the current user
        serializer.save(author=self.request.user)
        # In a real scenario, this would likely trigger an async AI moderation task
        # For now, let's set it to 'pending'
        serializer.instance.status = 'pending'
        serializer.instance.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def share(self, request, pk=None):
        post = self.get_object()
        platform = request.data.get('platform', '')
        message = request.data.get('message', '')

        share, created = PostShare.objects.get_or_create(
            post=post,
            user=request.user,
            platform=platform,
            defaults={'message': message},
        )

        if not created:
            share.message = message
            share.save(update_fields=['message'])
            post.refresh_from_db()
            serializer = self.get_serializer(post)
            return Response({'detail': 'Share updated.', 'post': serializer.data}, status=status.HTTP_200_OK)

        post.refresh_from_db()
        serializer = self.get_serializer(post)
        return Response({'detail': 'Post shared successfully.', 'post': serializer.data}, status=status.HTTP_201_CREATED)

    @share.mapping.delete
    def unshare(self, request, pk=None):
        post = self.get_object()
        deleted, _ = PostShare.objects.filter(post=post, user=request.user).delete()
        if deleted:
            post.refresh_from_db()
            serializer = self.get_serializer(post)
            return Response({'detail': 'Share removed.', 'post': serializer.data}, status=status.HTTP_200_OK)
        return Response({'detail': 'No share found for this post.'}, status=status.HTTP_404_NOT_FOUND)

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


class UploadPostImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        image_file = request.FILES.get('image')

        if not image_file:
            return Response({'detail': 'No image file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        content_type = getattr(image_file, 'content_type', '') or mimetypes.guess_type(image_file.name)[0] or ''
        if not content_type.startswith('image/'):
            return Response({'detail': 'Invalid file type. Only image uploads are allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        extension = mimetypes.guess_extension(content_type) or ''
        if not extension:
            name_parts = image_file.name.rsplit('.', 1)
            if len(name_parts) == 2:
                extension = f".{name_parts[1]}"

        unique_name = f"posts/{request.user.id}/{uuid.uuid4().hex}{extension}"

        client = get_supabase_client()
        bucket = client.storage.from_(settings.SUPABASE_POST_IMAGE_BUCKET)

        file_bytes = image_file.read()

        try:
            response = bucket.upload(unique_name, file_bytes, {
                "contentType": content_type,
                "cacheControl": "31536000",
                "upsert": "false",
            })
        except StorageException as exc:
            detail = getattr(exc, 'message', None) or getattr(exc, 'error', None) or str(exc)
            return Response({'detail': f'Image upload failed: {detail}'}, status=status.HTTP_502_BAD_GATEWAY)

        error_message = extract_response_error(response)
        if error_message:
            return Response({'detail': f'Image upload failed: {error_message}'}, status=status.HTTP_502_BAD_GATEWAY)

        public_url = get_public_url(unique_name)
        if not public_url:
            return Response({'detail': 'Unable to resolve public URL for uploaded image.'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({'url': public_url, 'path': unique_name}, status=status.HTTP_201_CREATED)

