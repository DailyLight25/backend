# C:\Users\emaru\projects\backend\posts\permissions.py

from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only authors of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of the post.
        return obj.author == request.user

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only admin users to perform write operations,
    while allowing read operations for any user.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to admin users.
        return request.user and request.user.is_staff