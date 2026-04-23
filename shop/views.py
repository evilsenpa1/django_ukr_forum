from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from core.mixins.permissions import OwnerRequiredMixin
from shop.models import Categories, Product, ProductImage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .forms import ProductForm
from slugify import slugify
from django.views.generic import CreateView, DeleteView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from geo.models import City, Country, Region
from shop.utils import q_search, haversine, get_cached_categories
from urllib.parse import urlencode
from django.core.cache import cache
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

def index(request):
    RADII = [10, 30, 50, 100]
    cache_key_categories = "categories:all:v1"
    cache_key_products = "catalog:product:all:v1"

    categories = cache.get(cache_key_categories)
    if categories is None:
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

        cache.set(cache_key_categories, categories, timeout=3600 * 12)

    products = cache.get(cache_key_products)
    if products is None:
        products_qs = Product.objects.select_related("category", "city", "region", "country").prefetch_related("images").order_by("-date")[:15]

        products = []
        for p in products_qs:
            images_list=[]
            try:
                for img_obj in p.images.all():
                    if getattr(img_obj, "image", None):
                        try:
                            images_list.append(img_obj.image.url)
                        except Exception:
                            pass
            except Exception:
                images_list = []
            first_image = images_list[0] if images_list else None

            products.append({
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "slug": p.slug,
                    "date": p.date.isoformat(),
                    "category": {"id": p.category_id, "name": p.category.name, "slug": p.category.slug},
                    "country": {"id": p.country_id, "name": p.country.name, "currency_symbol": p.country.currency_symbol if p.country else None, "currency": p.country.currency if p.country else ""},
                    "region": {"id": p.region_id, "name": p.region.name if p.region else None},
                    "city": {"id": p.city_id, "name": p.city.name if p.city else None},
                    "images": first_image,
                })
        
        cache.set(cache_key_products, products, timeout=60 * 15)

    context = {
    "title": "Торгівля",
    "Category": categories, 
    "Products": products,
    "RADII": RADII,
    }
    return render(request, "shop_temp/index.html", context)

def _safe_int(value):
    """Return int if value is a digit string, otherwise None."""
    if value and str(value).isdigit():
        return int(value)
    return None

def search(request, category_slug=None):

    page = request.GET.get("page", 1)

    country_id  = _safe_int(request.GET.get('country_id'))
    region_id   = _safe_int(request.GET.get('region_id'))
    city_id     = _safe_int(request.GET.get('city_id'))
    category_id = _safe_int(request.GET.get('category_id'))

    q = (request.GET.get('q', '') or '').strip()[:200]


    radius = request.GET.get('radius', None)
    status = request.GET.get('status', None)
    date_sort = request.GET.get('date_sort', None)


    RADII = [10, 30, 50, 100]
    PER_PAGE = 10

    categories = get_cached_categories()


    products = Product.objects.select_related(
        "category", 
        "author", 
        "city", 
        "region", 
        "country"
    )

    if q:
        products = q_search(products, q, search_fields=['name', 'description'])


    if category_id:
        try:
            category = Categories.objects.get(id=category_id)
            products = products.filter(category=category)
            title = f"Барахолка - {category.name}"
        except Categories.DoesNotExist:
            title = "Барахолка - Усі товари"
    else:
        title = "Барахолка - Усі товари"



    country = None
    region = None
    city = None

    if country_id:
        try:
            country = Country.objects.get(id=country_id)
            products = products.filter(country=country)
        except Country.DoesNotExist:
            country_id = None
            country = None
            region_id = None
            city_id = None
            radius = None

    if region_id:
        if country:
            try:
                region = Region.objects.get(id=region_id, country=country)
                products = products.filter(region_id=region_id)
            except Region.DoesNotExist:
                # Region does not belong to the selected country — reset dependent params
                region_id = None
                region = None
                city_id = None
                radius = None
        else:
            region_id = None
            city_id = None
            radius = None


    if city_id:
        if country:
            try:
                city_filter = {'id': city_id, 'country': country, 'region': region}

                city = City.objects.get(**city_filter)

                if radius:
                    try:
                        products = haversine(city_id, radius, products)
                    except (ValueError, TypeError):
                        products = products.filter(city=city)
                        radius = None
                else:
                    products = products.filter(city=city)

            except City.DoesNotExist:
                city_id = None
                city = None
                radius = None
    else:
        city_id = None
        radius = None
    
    if radius and not city_id:
        radius = None



    if status and status in ['new', 'used']:
        products = products.filter(status=status)

    if date_sort and date_sort in ['date', '-date']:
        products = products.order_by(date_sort)
    else:
        products = products.order_by("-date")

    cache_key = _generate_cache_key(request.GET, page)
    cached_result = cache.get(cache_key)

    if cached_result:
        products_page = cached_result
    else:
        paginator = Paginator(products, PER_PAGE)
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        cache.set(cache_key, products_page, timeout=180)

    context = {
        "title": title,
        "Products": products_page,
        "Category": categories,
        "category_slug": category_slug,
        "q": q,
        "RADII": RADII
    }

    return render(request, "shop_temp/product_list.html", context)

