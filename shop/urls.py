from django.urls import path
from . import views

APP_NAME = "shop"

urlpatterns = [
    path("", views.index, name="index"),
    path("my_products/", views.MyProducts.as_view(), name="my_products"),
    path("search/", views.search, name="search"),
    path("redirect/search/", views.redirect_to_category, name="redirect_to_category"),
    path("create_product/", views.CreateProduct.as_view(), name="create_product"),
    path("update_product/<int:pk>/<slug:product_slug>/", views.UpdateProduct.as_view(), name="update_product"),

    path("delete_product/<int:pk>/<slug:product_slug>/", views.DeleteProduct.as_view(), name="delete_product"),
    path('delete-image/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
    path("<slug:category_slug>/<int:pk>/<slug:product_slug>/", views.ReadProduct.as_view(), name="product"),
]
