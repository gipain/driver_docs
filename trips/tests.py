"""Юніт-тести алгоритмів перевірки рейсу (день 7) - окремо валідні й
невалідні кейси для кожної перевірки, плюс перевірка того, що
Trip.confirm() дійсно блокує підтвердження, коли перевірки не пройдені."""
from datetime import date
from decimal import Decimal

import pytest

from core.vat import calculate_vat
from documents.models import Act, ActLine
from fleet.models import Driver, Trailer, Vehicle
from partners.models import Contract, Counterparty
from trips.models import Trip
from trips.validation import (
    validate_act_amount_matches_trips,
    validate_amount_consistency,
    validate_capacity,
    validate_documents_validity,
    validate_required_fields,
    validate_trip_for_confirmation,
)


@pytest.fixture
def counterparty(db):
    return Counterparty.objects.create(name='ТОВ "Тест"', edrpou='11112222', address='м. Тест')


@pytest.fixture
def contract(db, counterparty):
    return Contract.objects.create(counterparty=counterparty, number='Т-1', date=date(2026, 1, 1))


@pytest.fixture
def driver(db):
    return Driver.objects.create(
        full_name='Тестовий Водій', license_number='TEST0001',
        license_expiry=date(2030, 1, 1),
    )


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.create(
        brand_model='TEST MODEL', plate_number='AI0001AA', capacity_t=Decimal('10.000'),
        length_m=Decimal('8.000'), width_m=Decimal('2.400'), height_m=Decimal('3.000'),
        inspection_expiry=date(2030, 1, 1),
    )


@pytest.fixture
def valid_trip(db, contract, driver, vehicle, counterparty):
    return Trip.objects.create(
        contract=contract, driver=driver, vehicle=vehicle,
        carrier=counterparty, sender=counterparty, receiver=counterparty,
        date=date(2026, 6, 1), loading_address='А', unloading_address='Б',
        weight_t=Decimal('5.000'), amount_no_vat=Decimal('1000.00'),
        cargo_name='Тестовий вантаж',
    )


def test_validate_required_fields_valid_trip_has_no_errors(valid_trip):
    assert validate_required_fields(valid_trip) == []


def test_validate_required_fields_missing_addresses(valid_trip):
    valid_trip.loading_address = ''
    assert any('пункт навантаження' in e.lower() for e in validate_required_fields(valid_trip))


def test_validate_documents_validity_all_current(valid_trip):
    assert validate_documents_validity(valid_trip) == []


def test_validate_documents_validity_expired_license_on_trip_date(valid_trip, driver):
    driver.license_expiry = date(2026, 1, 1)  # раніше дати рейсу (2026-06-01)
    driver.save()
    errors = validate_documents_validity(valid_trip)
    assert any('посвідчення' in e.lower() for e in errors)


def test_validate_documents_validity_expired_inspection_on_trip_date(valid_trip, vehicle):
    vehicle.inspection_expiry = date(2026, 1, 1)
    vehicle.save()
    errors = validate_documents_validity(valid_trip)
    assert any('техогляд' in e.lower() for e in errors)


def test_validate_documents_validity_contract_expired_before_trip(valid_trip, contract):
    contract.valid_until = date(2026, 1, 1)  # раніше дати рейсу
    contract.save()
    errors = validate_documents_validity(valid_trip)
    assert any('договір' in e.lower() for e in errors)


def test_validate_documents_validity_contract_without_end_date_is_fine(valid_trip):
    # valid_until не задано - договір безстроковий, помилки бути не повинно
    assert validate_documents_validity(valid_trip) == []


def test_validate_capacity_within_limit(valid_trip):
    assert validate_capacity(valid_trip) == []


def test_validate_capacity_exceeded(valid_trip):
    valid_trip.weight_t = Decimal('20.000')  # більше за вантажопідйомність 10 т
    assert len(validate_capacity(valid_trip)) == 1


def test_validate_amount_consistency_correct():
    vat, total = calculate_vat(Decimal('1000.00'))
    assert validate_amount_consistency(Decimal('1000.00'), vat, total) == []


def test_validate_amount_consistency_wrong_vat():
    errors = validate_amount_consistency(Decimal('1000.00'), Decimal('999.00'), Decimal('1999.00'))
    assert len(errors) == 2


def test_validate_trip_for_confirmation_valid_trip(valid_trip):
    assert validate_trip_for_confirmation(valid_trip) == []


def test_trip_confirm_succeeds_for_valid_trip(valid_trip):
    valid_trip.confirm()
    valid_trip.refresh_from_db()
    assert valid_trip.status == Trip.Status.CONFIRMED
    assert valid_trip.status_logs.count() == 1


def test_trip_confirm_blocked_for_expired_license(valid_trip, driver):
    driver.license_expiry = date(2026, 1, 1)
    driver.save()
    with pytest.raises(ValueError, match='Посвідчення'):
        valid_trip.confirm()
    valid_trip.refresh_from_db()
    assert valid_trip.status == Trip.Status.DRAFT
    assert valid_trip.status_logs.count() == 0


def test_trip_confirm_blocked_for_overweight(valid_trip):
    valid_trip.weight_t = Decimal('99.000')
    valid_trip.save()
    with pytest.raises(ValueError, match='вантажопідйомність'):
        valid_trip.confirm()


def test_validate_act_amount_matches_trips(db, contract, counterparty, valid_trip):
    from core.models import Company

    company = Company.objects.create(
        name='ТОВ "Виконавець"', edrpou='99998888', address='м. Тест', director='Директор',
    )
    act = Act.objects.create(
        number='ОУ-0001', date=date(2026, 6, 5), contract=contract,
        customer=counterparty, executor=company,
        amount_no_vat=valid_trip.amount_no_vat, vat_amount=Decimal('200.00'),
        amount_with_vat=Decimal('1200.00'),
    )
    ActLine.objects.create(
        act=act, trip=valid_trip, description='Перевезення',
        weight_t=valid_trip.weight_t, amount=valid_trip.amount_no_vat,
    )
    assert validate_act_amount_matches_trips(act) == []

    act.amount_no_vat = Decimal('1.00')
    act.save()
    assert len(validate_act_amount_matches_trips(act)) == 1
