from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Comment
from .serializers import CommentSerializer
from posts.models import Post # To link comments to posts
from posts.permissions import IsAuthorOrReadOnly

from comments import serializers # Re-use permission

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        # Allow filtering comments by post_id
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def perform_create(self, serializer):
        # Ensure post_id is provided and valid
        post_id = self.request.data.get('post') # 'post' field from request body
        if not post_id:
            raise serializers.ValidationError({"post": "This field is required."})
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise serializers.ValidationError({"post": "Post not found."})

        serializer.save(author=self.request.user, post=post)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        comment = self.get_object()
        reaction_type = request.data.get('type') # e.g., 'heart', 'pray'

        if not reaction_type:
            return Response({'detail': 'Reaction type is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update reactions JSONField
        reactions = comment.reactions or {}
        user_id = str(request.user.id)

        if user_id in reactions and reactions[user_id] == reaction_type:
            # User already reacted with this type, so remove it (toggle off)
            del reactions[user_id]
            message = f'Reaction "{reaction_type}" removed.'
        else:
            # Add or change reaction
            reactions[user_id] = reaction_type
            message = f'Reaction "{reaction_type}" added.'

        comment.reactions = reactions
        comment.save()
        return Response({'detail': message, 'reactions': comment.reactions}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def moderation_feedback(self, request, pk=None):
        comment = self.get_object()
        return Response(comment.ai_moderation_feedback)