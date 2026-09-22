from django import forms

from .models import Contract, Counterparty


class CounterpartyForm(forms.ModelForm):
    class Meta:
        model = Counterparty
        fields = ['name', 'edrpou', 'inn', 'address', 'bank_details', 'director', 'phone']


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['counterparty', 'number', 'date', 'valid_until']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }
