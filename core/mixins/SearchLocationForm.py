from django import forms
from core.mixins.LocationFieldsMixin import LocationFieldsMixin


class SearchLocationForm(LocationFieldsMixin, forms.Form):
    """Search form that filters by country, region, and city."""
    query = forms.CharField(
        label="Пошук",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Що шукаємо?"})
    )
