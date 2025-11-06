from rest_framework import serializers
from .models import User, Follow
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

class UserRegisterSerializer(serializers.ModelSerializer):
    confirmPassword = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmPassword']
        extra_kwargs = {'email': {'required': False}}

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError({
                'confirmPassword': ['Passwords do not match.']
            })
        
        # Check if username already exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({
                'username': ['A user with this username already exists.']
            })
        
        # Check if email already exists (if email is provided)
        if data.get('email') and User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': ['A user with this email already exists.']
            })
        
        return data

    def create(self, validated_data):
        validated_data.pop('confirmPassword')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        # Keep user inactive and unverified until email is verified
        user.is_active = False
        user.is_verified = False
        user.save()

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Try to authenticate with username first
            user = authenticate(username=username, password=password)
            
            # If that fails, try to authenticate with email
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                
                # Check if email is verified
                if hasattr(user, 'is_verified') and not user.is_verified:
                    raise serializers.ValidationError('Please verify your email address before logging in.')
                
                refresh = self.get_token(user)
                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                return data
            else:
                raise serializers.ValidationError('No active account found with the given credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')


class UserProfileSerializer(serializers.ModelSerializer):
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'profile_picture',
            'date_joined',
            'last_login',
            'follower_count',
            'following_count',
            'is_following',
            'is_self',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'date_joined',
            'last_login',
            'follower_count',
            'following_count',
            'is_following',
            'is_self',
        ]

    def get_follower_count(self, obj):
        return obj.follower_relations.count()

    def get_following_count(self, obj):
        return obj.following_relations.count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False

    def get_is_self(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj == request.user
        return False
