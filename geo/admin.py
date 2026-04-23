from django.contrib import admin
from .models import Country, Region, City
# Register your models here.

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    pass

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    pass

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    pass