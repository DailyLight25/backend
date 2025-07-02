from django.urls import path
from dj_rest_auth.views import LoginView, LogoutView
from .views import UserRegistrationView, UserProfileView, PublicUserProfileView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='rest_register'),
    path('login/', LoginView.as_view(), name='rest_login'),
    path('logout/', LogoutView.as_view(), name='rest_logout'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('<int:id>/', PublicUserProfileView.as_view(), name='public_user_profile'),
]