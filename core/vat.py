"""Авторозрахунок ПДВ 20% із округленням до копійки"""
from decimal import ROUND_HALF_UP, Decimal

VAT_RATE = Decimal('0.20')
_CENT = Decimal('0.01')


def calculate_vat(amount_no_vat: Decimal) -> tuple[Decimal, Decimal]:
    """Повертає (сума_ПДВ, сума_з_ПДВ) для суми без ПДВ, округлені до
    копійки арифметично (0.5 копійки і більше - вгору)."""
    amount_no_vat = Decimal(amount_no_vat)
    vat_amount = (amount_no_vat * VAT_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)
    amount_with_vat = (amount_no_vat + vat_amount).quantize(_CENT, rounding=ROUND_HALF_UP)
    return vat_amount, amount_with_vat
