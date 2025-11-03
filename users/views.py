from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
# from dj_rest_auth.registration.views import RegisterView as BaseRegisterView
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils import timezone
from django.template.loader import render_to_string
from .models import User, Follow
from .serializers import UserProfileSerializer, UserRegisterSerializer
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)


def cleanup_expired_unverified_users():
    """Helper function to clean up expired unverified users"""
    deleted_count, _ = User.objects.filter(
        is_verified=False,
        verification_expires_at__lt=timezone.now()
    ).delete()
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired unverified user(s)")
    return deleted_count


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]   # 👈 add this


    def perform_create(self, serializer):
        # Clean up any expired unverified users first
        cleanup_expired_unverified_users()
        
        # Create unverified, inactive user
        user = serializer.save(is_verified=False, is_active=False)
        
        # Generate temporary login token for post-verification auto-login
        temp_token = user.generate_temp_login_token()
        
        # Set verification expiry to 2 minutes
        user.set_verification_expiry(hours=0, minutes=2)
        
        # Generate 6-digit verification code
        verification_code = user.generate_verification_code()
        
        # Generate email verification token
        refresh = RefreshToken.for_user(user)
        token = refresh.access_token
        token["purpose"] = "email_verification"
        token["user_id"] = user.id

        current_site = get_current_site(self.request).domain
        relative_link = reverse("email-verify")
        abs_url = f"http://{current_site}{relative_link}?token={str(token)}"
        site_url = f"http://{current_site}"

        # Send HTML email
        subject = "Welcome to DayLight! Verify Your Email Address"
        html_message = render_to_string(
            'users/emails/verification_email.html',
            {
                'username': user.username,
                'verification_code': verification_code,
                'verification_url': abs_url,
                'site_url': site_url,
            }
        )
        
        # Plain text fallback
        plain_message = f"""
Hello {user.username},

Welcome to DayLight! Please verify your email address.

Your verification code is: {verification_code}

Or click this link: {abs_url}

This code expires in 2 minutes.

If you didn't create an account, please ignore this email.

Best regards,
The DayLight Team
"""

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            # Don't fail the registration if email fails, but log it
        
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
        
        if not token:
            return Response({"error": "No token provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Try to decode the token - this will fail if token is expired or invalid
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
            
            # Clear verification code
            user.verification_code = None
            user.save()

            # Return temporary login token for auto-login
            return Response({
                "message": "Email successfully verified!",
                "temp_login_token": user.temp_login_token
            }, status=status.HTTP_200_OK)

        except InvalidToken as e:
            # Token is expired or invalid - delete expired unverified users
            logger.warning(f"Invalid or expired verification token: {str(e)}")
            
            # Clean up all expired unverified users
            deleted_count = cleanup_expired_unverified_users()
            
            return Response({
                "error": "This verification link has expired. Your account has been removed. Please register again.",
                "expired": True
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            return Response({
                "error": "User not found. This verification link is invalid."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            return Response({"error": "An error occurred while verifying your email"}, status=status.HTTP_400_BAD_REQUEST)


class TempLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Login using temporary token after email verification"""
        temp_token = request.data.get('temp_login_token')
        
        if not temp_token:
            return Response({"error": "No temp login token provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(temp_login_token=temp_token, is_verified=True)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Clear the temp token so it can't be reused
            user.temp_login_token = None
            user.save()
            
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({"error": "Invalid or expired login token"}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailCodeView(APIView):
    """Verify email using 6-digit code instead of link"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Verify email with code"""
        code = request.data.get('code')
        email = request.data.get('email')
        
        if not code or not email:
            return Response(
                {"error": "Both code and email are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, is_verified=False)
            
            # Check if code matches
            if not user.verification_code or user.verification_code != code:
                return Response(
                    {"error": "Invalid verification code"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if expired
            if user.is_verification_expired():
                user.delete()
                return Response({
                    "error": "This verification code has expired. Your account has been removed. Please register again.",
                    "expired": True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark as verified and active
            user.is_active = True
            user.is_verified = True
            user.verification_code = None  # Clear the code
            user.save()
            
            return Response({
                "message": "Email successfully verified!",
                "temp_login_token": user.temp_login_token
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid code or email. User not found."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error verifying email with code: {str(e)}")
            return Response(
                {"error": "An error occurred while verifying your email"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class CheckEmailVerificationStatusView(APIView):
    """Check if a user's email has been verified"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Check verification status by email"""
        email = request.GET.get('email')
        
        if not email:
            return Response(
                {"error": "Email parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            response_data = {
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "has_temp_token": bool(user.temp_login_token),
            }
            # If verified and has temp token, include it for auto-login
            if user.is_verified and user.temp_login_token:
                response_data["temp_login_token"] = user.temp_login_token
            return Response(response_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error checking verification status: {str(e)}")
            return Response(
                {"error": "An error occurred while checking verification status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


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
