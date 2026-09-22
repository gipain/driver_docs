from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.anomaly import trip_amount_anomaly
from documents.autofill import build_ttn_context
from trips.validation import validate_trip_for_confirmation

from .forms import TripForm
from .models import Trip


class TripListView(ListView):
    model = Trip
    template_name = 'trips/trip_list.html'
    context_object_name = 'trips'
    queryset = Trip.objects.select_related('driver', 'vehicle', 'carrier', 'sender', 'receiver')


class TripDetailView(DetailView):
    """Картка рейсу, доповнена попереднім переглядом автозаповнення
    (день 6) і результатом перевірок (день 7) - щоб побачити ці
    алгоритми в дії просто на сторінці, ще до появи форми генерації
    самого документа (дні 9-10)."""

    model = Trip
    template_name = 'trips/trip_detail.html'
    context_object_name = 'trip'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        trip = self.object
        ctx['ttn_context'] = build_ttn_context(trip)
        ctx['validation_errors'] = validate_trip_for_confirmation(trip)
        is_anomaly, z_score = trip_amount_anomaly(trip)
        ctx['amount_is_anomaly'] = is_anomaly
        ctx['amount_z_score'] = z_score
        return ctx


class TripCreateView(CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'generic_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Рейс №{self.object.pk} створено як чернетку.')
        return response

    def get_success_url(self):
        return reverse_lazy('trips:trip_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий рейс'
        ctx['back_url'] = reverse_lazy('trips:trip_list')
        return ctx


class TripUpdateView(UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'generic_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Рейс №{self.object.pk} оновлено.')
        return response

    def get_success_url(self):
        return reverse_lazy('trips:trip_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редагування рейсу №{self.object.pk}'
        ctx['back_url'] = reverse_lazy('trips:trip_detail', args=[self.object.pk])
        return ctx


class TripConfirmView(View):
    """Переводить рейс у статус «підтверджено» й пише запис у журнал
    змін (Trip.confirm(), день 5). Лише POST - підтвердження це дія
    зі побічним ефектом, не має відбуватись по GET-посиланню."""

    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk)
        try:
            trip.confirm()
            messages.success(request, f'Рейс №{trip.pk} підтверджено.')
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect('trips:trip_detail', pk=pk)
