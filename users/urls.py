from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("profile/", views.EditProfileView.as_view(), name="user_detail"),
    path('profile/referral/create/', views.ReferralCreateView.as_view(), name='referral_create'),
    path('go/<str:ref_hash>/', views.ReferralRedirectView.as_view(), name='ref_redirect'),
    path("<int:pk>/prof_pub/", views.DetailUserPage.as_view(), name="user_detail_public"),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("login/", views.LoginPageView.as_view(), name="login"),
    path("logout/", views.LogoutPageView.as_view(), name="logout"),
    path('referral-tree/', views.admin_referral_tree_view, name='admin_referral_tree'),
]