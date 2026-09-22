"""Тести реєстру ТТН і зведеного звіту - реальна агрегація по
базі замість макета."""
from datetime import date
from decimal import Decimal

import pytest

from core.vat import calculate_vat
from fleet.models import Driver, Vehicle
from partners.models import Contract, Counterparty
from trips.models import Trip

from .models import TTN
from .registry import build_monthly_registry_workbook
from .summary import build_summary


@pytest.fixture
def two_counterparties_setup(db):
    cp_a = Counterparty.objects.create(name='ТОВ "Альфа"', edrpou='10000001', address='м. А')
    cp_b = Counterparty.objects.create(name='ТОВ "Бета"', edrpou='10000002', address='м. Б')
    contract_a = Contract.objects.create(counterparty=cp_a, number='ДА-1', date=date(2026, 1, 1))
    contract_b = Contract.objects.create(counterparty=cp_b, number='ДБ-1', date=date(2026, 1, 1))
    driver = Driver.objects.create(full_name='Водій Т.', license_number='REG0001', license_expiry=date(2030, 1, 1))
    vehicle = Vehicle.objects.create(
        brand_model='TEST', plate_number='AI0002AA', capacity_t=Decimal('20'),
        length_m=Decimal('8'), width_m=Decimal('2.4'), height_m=Decimal('3'),
        inspection_expiry=date(2030, 1, 1),
    )

    def make_trip(contract, counterparty, d, amount, confirm=True, cargo='Вантаж'):
        trip = Trip.objects.create(
            contract=contract, driver=driver, vehicle=vehicle,
            carrier=counterparty, sender=counterparty, receiver=counterparty,
            date=d, loading_address='А', unloading_address='Б',
            weight_t=Decimal('1.000'), amount_no_vat=amount, cargo_name=cargo,
        )
        if confirm:
            trip.confirm()
        return trip

    t1 = make_trip(contract_a, cp_a, date(2026, 6, 5), Decimal('1000.00'))
    t2 = make_trip(contract_a, cp_a, date(2026, 6, 10), Decimal('2000.00'))
    t3 = make_trip(contract_b, cp_b, date(2026, 6, 15), Decimal('500.00'))
    outside = make_trip(contract_a, cp_a, date(2026, 7, 1), Decimal('999.00'))  # поза періодом
    draft = make_trip(contract_a, cp_a, date(2026, 6, 20), Decimal('777.00'), confirm=False)  # чернетка

    TTN.objects.create(trip=t1, number='НИ-0201', date=t1.date, place='м. Тест')
    TTN.objects.create(trip=t2, number='НИ-0202', date=t2.date, place='м. Тест')
    TTN.objects.create(trip=t3, number='НИ-0203', date=t3.date, place='м. Тест')
    TTN.objects.create(trip=outside, number='НИ-0204', date=outside.date, place='м. Тест')

    return {'cp_a': cp_a, 'cp_b': cp_b, 'trips': [t1, t2, t3, outside]}


@pytest.mark.django_db
def test_registry_includes_only_period_and_has_total_formula(two_counterparties_setup):
    wb = build_monthly_registry_workbook(date(2026, 6, 1), date(2026, 6, 30))
    ws = wb.active
    numbers = [ws.cell(row=r, column=2).value for r in range(2, ws.max_row + 1)]
    assert 'НИ-0201' in numbers
    assert 'НИ-0202' in numbers
    assert 'НИ-0203' in numbers
    assert 'НИ-0204' not in numbers  # поза періодом

    last_data_row = 1 + 3
    total_row = last_data_row + 1
    assert ws.cell(row=total_row, column=6).value == f'=SUM(F2:F{last_data_row})'
    assert ws.cell(row=total_row, column=7).value == f'=SUM(G2:G{last_data_row})'


@pytest.mark.django_db
def test_summary_groups_by_counterparty_correctly(two_counterparties_setup):
    rows = build_summary(date(2026, 6, 1), date(2026, 6, 30), group_by='counterparty')
    by_name = {r['name']: r for r in rows}

    assert by_name['ТОВ "Альфа"']['trips'] == 2
    assert by_name['ТОВ "Альфа"']['amount_no_vat'] == Decimal('3000.00')
    assert by_name['ТОВ "Бета"']['trips'] == 1
    assert by_name['ТОВ "Бета"']['amount_no_vat'] == Decimal('500.00')

    expected_vat, expected_total = calculate_vat(Decimal('3000.00'))
    assert by_name['ТОВ "Альфа"']['vat_amount'] == expected_vat
    assert by_name['ТОВ "Альфа"']['amount_with_vat'] == expected_total


@pytest.mark.django_db
def test_summary_excludes_unconfirmed_and_out_of_period_trips(two_counterparties_setup):
    rows = build_summary(date(2026, 6, 1), date(2026, 6, 30), group_by='counterparty')
    total_trips = sum(r['trips'] for r in rows)
    assert total_trips == 3  # чернетки й позаперіодні рейси тут не рахуються


@pytest.mark.django_db
def test_registry_keeps_long_counterparty_name_intact(two_counterparties_setup):
    """Межовий випадок дня 12: довга назва контрагента не повинна
    обрізатись у комірці реєстру - фіксована ширина колонки впливає лише
    на візуальне відображення при друку, не на самі дані."""
    long_name = 'ТОВ "' + 'Дуже Довга Назва Контрагента ' * 7 + 'Лтд"'
    cp_a = two_counterparties_setup['cp_a']
    cp_a.name = long_name
    cp_a.save()

    wb = build_monthly_registry_workbook(date(2026, 6, 1), date(2026, 6, 30))
    ws = wb.active
    names = [ws.cell(row=r, column=3).value for r in range(2, ws.max_row)]
    assert long_name in names
