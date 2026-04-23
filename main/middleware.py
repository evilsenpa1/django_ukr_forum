import datetime
from django.utils.deprecation import MiddlewareMixin
from .models import Visitor


class VisitorTrackingMiddleware(MiddlewareMixin):
    """Tracks visitor IP, User-Agent, and last visit time."""

    def process_request(self, request):
        # Use X-Forwarded-For to get real IP behind a proxy
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
            or request.META.get('REMOTE_ADDR')
        )

        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        session_key = request.session.session_key

        if not session_key:
            request.session.save()
            session_key = request.session.session_key

        visitor, created = Visitor.objects.get_or_create(
            ip=ip,
            defaults={
                'user_agent': user_agent,
                'session_key': session_key,
                'last_visit': datetime.datetime.now(),
            },
        )

        if not created:
            visitor.last_visit = datetime.datetime.now()
            visitor.user_agent = user_agent
            visitor.session_key = session_key
            visitor.save(update_fields=['last_visit', 'user_agent', 'session_key'])
