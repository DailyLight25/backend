from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from dj_rest_auth.registration.views import RegisterView as BaseRegisterView
from .models import User
from .serializers import UserProfileSerializer, UserRegisterSerializer

class UserRegistrationView(BaseRegisterView):
    serializer_class = UserRegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Allow users to retrieve/update their own profile using /api/users/me/
        return self.request.user

class PublicUserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny] # Publicly accessible
    lookup_field = 'id' # To access by user ID (e.g., /api/users/1/)