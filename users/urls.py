from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UserRegistrationView,
    VerifyEmailView,
    VerifyEmailCodeView,
    CheckEmailVerificationStatusView,
    TempLoginView,
    UserProfileView,
    PublicUserProfileView,
    ToggleFollowView,
    FollowersListView,
    FollowingListView,
)

urlpatterns = [
    # Registration + Email Verification
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('email-verify/', VerifyEmailView.as_view(), name='email-verify'),
    path('email-verify-code/', VerifyEmailCodeView.as_view(), name='email-verify-code'),
    path('check-verification-status/', CheckEmailVerificationStatusView.as_view(), name='check_verification_status'),
    path('temp-login/', TempLoginView.as_view(), name='temp_login'),

    # JWT Login & Refresh
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # User Profiles
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('<int:user_id>/follow/', ToggleFollowView.as_view(), name='toggle_follow'),
    path('<int:user_id>/followers/', FollowersListView.as_view(), name='followers_list'),
    path('<int:user_id>/following/', FollowingListView.as_view(), name='following_list'),
    path('<int:id>/', PublicUserProfileView.as_view(), name='public_user_profile'),
]
