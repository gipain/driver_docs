from django.contrib import admin

from .models import Trip, TripStatusLog


class TripStatusLogInline(admin.TabularInline):
    model = TripStatusLog
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'date', 'driver', 'vehicle', 'carrier', 'sender', 'receiver',
        'status', 'amount_no_vat',
    )
    list_filter = ('status', 'date')
    search_fields = ('driver__full_name', 'vehicle__plate_number')
    autocomplete_fields = (
        'contract', 'driver', 'vehicle', 'trailer', 'carrier', 'sender', 'receiver',
    )
    inlines = [TripStatusLogInline]
