"""
Custom permission classes for AutoParts Kenya API.
Implements guest-first philosophy and owner-only restrictions.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """
    Permission to check if user is the store owner.
    Owner is identified by UserProfile.is_owner = True.
    """
    message = 'Huenda katika kuruka kuweza fanya operesheni hii. (You do not have permission to perform this action.)'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_owner


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission allowing owner to edit/delete, anyone to read.
    """
    message = 'Huenda katika kuruka kuweza kubadilisha au kuondoa hii. (You do not have permission to modify or delete this.)'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_owner


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Permission allowing unauthenticated read access, authenticated write access.
    Guest-first design: GET endpoints are public, POST/PUT/DELETE require login.
    """
    message = 'Tafadhali ingia akaunti ili kuendelea. (Please log in to continue.)'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsOwnerOrCreateOnly(BasePermission):
    """
    Permission allowing owner write access, all users can create (registration).
    Used in user registration endpoint.
    """

    def has_permission(self, request, view):
        # Allow POST (create) for registration
        if request.method == 'POST':
            return True
        # Allow owner to edit their own profile
        if request.user and request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_owner:
            return True
        # Deny all other requests
        return False
