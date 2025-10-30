from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """
    Main (or index) view.

    Returns rendered default page to the user.
    """
    from django.conf import settings

    context = {
        'debug': settings.DEBUG,
    }
    return render(request, 'main/index.html', context)
