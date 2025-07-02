from rest_framework import serializers
from .models import Post, Reaction
from users.serializers import UserProfileSerializer # To display author info

class PostSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True) # Embed author details
    # You might want to include files here too, but for simplicity, let's assume files are managed separately
    # and linked later or fetched by a separate API call.

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'tags', 'scripture_refs', 'author',
                  'status', 'views', 'created_at', 'updated_at', 'ai_moderation_feedback']
        read_only_fields = ['author', 'status', 'views', 'created_at', 'updated_at', 'ai_moderation_feedback']

    def create(self, validated_data):
        # The author will be automatically set by the view based on the authenticated user
        validated_data['author'] = self.context['request'].user
        post = Post.objects.create(**validated_data)
        # Trigger AI moderation here (e.g., via a Celery task or directly if quick)
        # from scripts.ai_moderation import moderate_content
        # post.ai_moderation_feedback = moderate_content(post.content, post.scripture_refs)
        # post.status = 'pending' # Initial status
        # post.save()
        return post

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'post', 'user', 'type', 'created_at']
        read_only_fields = ['user', 'created_at']