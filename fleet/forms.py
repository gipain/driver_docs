from django import forms

from .models import Driver, Trailer, Vehicle


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['full_name', 'license_number', 'license_expiry']
        widgets = {'license_expiry': forms.DateInput(attrs={'type': 'date'})}


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'brand_model', 'plate_number', 'vehicle_type', 'capacity_t',
            'length_m', 'width_m', 'height_m', 'inspection_expiry',
        ]
        widgets = {'inspection_expiry': forms.DateInput(attrs={'type': 'date'})}


class TrailerForm(forms.ModelForm):
    class Meta:
        model = Trailer
        fields = ['brand_model', 'plate_number']
