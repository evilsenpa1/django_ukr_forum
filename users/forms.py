from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, UserReferrals
from geo.models import Country, Region, City
import logging

logger = logging.getLogger(__name__)


class CreationCustomUserForm(UserCreationForm):
    consent_given = forms.BooleanField(
        required=True,
        error_messages={'required':'Ви повинні надати згоду для реєстрації.'},
        label="Я погоджуюсь на обробку даних"
    )

    # Оголошуємо явно (це поле НЕ буде автоматично зберігатися в модель)
    country = forms.CharField(
        required=False,
        widget=forms.Select(
            choices=[],
            attrs={'id': 'id_country'}
        )
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'] = forms.CharField(
            label="Країна",
            widget=forms.Select(attrs={
                'id': 'id_country'
            })
        )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "display_name", "username", "first_name", "first_name_public",
            "last_name", "last_name_public", "email", "email_public",
            "phone_number", "phone_public", "social_network", "social_public",
            "age",
            "country_public",
            "region_public",
            "city_public",
            "consent_given",            
        )

    def save(self, request, commit=True):
        # "country" is not in Meta.fields, so Django won't try to assign the raw ISO string to it
        user = super().save(commit=False)

        country_iso = self.cleaned_data.get('country')
        country_name = self.data.get('country_name')

        region_iso = self.data.get('region')
        region_name = self.data.get('region_name')

        city_name = self.data.get('city_name')
        city_api_id = self.data.get('city_api_id')

        latitude = self.data.get('latitude')
        longitude = self.data.get('longitude')

        if country_iso and country_name:
            country_obj, _ = Country.objects.get_or_create(
                code=country_iso,
                defaults={'name': country_name}
            )
            user.country = country_obj

            if region_name:
                region_obj, _ = Region.objects.update_or_create(
                    country=country_obj,
                    name=region_name,
                    defaults={'state_code': region_iso}
                )
                user.region = region_obj

                if city_name:
                    def _to_float(val):
                        try:
                            return float(val)
                        except (TypeError, ValueError):
                            return None

                    city_obj, _ = City.objects.update_or_create(
                        region=region_obj,
                        name=city_name,
                        defaults={
                            'country': country_obj,
                            'city_id': city_api_id,
                            'latitude': _to_float(latitude),
                            'longitude': _to_float(longitude),
                        }
                    )
                    user.city = city_obj

        if commit:
            user.save()

        # Referral code is stored in session by ReferralRedirectView
        ref_code = request.session['active_referral_code']

        if ref_code:
            try:
                referral = UserReferrals.objects.get(referral_code=ref_code, status=True)
                referral.invitee = user
                referral.status = False
                referral.used_at = timezone.now()
                referral.save()
                del request.session['active_referral_code']
            except UserReferrals.DoesNotExist:
                pass


        if commit:
            user.save()
        return user



class EditionCustomUserForm(forms.ModelForm):
    # These fields receive ISO codes from JS and are not auto-saved to the model
    country = forms.CharField(
        required=False,
        widget=forms.Select(
            choices=[],
            attrs={'id': 'id_country'}
        )
    )

    region = forms.CharField(required=False)
    city = forms.CharField(required=False)
    

    class Meta():
        model = CustomUser
        fields = (
            "display_name",
            "username",
            "first_name",
            "first_name_public",
            "last_name",
            "last_name_public",
            "email",
            "email_public",
            "phone_number",
            "phone_public",
            "social_network",
            "social_public",
            "age",            
            "country_public",
            "region_public",
            "city_public",
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        country_iso = self.cleaned_data.get('country')
        country_name = self.data.get('country_name')

        currency_code = self.data.get('currency_code')
        currency_symbol = self.data.get('currency_symbol')

        region_iso = self.cleaned_data.get('region')
        region_name = self.data.get('region_name')

        city_name = self.data.get('city_name')
        city_api_id = self.data.get('city_api_id')

        latitude = self.data.get('latitude')
        longitude = self.data.get('longitude')

        if country_iso and country_name:
            country_obj, created = Country.objects.get_or_create(
                code=country_iso,
                defaults={
                    'name': country_name,
                    'currency': self.data.get('currency_code'),
                    'currency_symbol': self.data.get('currency_symbol')
            })

            # Update currency if country already existed and values changed
            if not created:
                updated = False
                if currency_code and country_obj.currency != currency_code:
                    country_obj.currency = currency_code
                    updated = True
                if currency_symbol and country_obj.currency_symbol != currency_symbol:
                    country_obj.currency_symbol = currency_symbol
                    updated = True
                if updated:
                    country_obj.save()

            is_country_changed = user.country != country_obj
            user.country = country_obj

            if region_name:
                region_obj, _ = Region.objects.update_or_create(
                    country=country_obj,
                    name=region_name,
                    defaults={'state_code': region_iso}
                )
                is_region_changed = user.region != region_obj
                user.region = region_obj

                if city_name:
                    try:
                        lat_val = float(latitude) if latitude else None
                        lon_val = float(longitude) if longitude else None
                    except (ValueError, TypeError):
                        lat_val = lon_val = None

                    # Prefer lookup by city_id (API id); fall back to name + region
                    lookup_fields = {'city_id': city_api_id} if city_api_id else {'name': city_name, 'region': region_obj}

                    city_obj, _ = City.objects.update_or_create(
                        **lookup_fields,
                        defaults={
                            'country': country_obj,
                            'region': region_obj,
                            'name': city_name,
                            'city_id': city_api_id,
                            'latitude': lat_val,
                            'longitude': lon_val,
                        }
                    )
                    user.city = city_obj
                else:
                    if is_region_changed or is_country_changed:
                        user.city = None
            else:
                if is_country_changed:
                    user.region = None
                    user.city = None
        else:
            # If country_iso is empty the user didn't change location — leave existing values
            user.country = None
            user.region = None
            user.city = None

        if commit:
            user.save()
        return user
      

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholder_fields = [
            "display_name",
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "social_network",
            "country",
            "region",
            "city",
            # "date_joined",
        ]

        for field_name in placeholder_fields:
            field = self.fields.get(field_name)

            if field is None:
                logger.debug("field '%s' not found in form", field_name)
                continue

            if field and getattr(self.instance, field_name, None):
                field.widget.attrs["placeholder"] = getattr(self.instance, field_name)
            else:
                if field.label:
                    field.widget.attrs["placeholder"] = f"Введіть {field.label.lower()}"

    