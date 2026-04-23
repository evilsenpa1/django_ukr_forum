from re import search
from django.contrib.postgres.search import (
    SearchVector, SearchRank, SearchQuery, TrigramSimilarity
)
from django.db.models import Q, F, Value, FloatField
from django.db.models.functions import Radians, Sin, Cos, Sqrt, ASin, Power, Greatest, Coalesce
from geo.models import City

from django.core.cache import cache
from .models import Categories



def q_search(queryset, search_term, search_fields, weights=None):
    if not search_term or not search_term.strip():
        return queryset.none()

    search_term = search_term.strip()

    if weights is None:
        weights = {field: 'B' for field in search_fields}

    search_vector_uk = SearchVector(
        *search_fields, weight=list(weights.values())[0] if len(weights) == 1 else None,
        config='simple'
    )

    search_query = SearchQuery(
        search_term,
        config='simple',
        search_type='websearch'
    )

    trigram_similarities = []
    for field in search_fields:
        trigram_similarities.append(
            TrigramSimilarity(field, search_term)
        )

    combined_trigram = trigram_similarities[0]
    for sim in trigram_similarities[1:]:
        combined_trigram = combined_trigram + sim

    queryset = queryset.annotate(
        search_rank = SearchRank(search_vector_uk, search_query),
        trigram_similarity = combined_trigram,
        final_rank=Greatest(
            F('search_rank') * 2.0,
            F('trigram_similarity'),
            output_field=FloatField()
        )
    ).filter(
        Q(search_rank__gte=0.01) |
        Q(trigram_similarity__gte=0.2)
    ).order_by('-final_rank')

    return queryset
def haversine(city_id, radius_km, goods):
    city = City.objects.filter(id=city_id).first()
    if not city:
        return goods.none()

    try:
        radius_km = float(radius_km) if radius_km else 5
    except ValueError:
        radius_km = 10

    user_lat = city.latitude
    user_lon = city.longitude
    R = 6371  # Earth radius in km

    products = goods.annotate(
        dlat=Radians(F('city__latitude') - user_lat),
        dlon=Radians(F('city__longitude') - user_lon)
    ).annotate(
        a=Power(Sin(F('dlat') / 2), 2) +
          Cos(Radians(user_lat)) * Cos(Radians(F('city__latitude'))) *
          Power(Sin(F('dlon') / 2), 2)
    ).annotate(
        distance_km=2 * R * ASin(Sqrt(F('a')))
    ).filter(distance_km__lte=radius_km).order_by('distance_km')

    return products


def get_cached_categories():
    cache_key = "categories:all:v1"

    categories = cache.get(cache_key)

    if categories is not None:
        return categories

    cats_qs = Categories.objects.all().order_by("name")

    categories = []
    for c in cats_qs:
        cat_img = None
        if getattr(c, "img", None):
            try:
                cat_img = c.img.url
            except Exception:
                cat_img = None

        categories.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "img": cat_img,
        })

    cache.set(cache_key, categories, timeout=3600 * 12)

    return categories