from django import forms

from .models import Trip


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'contract', 'driver', 'vehicle', 'trailer',
            'carrier', 'sender', 'receiver',
            'date', 'loading_address', 'unloading_address', 'route_text',
            'weight_t', 'amount_no_vat',
            'cargo_name', 'cargo_unit', 'places_count', 'cargo_packaging',
        ]
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}
        help_texts = {
            'carrier': 'Контрагент у ролі перевізника для цього рейсу.',
            'sender': 'Контрагент у ролі вантажовідправника.',
            'receiver': 'Контрагент у ролі вантажоодержувача.',
        }
