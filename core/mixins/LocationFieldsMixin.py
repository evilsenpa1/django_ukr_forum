from django import forms
from geo.models import Country, Region, City

class LocationFieldsMixin():
    """Mixin for location fields. Uses CharField to accept ISO codes sent by JS."""
    # CharField because JS sends 'UA', not an object ID
    country = forms.CharField(
        widget=forms.Select(attrs={"id": "id_country"}),
        label="Країна"
    )
    region = forms.CharField(
        required=False,
        widget=forms.Select(attrs={"id": "id_region"}),
        label="Регіон"
    )
    city = forms.CharField(
        required=False,
        widget=forms.Select(attrs={"id": "id_city"}),
        label="Місто"
    )

    def save_location(self, user):
        # ISO codes come from validated fields; full names come from hidden POST fields
        country_code = self.cleaned_data.get('country')
        region_code = self.cleaned_data.get('region')
        city_name = self.cleaned_data.get('city')

        country_name = self.data.get('country_name')
        region_name = self.data.get('region_name')
        city_api_id = self.data.get('city_api_id')
        lat = self.data.get('latitude')
        lng = self.data.get('longitude')

        if country_code and country_name:
            country_obj, _ = Country.objects.update_or_create(
                code=country_code,
                defaults={'name': country_name}
            )
            user.country = country_obj

            if region_name:
                region_obj, _ = Region.objects.update_or_create(
                    country=country_obj,
                    name=region_name,
                    defaults={'state_code': region_code}
                )
                user.region = region_obj

                if city_name and city_api_id:
                    city_obj, _ = City.objects.update_or_create(
                        city_id=city_api_id,
                        defaults={
                            'name': city_name,
                            'region': region_obj,
                            'country': country_obj,
                            'latitude': lat if lat else None,
                            'longitude': lng if lng else None,
                        }
                    )
                    user.city = city_obj
        return user