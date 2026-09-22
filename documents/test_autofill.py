"""Юніт-тест збірки контексту акту - перевіряє, що
build_act_context() правильно бере суми й текст словами з уже
збереженого запису Act, а рядки - з його ActLine."""
from datetime import date
from decimal import Decimal

import pytest

from core.models import Company
from core.vat import calculate_vat
from fleet.models import Driver, Vehicle
from partners.models import Contract, Counterparty
from trips.models import Trip

from .autofill import build_act_context
from .models import Act, ActLine


@pytest.mark.django_db
def test_build_act_context_matches_saved_act_and_lines():
    counterparty = Counterparty.objects.create(
        name='ТОВ "Замовник"', edrpou='11112222', address='м. Тест, вул. 1',
    )
    company = Company.objects.create(
        name='ТОВ "Виконавець"', edrpou='33334444', address='м. Тест, вул. 2',
        director='Директор Д. Д.',
    )
    contract = Contract.objects.create(counterparty=counterparty, number='Т-1', date=date(2026, 1, 1))
    driver = Driver.objects.create(
        full_name='Водій Тест', license_number='TEST0009', license_expiry=date(2030, 1, 1),
    )
    vehicle = Vehicle.objects.create(
        brand_model='TEST', plate_number='AI0009AA', capacity_t=Decimal('10'),
        length_m=Decimal('8'), width_m=Decimal('2.4'), height_m=Decimal('3'),
        inspection_expiry=date(2030, 1, 1),
    )
    trip = Trip.objects.create(
        contract=contract, driver=driver, vehicle=vehicle,
        carrier=counterparty, sender=counterparty, receiver=counterparty,
        date=date(2026, 6, 1), loading_address='А', unloading_address='Б',
        weight_t=Decimal('5.000'), amount_no_vat=Decimal('1000.00'),
    )
    vat, total = calculate_vat(Decimal('1000.00'))
    act = Act.objects.create(
        number='ОУ-0099', date=date(2026, 6, 2), contract=contract,
        customer=counterparty, executor=company,
        amount_no_vat=Decimal('1000.00'), vat_amount=vat, amount_with_vat=total,
    )
    ActLine.objects.create(act=act, trip=trip, description='А - Б', weight_t=trip.weight_t, amount=trip.amount_no_vat)

    ctx = build_act_context(act)

    assert ctx.number == 'ОУ-0099'
    assert ctx.customer_name == counterparty.name
    assert ctx.executor_name == company.name
    assert ctx.amount_no_vat == Decimal('1000.00')
    assert ctx.vat_amount == vat
    assert ctx.amount_with_vat == total
    assert ctx.amount_with_vat_words == 'Одна тисяча двісті гривень нуль копійок'
    assert len(ctx.lines) == 1
    assert ctx.lines[0].vehicle_plate == 'AI0009AA'
    assert ctx.lines[0].driver_name == 'Водій Тест'
