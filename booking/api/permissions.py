from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user if request.user.is_authenticated else None
        return (getattr(obj, "user_id", None) == getattr(user, "id", None)) or (user and user.is_staff)
