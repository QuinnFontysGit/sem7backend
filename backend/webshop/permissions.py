from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Customer').exists()

class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        return request.user.groups.filter(name='Manager').exists()

class IsCartOwner(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'list':
            raise PermissionDenied('You are not allowed to access this resource.')
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.id == obj.account.id:
            return True
        raise PermissionDenied('Not your shopping cart')
