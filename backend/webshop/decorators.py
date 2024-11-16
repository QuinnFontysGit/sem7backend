from django.http import JsonResponse

def require_totp_verified(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('totp_verified', False):
            return JsonResponse({"error": "TOTP verification required."}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
