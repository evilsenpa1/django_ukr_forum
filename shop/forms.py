from django import forms
from geo.models import Country, City
from .models import Product
from decimal import Decimal
from django.core.exceptions import ValidationError


class ProductForm(forms.ModelForm):
    city_text = forms.CharField(
        label="Місто",
        widget=forms.TextInput(attrs={
            "class": "city-autocomplete",
            "placeholder": "Введіть місто",
        }),
        required=True
    )
    city_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)

    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),  # минимум 0.01
        max_value=Decimal('99999.99'),
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'max': '99999.99',
            'inputmode': 'decimal',
            'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        error_messages={
            'max_value': 'Максимальна ціна — 99 999.99',
            'min_value': 'Ціна повинна бути більшою за 0',
            'invalid': 'Введіть коректну ціну',
        }
    )

    class Meta:
        model = Product
        fields = [
            "name", "description", "price", "status",
            "category", "country", "city",
        ]

        widgets = {
            "city": forms.HiddenInput(),
            "region": forms.HiddenInput(),
            "name": forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'maxlength': '150'
            }),
            "description": forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': '5',
                'maxlength': '1500'
            }),
            "category": forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            "status": forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            "country": forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.order_by("name")

    def clean_name(self):
        name = self.cleaned_data['name']

        # Reject emoji characters
        if any(ord(char) > 0x1F300 for char in name):
            raise forms.ValidationError('Назва не може мати emoji')

        return name

    def clean_price(self):
        price = self.cleaned_data.get("price")
        
        if price is None:
            return price
        
        if price <= 0:
            raise ValidationError("Ціна повинна бути більшою за 0")
        
        if price > Decimal("99999.99"):
            raise ValidationError("Максимальна ціна — 99 999.99")
        
        return price

    def clean(self):
        cleaned_data = super().clean()
        city_id = cleaned_data.get("city_id")

        if not city_id:
            raise forms.ValidationError("Оберіть місто зі списку підказок.")

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        city_id = self.cleaned_data.get("city_id")

        if city_id:
            city = City.objects.get(id=city_id)
            product.city = city
            product.region = city.region
            product.country = city.country

        if commit:
            product.save()

        return product