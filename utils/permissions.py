from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsCustomerUser(permissions.BasePermission):
    """
    Allows access only to customer users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'customer'
