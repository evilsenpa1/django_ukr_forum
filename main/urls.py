from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.IndexPageView.as_view(), name = 'home'),
    path('about/',views.AboutPage.as_view(),name='about'),
    path('rules/',views.RulesPage.as_view(),name='rules'),
    path('in-development/', views.InDevelopmentPage.as_view(), name='in_development'),
]