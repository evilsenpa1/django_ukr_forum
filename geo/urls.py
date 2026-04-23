from django.urls import path
from . import views

app_name = "geo"

urlpatterns = [
    # External API proxies (used by signup/edit forms via JS)
    path('ajax/proxy/countries/', views.load_countries_proxy, name='load_countries_proxy'),
    path('ajax/load-regions/', views.load_states_proxy, name='ajax_load_regions'),
    path('ajax/load-cities/', views.load_cities_proxy, name='ajax_load_cities'),

    path('location/', views.LocationPageView.as_view(), name='location_page'),

    # Internal DB API (used by search/filter UI)
    path('api/locations/', views.GetLocationsApiView.as_view(), name='locations_api'),
    path('api/get-countries/', views.get_countries, name='get_countries_db'),
    path('api/get-regions/', views.get_regions, name="get_regions_db"),
    path('api/get-cities/', views.get_cities, name="get_cities_db"),
]