from decimal import Decimal

import pytest

from core.vat import calculate_vat


@pytest.mark.parametrize('amount_no_vat,expected_vat,expected_total', [
    (Decimal('100.00'), Decimal('20.00'), Decimal('120.00')),
    (Decimal('26209.71'), Decimal('5241.94'), Decimal('31451.65')),  #звірено з ТТН №НИ-0065
    (Decimal('0.01'), Decimal('0.00'), Decimal('0.01')),
    (Decimal('0.03'), Decimal('0.01'), Decimal('0.04')),
    (Decimal('10.005'), Decimal('2.00'), Decimal('12.01')),  # межове округлення копійки
    (Decimal('12.525'), Decimal('2.51'), Decimal('15.04')),  # округлення вгору і в ПДВ, і в сумі з ПДВ
    (Decimal('10.004'), Decimal('2.00'), Decimal('12.00')),  # тисячна частка нижче межі - округлення вниз
])
def test_calculate_vat(amount_no_vat, expected_vat, expected_total):
    vat, total = calculate_vat(amount_no_vat)
    assert vat == expected_vat
    assert total == expected_total
