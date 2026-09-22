from django.contrib import admin

from .models import TTN, Act, ActLine, CargoLine


class CargoLineInline(admin.TabularInline):
    model = CargoLine
    extra = 1


@admin.register(TTN)
class TTNAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'trip', 'place')
    search_fields = ('number',)
    autocomplete_fields = ('trip',)
    inlines = [CargoLineInline]


class ActLineInline(admin.TabularInline):
    model = ActLine
    extra = 1
    autocomplete_fields = ('trip',)


@admin.register(Act)
class ActAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'customer', 'executor', 'amount_with_vat')
    search_fields = ('number',)
    autocomplete_fields = ('contract', 'customer', 'executor')
    inlines = [ActLineInline]
