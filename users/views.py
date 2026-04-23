
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model

from .forms import CreationCustomUserForm, EditionCustomUserForm
from .models import CustomUser, ConsentText, UserReferrals, get_referral_tree
from geo.models import City, Country, Region
from core.mixins import AuthorOrStaffRequiredMixin
from core.utils.en_de_ref_cod import decode_ref

import logging

logger = logging.getLogger(__name__)


class SignUp(CreateView):
    form_class = CreationCustomUserForm
    success_url = reverse_lazy("users:login")
    template_name = "users_temp/signup.html"
    context_object_name = "sign_up"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['countrys'] = City.objects.all()
        context["country_list"] = Country.objects.all()
        context["region_list"] = Region.objects.all()
        context["city_list"] = City.objects.all()
        latest_consent = ConsentText.objects.order_by('-created_at').first()
        context["consent_version"] = latest_consent

        return context

    def form_valid(self, form):
        user = form.save(request=self.request)
        from django.contrib.auth import login
        login(self.request, user)
        return redirect('users:login')


class DetailUserPage(DetailView):
    model = CustomUser
    context_object_name = "user_detail_public"
    template_name = "users_temp/user_detail_public.html"

    

class ReferralCreateView(LoginRequiredMixin,View):


    def post(self, request, *args, **kwargs):
        user = request.user
        logger.debug("Creating referral code for user: %s", user)
        existing = UserReferrals.objects.filter(referrer=user, status=True).first()
        if not existing:
            UserReferrals.objects.create(referrer=user)
        return redirect('users:user_detail')


class ReferralRedirectView(View):
    def get(self, request, ref_hash):
        original_id = decode_ref(ref_hash)

        if original_id is None:
            return redirect('main:home')

        # Store valid referral code in session so SignUp can use it
        request.session['active_referral_code'] = ref_hash
        return redirect('users:signup')



class EditProfileView(UpdateView):
    model = CustomUser
    form_class = EditionCustomUserForm
    template_name = "users_temp/user_detail.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("users:user_detail")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        referral_code = UserReferrals.objects.filter(referrer=user, status=True).first()
        context['referral'] = referral_code
        return context


class LoginPageView(LoginView):
    template_name = "registration/login.html"
    success_url = reverse_lazy("main:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("main:home")
        return super().dispatch(request, *args, **kwargs)


class LogoutPageView(LogoutView):
    next_page = reverse_lazy("main:home")




User = get_user_model()


@staff_member_required
def admin_referral_tree_view(request):
    # Root users = those who were never invited by anyone
    invited_ids = UserReferrals.objects.filter(invitee__isnull=False).values_list('invitee_id', flat=True)
    root_users = User.objects.exclude(id__in=invited_ids)

    full_tree = []
    for user in root_users:
        has_referrals = UserReferrals.objects.filter(referrer=user, invitee__isnull=False).exists()
        if has_referrals:
            full_tree.append({
                'user': user,
                'children': get_referral_tree(user)
            })

    return render(request, 'users_temp/referral_tree.html', {'tree': full_tree})