
from django.contrib.auth.mixins import UserPassesTestMixin

class OwnerRequiredMixin(UserPassesTestMixin):

    owner_field = "author"

    def test_func(self):
        obj = self.get_object()

        return getattr(obj, self.owner_field) == self.request.user or self.request.user.is_staff