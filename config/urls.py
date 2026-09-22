from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='partners:counterparty_list'), name='home'),
    path('', include('partners.urls')),
    path('', include('fleet.urls')),
    path('', include('trips.urls')),
    path('', include('documents.urls')),
]
