from django.urls import path

from . import views

app_name = 'fleet'

urlpatterns = [
    path('drivers/', views.DriverListView.as_view(), name='driver_list'),
    path('drivers/new/', views.DriverCreateView.as_view(), name='driver_create'),
    path('drivers/<int:pk>/edit/', views.DriverUpdateView.as_view(), name='driver_update'),

    path('vehicles/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/new/', views.VehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.VehicleUpdateView.as_view(), name='vehicle_update'),

    path('trailers/', views.TrailerListView.as_view(), name='trailer_list'),
    path('trailers/new/', views.TrailerCreateView.as_view(), name='trailer_create'),
    path('trailers/<int:pk>/edit/', views.TrailerUpdateView.as_view(), name='trailer_update'),
]
