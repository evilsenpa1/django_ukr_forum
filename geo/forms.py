
from django import forms
from .models import LocationPlace, Country, Region, City


class LocationForm(forms.ModelForm):
    # These fields are added manually as CharField so JS can populate them from the API
    country = forms.CharField(
        label="Країна",
        widget=forms.Select(attrs={'id': 'id_country', 'class': 'form-select'})
    )
    
    region = forms.CharField(
        label="Регіон",
        required=False,
        widget=forms.Select(attrs={'id': 'id_region', 'class': 'form-select'})
    )
    
    city = forms.CharField(
        label="Місто",
        required=False,
        widget=forms.Select(attrs={'id': 'id_city', 'class': 'form-select'})
    )

    local_place_search = forms.CharField(
        label="Пошук закладу (магазин, кафе тощо)",
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_local_place_search', 
            'class': 'form-control',
            'placeholder': 'Почніть вводити назву...'
        })
    )

    class Meta:
        model = Country
        fields = ['country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'local_place') and self.instance.local_place:
            self.fields['local_place_search'].initial = self.instance.local_place.place_name




class GeoLocationFormMixin(forms.Form):
    """Mixin for forms that require a map point selection."""
    local_place_search = forms.CharField(
        label="Пошук на карті",
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_local_place_search',
            'class': 'form-control',
            'placeholder': 'Клікніть на карті або знайдіть адресу...'
        })
    )

    def save_geo_location(self, instance):
        """Save map point to LocationPlace and attach it to the given model instance."""
        p_id = self.data.get('place_id')
        p_name = self.data.get('place_name')
        p_lat = self.data.get('place_lat')
        p_lng = self.data.get('place_lng')

        if p_lat and p_lng:
            lookup = {'place_id': p_id} if p_id else {'latitude': p_lat, 'longitude': p_lng}
            
            place_obj, _ = LocationPlace.objects.update_or_create(
                **lookup,
                defaults={
                    'place_name': p_name or "Вибрана точка",
                    'latitude': p_lat,
                    'longitude': p_lng,
                    'place_id': p_id
                }
            )
            instance.local_place = place_obj
        elif 'local_place_search' in self.data and not self.data.get('local_place_search'):
            instance.local_place = None
        
        return instance