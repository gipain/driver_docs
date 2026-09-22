from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ContractForm, CounterpartyForm
from .models import Contract, Counterparty


class CounterpartyListView(ListView):
    model = Counterparty
    template_name = 'partners/counterparty_list.html'
    context_object_name = 'counterparties'


class CounterpartyCreateView(SuccessMessageMixin, CreateView):
    model = Counterparty
    form_class = CounterpartyForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('partners:counterparty_list')
    success_message = 'Контрагента "%(name)s" створено.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий контрагент'
        ctx['back_url'] = self.success_url
        return ctx


class CounterpartyUpdateView(SuccessMessageMixin, UpdateView):
    model = Counterparty
    form_class = CounterpartyForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('partners:counterparty_list')
    success_message = 'Контрагента "%(name)s" оновлено.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редагування: {self.object.name}'
        ctx['back_url'] = self.success_url
        return ctx


class ContractListView(ListView):
    model = Contract
    template_name = 'partners/contract_list.html'
    context_object_name = 'contracts'
    queryset = Contract.objects.select_related('counterparty')


class ContractCreateView(SuccessMessageMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('partners:contract_list')
    success_message = 'Договір №%(number)s створено.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий договір'
        ctx['back_url'] = self.success_url
        return ctx


class ContractUpdateView(SuccessMessageMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'generic_form.html'
    success_url = reverse_lazy('partners:contract_list')
    success_message = 'Договір №%(number)s оновлено.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редагування: договір №{self.object.number}'
        ctx['back_url'] = self.success_url
        return ctx
