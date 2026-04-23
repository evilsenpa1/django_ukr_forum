from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Categories, ProductImage
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Categories)
def invalidate_categories_cache(sender, instance, **kwargs):
    cache_key = "categories:all:v1"
    cache.delete(cache_key)
    logger.debug("Cache invalidated: %s", cache_key)


@receiver([post_save, post_delete], sender=Product)
def invalidate_products_cache_on_product_change(sender, instance, **kwargs):
    cache_key_all = "catalog:product:all:v1"
    cache.delete(cache_key_all)
    logger.debug("Cache invalidated: %s", cache_key_all)


@receiver([post_save, post_delete], sender=ProductImage)
def invalidate_products_cache_on_image_change(sender, instance, **kwargs):
    """Invalidate catalog cache when a product image is added, changed, or deleted."""
    product = instance.product

    cache_key_all = "catalog:category:all:page:1:v1"
    cache.delete(cache_key_all)
    logger.debug("Cache invalidated: %s", cache_key_all)

    if product.category:
        cache_key_category = f"catalog:category:{product.category.slug}:page:1:v1"
        cache.delete(cache_key_category)
        logger.debug("Cache invalidated: %s", cache_key_category)


@receiver([post_save, post_delete], sender=Product)
def invalidate_search_cache(sender, instance, **kwargs):
    """Invalidate search result cache when any product changes."""
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern("search_results:*")