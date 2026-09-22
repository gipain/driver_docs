from django.contrib import admin

from .models import Contract, Counterparty


@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'edrpou', 'director', 'phone')
    search_fields = ('name', 'edrpou')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'counterparty')
    list_filter = ('date',)
    search_fields = ('number', 'counterparty__name')
    autocomplete_fields = ('counterparty',)
