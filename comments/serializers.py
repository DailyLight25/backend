from rest_framework import serializers
from .models import Comment
from users.serializers import UserProfileSerializer # To display author info

class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True) # Embed author details

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'reactions', 'ai_moderation_feedback', 'created_at', 'updated_at']
        read_only_fields = ['author', 'reactions', 'ai_moderation_feedback', 'created_at', 'updated_at']

    def create(self, validated_data):
        # The author will be automatically set by the view based on the authenticated user
        validated_data['author'] = self.context['request'].user
        comment = Comment.objects.create(**validated_data)
        # TODO: Trigger AI moderation for comments here (e.g., async task)
        # For now, set a placeholder moderation status
        comment.ai_moderation_feedback = {"status": "pending", "reason": "Awaiting moderation"}
        comment.save()
        return comment