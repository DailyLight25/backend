from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
# from dj_rest_auth.registration.views import RegisterView as BaseRegisterView
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import send_mail
from .models import User, Follow
from .serializers import UserProfileSerializer, UserRegisterSerializer
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]   # 👈 add this


    def perform_create(self, serializer):
        # Auto-verify users for development (skip email verification)
        user = serializer.save(is_verified=True, is_active=True)  # auto-verify and activate
        
        # Comment out email verification code for development
        # refresh = RefreshToken.for_user(user)
        # token = refresh.access_token
        # token["purpose"] = "email_verification"   # 👈 custom claim
        # # Add user_id manually if needed
        # token["user_id"] = user.id

        # current_site = get_current_site(self.request).domain
        # relative_link = reverse("email-verify")
        # abs_url = f"http://{current_site}{relative_link}?token={str(token)}"

        # # Send email
        # send_mail(
        #     subject="Verify your email",
        #     message=f"Hi {user.username}, use this link to verify your email: {abs_url}",
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[user.email],
        # )
        return user


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return self.request.user


class PublicUserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        token = request.GET.get("token")
        try:
            decoded = AccessToken(token)
            if decoded.get("purpose") != "email_verification":
                return Response({"error": "Invalid token purpose"}, status=status.HTTP_400_BAD_REQUEST)

            user_id = decoded["user_id"]
            user = User.objects.get(id=user_id)

            # Mark both verified and active
            if not user.is_active:
                user.is_active = True
            if hasattr(user, "is_verified") and not user.is_verified:
                user.is_verified = True

            user.save()

            return Response({"message": "Email successfully verified!"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ToggleFollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        target_user = get_object_or_404(User, id=kwargs.get("user_id"))

        if target_user == request.user:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user,
        )

        if created:
            serializer = UserProfileSerializer(target_user, context={"request": request})
            return Response({"detail": "Now following user.", "user": serializer.data}, status=status.HTTP_201_CREATED)

        return Response({"detail": "You already follow this user."}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        target_user = get_object_or_404(User, id=kwargs.get("user_id"))
        deleted, _ = Follow.objects.filter(
            follower=request.user,
            following=target_user,
        ).delete()

        if not deleted:
            return Response({"detail": "You are not following this user."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(target_user, context={"request": request})
        return Response({"detail": "Unfollowed user.", "user": serializer.data}, status=status.HTTP_200_OK)


class FollowersListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        target_user = get_object_or_404(User, id=self.kwargs.get("user_id"))
        return User.objects.filter(following_relations__following=target_user).distinct()


class FollowingListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        target_user = get_object_or_404(User, id=self.kwargs.get("user_id"))
        return User.objects.filter(follower_relations__follower=target_user).distinct()