def _generate_cache_key(get_params, page):
    """Generate a stable cache key from search parameters."""
    params = {
        'q': get_params.get('q', ''),
        'country_id': get_params.get('country_id', ''),
        'region_id': get_params.get('region_id', ''),
        'city_id': get_params.get('city_id', ''),
        'radius': get_params.get('radius', ''),
        'status': get_params.get('status', ''),
        'date_sort': get_params.get('date_sort', ''),
        'category_id': get_params.get('category_id', ''),
        'page': page,
    }

    params_string = json.dumps(params, sort_keys=True)
    hash_object = hashlib.md5(params_string.encode())
    
    return f"search_results:{hash_object.hexdigest()}"


def redirect_to_category(request):
    category_id = request.GET.get('category_id')

    if not category_id or not category_id.isdigit():
        return redirect("shop:index")

    # Проверяем, что категория существует
    category = get_object_or_404(Categories, id=category_id)

    query_params = {"category_id": category.id}


    if request.user.is_authenticated:
        user = request.user
        if user.country_id:
            try:
                query_params["country_id"] = user.country.id
                query_params["country_name"] = user.country.name
            except AttributeError:
                pass
        if user.region_id:
            try:
                query_params["region_id"] = user.region.id
                query_params["region_name"] = user.region.name
            except AttributeError:
                pass

    base_url = reverse("shop:search")
    return redirect(f"{base_url}?{urlencode(query_params)}")
    

class ReadProduct(LoginRequiredMixin, DetailView):
    model = Product


    template_name = "shop_temp/product_cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object
        return context


class CreateProduct(LoginRequiredMixin, CreateView):
    model = Product

    def get_queryset(self):
        return super().get_queryset().select_related("category", "author", "currency", "city", "region", "country")
    
    form_class = ProductForm

    template_name = "shop_temp/create_product.html"

    success_url = reverse_lazy("shop:index")


    def form_valid(self, form):

        for f in self.request.FILES.getlist('images'):
            logger.debug("file: %s size=%s type=%s", f.name, f.size, type(f))


        form.instance.author = self.request.user
        form.instance.slug = slugify(form.instance.name)

        city_id = form.cleaned_data.get("city_id")
        if city_id:
            city = City.objects.get(id=city_id)
            form.instance.city = city
            form.instance.region = city.region
            form.instance.country = city.country

        response = super().form_valid(form)

        images = self.request.FILES.getlist('images')

        for image in images:
            ProductImage.objects.create(product=self.object, image=image)


        return response
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.status_code = 400
        logger.debug("ProductForm invalid: %s", form.errors)
        return response


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Додання товару"
        context["categories"] = Categories.objects.all()
        return context

    



class UpdateProduct(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "shop_temp/update_product.html"
    success_url = reverse_lazy("shop:index")

    def form_valid(self, form):
        form.instance.slug = slugify(form.instance.name)
        response = super().form_valid(form)

        images = self.request.FILES.getlist("images")
        for image in images:
            ProductImage.objects.create(product=self.object, image=image)
        
        deleted_images_json = self.request.POST.get('deleted_images')
        if deleted_images_json:
            try:
                deleted_ids = json.loads(deleted_images_json)
                ProductImage.objects.filter(
                    id__in=deleted_ids,
                    product=self.object
                ).delete()
            except (json.JSONDecodeError, ValueError):
                pass
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Редагування товару"
        context["categories"] = Categories.objects.all()
        return context






@require_POST
@login_required
def delete_product_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)

    product = image.product
    if product is None or not Product.objects.filter(pk=product.pk).exists():
        return JsonResponse(
            {"error": "Продукт, пов’язаний із цим зображенням, не існує"}, status=400
        )

    if not request.user.is_staff and product.author != request.user:
        return JsonResponse(
            {"error": "У вас немає прав для видалення цього фото"}, status=403
        )

    image.image.delete(save=False)
    image.delete()

    return JsonResponse({"status": "ok"})


class DeleteProduct(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):

    model = Product

    template_name = "shop_temp/delete_product.html"

    success_url = reverse_lazy("shop:index")


class MyProducts(LoginRequiredMixin, ListView):
    model = Product
    template_name = "shop_temp/my_products.html"
    context_object_name = "products"
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.filter(author=self.request.user).order_by('date_update')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Мої товари"
        return context