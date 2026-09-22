from django.urls import path

from . import views

app_name = 'documents'

urlpatterns = [
    path('contracts/<int:contract_pk>/generate-act/', views.GenerateActView.as_view(), name='generate_act'),
    path('trips/<int:trip_pk>/generate-ttn/', views.GenerateTTNView.as_view(), name='generate_ttn'),
    path('ttn/<int:pk>/xlsx/', views.TTNXlsxView.as_view(), name='ttn_xlsx'),
    path('ttn/<int:pk>/pdf/', views.TTNPdfView.as_view(), name='ttn_pdf'),
    path('registry/', views.registry_page, name='registry'),
    path('registry/xlsx/', views.RegistryXlsxView.as_view(), name='registry_xlsx'),
    path('registry/summary-xlsx/', views.SummaryXlsxView.as_view(), name='summary_xlsx'),
    path('registry/batch/', views.BatchGenerateView.as_view(), name='batch_generate'),
    path('acts/', views.ActListView.as_view(), name='act_list'),
    path('acts/<int:pk>/', views.ActDetailView.as_view(), name='act_detail'),
    path('acts/<int:pk>/preview/', views.ActPreviewView.as_view(), name='act_preview'),
    path('acts/<int:pk>/pdf/', views.ActPdfView.as_view(), name='act_pdf'),
]
