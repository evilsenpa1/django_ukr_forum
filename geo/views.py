import re
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.generic import FormView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Country, Region, City
from .forms import LocationForm

API_KEY = getattr(settings, 'COUNTRY_STATE_CITY_API_KEY', '')
BASE_URL = getattr(settings, 'BASE_URL_COUNTRY_STATE_CITY', '')
HEADERS = {'X-CSCAPI-KEY': API_KEY}

# ISO country/state codes: 1-15 alphanumeric chars or dashes (e.g. "US", "CA-ON", "NSW")
_GEO_CODE_RE = re.compile(r'^[A-Za-z0-9\-]{1,15}$')

def _is_valid_geo_code(code):
    return bool(code and _GEO_CODE_RE.match(code))

class LocationPageView(LoginRequiredMixin,FormView):
    template_name = "geo_temp/location_page.html"
    form_class = LocationForm
    success_url = '/geo/location/' 

    def form_valid(self, form):
        # ISO codes come from visible select fields
        country_iso = form.cleaned_data.get('country')
        region_iso = form.cleaned_data.get('region')

        # Full names and coordinates are filled by JS into hidden fields
        country_full_name = self.request.POST.get('country_name')
        region_full_name = self.request.POST.get('region_name')
        city_full_name = self.request.POST.get('city_name')

        curr_code = self.request.POST.get('currency_code')
        curr_symbol = self.request.POST.get('currency_symbol')

        external_city_id = self.request.POST.get('city_api_id')
        lat = self.request.POST.get('latitude').strip()
        lng = self.request.POST.get('longitude').strip()

        if country_iso and country_full_name:
            country_obj, created = Country.objects.update_or_create(
                code=country_iso,
                defaults={
                    'name': country_full_name,
                    'currency': curr_code if curr_code else None,
                    'currency_symbol': curr_symbol if curr_symbol else None,
                }
            )

            region_obj = None
            if region_full_name:
                region_obj, _ = Region.objects.get_or_create(
                    country=country_obj,
                    name=region_full_name,
                    defaults={'state_code': region_iso}
                )

                if city_full_name and external_city_id:
                    city_obj, created = City.objects.update_or_create(
                        city_id=external_city_id,
                        defaults={
                            'name': city_full_name,
                            'region': region_obj,
                            'country': country_obj,
                            'latitude': lat if lat else None,
                            'longitude': lng if lng else None,
                        }
                    )
                    status = "збережено" if created else "оновлено"
                    messages.success(self.request, f"Місто {city_full_name} успішно {status}!")
                else:
                    messages.warning(self.request, "Країну та регіон збережено, але місто не вибрано.")
            else:
                messages.warning(self.request, "Країну збережено, але регіон не вибрано.")
        else:
            messages.error(self.request, "Помилка: не вдалося отримати назву країни.")

        return super().form_valid(form)


def load_country_details_proxy(request, country_code):
    """Отримує деталі конкретної країни (валюту, символ тощо)"""
    if not _is_valid_geo_code(country_code):
        return JsonResponse({}, safe=False)
    url = f"{BASE_URL}/countries/{country_code}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    return JsonResponse(response.json(), safe=False)


def load_countries_proxy(request):
    """Отримує список усіх країн з API"""
    url = f"{BASE_URL}/countries"
    response = requests.get(url, headers=HEADERS, timeout=10)
    return JsonResponse(response.json(), safe=False)

def load_states_proxy(request):
    """Отримує регіони конкретної країни"""
    country_code = request.GET.get('country_code', '').strip()
    if not _is_valid_geo_code(country_code):
        return JsonResponse([], safe=False)

    url = f"{BASE_URL}/countries/{country_code}/states"
    response = requests.get(url, headers=HEADERS, timeout=10)
    return JsonResponse(response.json(), safe=False)

def load_cities_proxy(request):
    """Отримує міста конкретного регіону країни"""
    country_code = request.GET.get('country_code', '').strip()
    state_code = request.GET.get('state_code', '').strip()
    if not _is_valid_geo_code(country_code) or not _is_valid_geo_code(state_code):
        return JsonResponse([], safe=False)

    url = f"{BASE_URL}/countries/{country_code}/states/{state_code}/cities"
    response = requests.get(url, headers=HEADERS, timeout=10)
    return JsonResponse(response.json(), safe=False)

class GetLocationsApiView(View):
    def get(self, request):
        country_id = request.GET.get('country_id')
        region_id = request.GET.get('region_id')

        # Якщо прийшов country_id — повертаємо РЕГІОНИ
        if country_id:
            regions = Region.objects.filter(country_id=country_id).values('id', 'name')
            return JsonResponse(list(regions), safe=False)

        if region_id:
            cities = City.objects.filter(region_id=region_id).values('id', 'name')
            return JsonResponse(list(cities), safe=False)

        query = request.GET.get('q', '').strip()
        if query:
            cities = City.objects.filter(name__icontains=query).select_related('region', 'country')[:10]
            results = [{'id': c.id, 'name': c.name} for c in cities]
            return JsonResponse(results, safe=False)

        return JsonResponse([], safe=False)
    
    




def get_countries(request):
    q = request.GET.get("q", "")
    qs = Country.objects.filter(name__icontains=q) if q else Country.objects.all()

    data = [{"id": c.id, "code": c.code, "name": c.name, "currency": c.currency} for c in qs[:15]]
    return JsonResponse(data, safe=False)


def get_regions(request):
    country_id = request.GET.get("country_id")
    if not country_id:
        return JsonResponse([], safe=False)

    qs = Region.objects.filter(country_id=country_id)
    data = [{"id": r.id, "name": r.name} for r in qs]
    return JsonResponse(data, safe=False)


def get_cities(request):
    q = request.GET.get("q", "")
    # Accept both 'country_id' and legacy 'country' parameter names
    country_id = request.GET.get("country_id") or request.GET.get("country")
    region_id = request.GET.get("region_id")

    if len(q) < 2 or not country_id:
        return JsonResponse([], safe=False)

    qs = City.objects.select_related("region").filter(
        name__icontains=q,
        country_id=country_id
    )

    if region_id:
        qs = qs.filter(region_id=region_id)

    data = [
        {
            "id": c.id,
            "city": c.name,
            "region": c.region.name,
            "region_code": c.region.state_code,
        }
        for c in qs[:15]
    ]

    return JsonResponse(data, safe=False)

