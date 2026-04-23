from django.contrib import admin
from .models import Categories, Product, ProductImage

# Register your models here.

@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}
    readonly_fields = ("date", "date_update")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)