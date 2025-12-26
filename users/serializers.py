from rest_framework import serializers
# from posts.serializers import PostSerializer
from .models import User, Follow
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
# from notifications.serializers import NotificationSerializer

class UserRegisterSerializer(serializers.ModelSerializer):
    confirmPassword = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmPassword']
        # Ensure email is unique in the model validation if creating a new user
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False}
        }

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError({
                'confirmPassword': ['Passwords do not match.']
            })
        # Removed manual uniqueness checks; allow DRF ModelSerializer to handle DB constraints
        return data

    def create(self, validated_data):
        validated_data.pop('confirmPassword')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        user.is_active = False
        user.is_verified = False
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # This serializer is logically sound for email/username login.
    def validate(self, attrs):
        username = attrs.get('username') # Frontend can send email here
        password = attrs.get('password')

        if username and password:
            # 1. Try Authentication as Username
            user = authenticate(username=username, password=password)

            # 2. If fail, Try Authentication as Email
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                
                # Robust check for custom attribute
                if getattr(user, 'is_verified', False) is False:
                     raise serializers.ValidationError('Please verify your email address before logging in.')

                refresh = self.get_token(user)
                return {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {  # Optional: Helpful to send user info back on login
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                }
            else:
                raise serializers.ValidationError('No active account found with the given credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

class UserProfileSerializer(serializers.ModelSerializer):
    # These fields are expensive (SLOW) for lists of users.
    # Ensure 'follower_relations' and 'following_relations' match your models.py related_name
    follower_count = serializers.IntegerField(source='follower_relations.count', read_only=True)
    following_count = serializers.IntegerField(source='following_relations.count', read_only=True)
    is_following = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'profile_picture', 'date_joined', 
            'last_login', 'follower_count', 'following_count', 'is_following', 'is_self'
        ]
        read_only_fields = fields

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            # This is a query per row. Optimized apps usually prefetch this data in the View.
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False

    def get_is_self(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.id == request.user.id
        return False    
    
