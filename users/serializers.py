from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken

class UserRegisterSerializer(serializers.ModelSerializer):
    confirmPassword = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmPassword']
        extra_kwargs = {'email': {'required': False}}

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirmPassword')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        user.is_active = False  # inactive until email verified
        user.save()

        # Generate verification token
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)

        # TODO: send verification email with `token`
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture', 'date_joined', 'last_login']
        read_only_fields = ['id', 'username', 'email', 'date_joined', 'last_login']
