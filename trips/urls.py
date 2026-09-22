from django.urls import path

from . import views

app_name = 'trips'

urlpatterns = [
    path('trips/', views.TripListView.as_view(), name='trip_list'),
    path('trips/new/', views.TripCreateView.as_view(), name='trip_create'),
    path('trips/<int:pk>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('trips/<int:pk>/edit/', views.TripUpdateView.as_view(), name='trip_update'),
    path('trips/<int:pk>/confirm/', views.TripConfirmView.as_view(), name='trip_confirm'),
]
