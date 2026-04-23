from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme


class AuthorOrStaffRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.author != request.user and not request.user.is_staff:
            referer_url = request.META.get('HTTP_REFERER')
            # Only redirect back to referer if it belongs to the same host
            if referer_url and url_has_allowed_host_and_scheme(
                referer_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(referer_url)
            return redirect(reverse_lazy('main:home'))

        return super().dispatch(request, *args, **kwargs)
