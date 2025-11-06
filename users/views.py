from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.exceptions import TokenError
from .models import User
from .serializers import UserProfileSerializer, UserRegisterSerializer
import os


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # ✅ Create an inactive, unverified user (no token yet)
        user = serializer.save(is_verified=True, is_active=True)

        # ✅ Generate temporary verification token (not login token)
        refresh = RefreshToken.for_user(user)
        token = refresh.access_token
        token["purpose"] = "email_verification"
        token["user_id"] = user.id

        # ✅ Generate verification link
        current_site = get_current_site(self.request).domain
        relative_link = reverse("email-verify")
        abs_url = f"http://{current_site}{relative_link}?token={str(token)}"

        # ✅ Send actual email (via Gmail SMTP)
        send_mail(
            subject="Verify your email",
            message=f"Hi {user.username}, use this link to verify your email: {abs_url}",
            from_email=os.environ.get('EMAIL_HOST_USER'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        token = request.GET.get("token")

        if not token:
            return Response({"error": "Token not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded = AccessToken(token)

            # ✅ Ensure this token was meant for email verification
            if decoded.get("purpose") != "email_verification":
                return Response({"error": "Invalid token purpose"}, status=status.HTTP_400_BAD_REQUEST)

            user_id = decoded.get("user_id")
            if not user_id:
                return Response({"error": "User ID missing in token"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # ✅ Activate and verify the user
            if not user.is_active or not user.is_verified:
                user.is_active = True
                user.is_verified = True
                user.save()

            # ✅ Now generate authentication tokens after successful verification
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            return Response(
                {
                    "message": "Email successfully verified!",
                    "refresh": str(refresh),
                    "access": str(access),
                },
                status=status.HTTP_200_OK,
            )

        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PublicUserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"
