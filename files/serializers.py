from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'post', 'file', 'file_type', 'size', 'ai_moderation', 'uploaded_at']
        read_only_fields = ['file_type', 'size', 'ai_moderation', 'uploaded_at'] # These are set by the view logic

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(max_length=None, use_url=True)
    post_id = serializers.IntegerField(required=False) # To link file directly to a post on upload

    def validate_file(self, value):
        if value.size > 5 * 1024 * 1024: # 5MB limit
            raise serializers.ValidationError("File size cannot exceed 5MB.")
        return value