from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import UserRegistrationView, VerifyEmailView, UserProfileView, PublicUserProfileView

urlpatterns = [
    # Registration + Email Verification
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),

    # JWT Login & Refresh
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # User Profiles
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('<int:id>/', PublicUserProfileView.as_view(), name='public_user_profile'),
]
