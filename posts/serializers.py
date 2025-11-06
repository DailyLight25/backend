from django.db.models import Count
from rest_framework import serializers
from .models import Post, Reaction
from users.serializers import UserProfileSerializer # To display author info

class PostSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True) # Embed author details
    reaction_counts = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()
    user_reactions = serializers.SerializerMethodField()
    has_shared = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(read_only=True, default=0)
    # You might want to include files here too, but for simplicity, let's assume files are managed separately
    # and linked later or fetched by a separate API call.

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'content',
            'image_url',
            'tags',
            'scripture_refs',
            'author',
            'status',
            'views',
            'created_at',
            'updated_at',
            'ai_moderation_feedback',
            'reaction_counts',
            'share_count',
            'user_reactions',
            'has_shared',
            'comment_count',
        ]
        read_only_fields = [
            'author',
            'status',
            'views',
            'created_at',
            'updated_at',
            'ai_moderation_feedback',
            'reaction_counts',
            'share_count',
            'user_reactions',
            'has_shared',
            'comment_count',
        ]
        extra_kwargs = {
            'image_url': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

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

    def get_reaction_counts(self, obj):
        reaction_summary = obj.reactions.values('type').annotate(count=Count('id'))
        return {item['type']: item['count'] for item in reaction_summary}

    def get_share_count(self, obj):
        return obj.shares.count()

    def get_user_reactions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return list(obj.reactions.filter(user=request.user).values_list('type', flat=True))
        return []

    def get_has_shared(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shares.filter(user=request.user).exists()
        return False

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'post', 'user', 'type', 'created_at']
        read_only_fields = ['user', 'created_at']