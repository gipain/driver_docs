from django.urls import path

from . import views

app_name = 'partners'

urlpatterns = [
    path('counterparties/', views.CounterpartyListView.as_view(), name='counterparty_list'),
    path('counterparties/new/', views.CounterpartyCreateView.as_view(), name='counterparty_create'),
    path('counterparties/<int:pk>/edit/', views.CounterpartyUpdateView.as_view(), name='counterparty_update'),

    path('contracts/', views.ContractListView.as_view(), name='contract_list'),
    path('contracts/new/', views.ContractCreateView.as_view(), name='contract_create'),
    path('contracts/<int:pk>/edit/', views.ContractUpdateView.as_view(), name='contract_update'),
]
