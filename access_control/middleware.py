from django.http import HttpResponseForbidden
from .models import AllowedIP

class RestrictAdminAccessMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            ip = request.META.get('REMOTE_ADDR')
            if not AllowedIP.objects.filter(ip_address=ip).exists():
                return HttpResponseForbidden("Access denied: IP address not allowed.")
        response = self.get_response(request)
        return response
