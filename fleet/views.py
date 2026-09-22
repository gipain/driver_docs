from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import DriverForm, TrailerForm, VehicleForm
from .models import Driver, Trailer, Vehicle


class DriverListView(ListView):
    model = Driver
    template_name = 'fleet/driver_list.html'
    context_object_name = 'drivers'


class DriverCreateView(SuccessMessageMixin, CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('fleet:driver_list')
    success_message = 'Водія "%(full_name)s" додано.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий водій'
        ctx['back_url'] = self.success_url
        return ctx


class DriverUpdateView(SuccessMessageMixin, UpdateView):
    model = Driver
    form_class = DriverForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('fleet:driver_list')
    success_message = 'Дані водія "%(full_name)s" оновлено.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редагування: {self.object.full_name}'
        ctx['back_url'] = self.success_url
        return ctx


class VehicleListView(ListView):
    model = Vehicle
    template_name = 'fleet/vehicle_list.html'
    context_object_name = 'vehicles'


class VehicleCreateView(SuccessMessageMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('fleet:vehicle_list')
    success_message = 'Автомобіль "%(plate_number)s" додано.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий автомобіль'
        ctx['back_url'] = self.success_url
        return ctx


class VehicleUpdateView(SuccessMessageMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('fleet:vehicle_list')
    success_message = 'Автомобіль "%(plate_number)s" оновлено.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редагування: {self.object.plate_number}'
        ctx['back_url'] = self.success_url
        return ctx


class TrailerListView(ListView):
    model = Trailer
    template_name = 'fleet/trailer_list.html'
    context_object_name = 'trailers'


class TrailerCreateView(SuccessMessageMixin, CreateView):
    model = Trailer
    form_class = TrailerForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('fleet:trailer_list')
    success_message = 'Причіп "%(plate_number)s" додано.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий причіп'
        ctx['back_url'] = self.success_url
        return ctx


class TrailerUpdateView(SuccessMessageMixin, UpdateView):
    model = Trailer
    form_class = TrailerForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('fleet:trailer_list')
    success_message = 'Причіп "%(plate_number)s" оновлено.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редагування: {self.object.plate_number}'
        ctx['back_url'] = self.success_url
        return ctx
