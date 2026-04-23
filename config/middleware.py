from django.shortcuts import redirect
from django.conf import settings


class LoginRequiredMiddleware:
    EXEMPT_URLS = ['/users/login/', '/users/signup/', '/.well-known/', '']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            is_exempt = request.path in ['/'] or any(
                request.path.startswith(url) for url in ['/users/login/', '/users/signup/', '/.well-known/', '/health/',]
            )
            if not is_exempt:
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)