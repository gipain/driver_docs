from django.contrib import admin
from django.utils.html import format_html

from .models import Driver, Trailer, Vehicle


def status_badge(is_expired):
    if is_expired:
        return format_html(
            '<span style="color:#fff;background:#c0392b;padding:2px 8px;'
            'border-radius:3px;font-size:12px;">прострочено</span>'
        )
    return format_html(
        '<span style="color:#fff;background:#27ae60;padding:2px 8px;'
        'border-radius:3px;font-size:12px;">чинне</span>'
    )


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'license_number', 'license_expiry', 'license_status')
    search_fields = ('full_name', 'license_number')

    @admin.display(description='статус посвідчення')
    def license_status(self, obj):
        return status_badge(obj.is_license_expired)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'plate_number', 'brand_model', 'capacity_t', 'inspection_expiry', 'inspection_status',
    )
    search_fields = ('plate_number', 'brand_model')

    @admin.display(description='статус техогляду')
    def inspection_status(self, obj):
        return status_badge(obj.is_inspection_expired)


@admin.register(Trailer)
class TrailerAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'brand_model')
    search_fields = ('plate_number', 'brand_model')
