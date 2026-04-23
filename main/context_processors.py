from datetime import timedelta
from config import settings
from django.utils import timezone
from users.models import CustomUser
from .models import Visitor
from django.urls import resolve, Resolver404 

def visitor_counters(request):
    now = timezone.now()
    today = now.date()
    five_minutes_ago = now-timedelta(minutes=5)

    total_visitors = Visitor.objects.count()
    today_visitors = Visitor.objects.filter(last_visit__date = today).count()
    aktive_visitors = Visitor.objects.filter(last_visit__gte = five_minutes_ago).count()
    users_visitors = CustomUser.objects.count()

    return {
        'total_visitors': total_visitors,
        'today_visitors':today_visitors,
        'aktive_visitors':aktive_visitors,
        'users_visitors':users_visitors,
    }


def breadcrumbs(request):
    path_segments = request.path.strip('/').split('/')
    crumbs = []
    accumulated_url = '/'
    
    titles_map = {
        'articl': 'Чат',
        'shop': 'Барахолка',
        'advboard': 'Блог',
        'users': 'Користувач',
        'geo': 'Локація',
        'create': 'Створити',
        'edit': 'Редагувати',
        'detail': 'Деталі',
        'profile': 'Профіль',
    }

    for segment in path_segments:
        if not segment or segment.isdigit():
            continue
            
        accumulated_url += f"{segment}/"
        
        is_clickable = True
        try:
            resolve(accumulated_url)
        except Resolver404:
            is_clickable = False

        name = titles_map.get(segment, segment.capitalize())

        crumbs.append({
            'name': name,
            'url': accumulated_url,
            'is_clickable': is_clickable,
        })

    return {'auto_crumbs': crumbs}

def google_maps_key(request):
    return {'GOOGLE_MAPS_KEY': settings.GOOGLE_MAPS_API_KEY}