from django.shortcuts import render


def custom_400(request, exception):
    return render(request, "error/400.html", status=400)


def custom_403(request, exception):
    return render(request, "error/403.html", status=403)


def custom_404(request, exception):
    return render(request, "error/404.html", status=404)


def custom_500(request):
    return render(request, "error/500.html", status=500)
