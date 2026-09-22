"""Тести пакетної генерації - весь пакет через 
Django-клієнт: щасливий шлях (усі рейси без помилок) і навмисно зіпсований
випадок (одному рейсу не вдається сформувати ТТН, решта пакета все одно
генерується, а помилка потрапляє в errors.txt всередині архіву)."""
import io
import zipfile
from datetime import date
from decimal import Decimal

import pytest

from core.models import Company
from fleet.models import Driver, Vehicle
from partners.models import Contract, Counterparty
from trips.models import Trip


@pytest.fixture
def batch_setup(db):
    Company.objects.create(
        name='ТОВ "Виконавець"', edrpou='55555555', address='м. Тест',
        director='Директор Д.',
    )
    counterparty = Counterparty.objects.create(name='ТОВ "Клієнт"', edrpou='66666666', address='м. Тест')
    contract = Contract.objects.create(counterparty=counterparty, number='ДБ-1', date=date(2026, 1, 1))
    driver = Driver.objects.create(full_name='Водій Б.', license_number='BATCH001', license_expiry=date(2030, 1, 1))
    vehicle = Vehicle.objects.create(
        brand_model='TEST', plate_number='AI0003AA', capacity_t=Decimal('20'),
        length_m=Decimal('8'), width_m=Decimal('2.4'), height_m=Decimal('3'),
        inspection_expiry=date(2030, 1, 1),
    )
    trips = []
    for i in range(2):
        trip = Trip.objects.create(
            contract=contract, driver=driver, vehicle=vehicle,
            carrier=counterparty, sender=counterparty, receiver=counterparty,
            date=date(2026, 6, 5 + i), loading_address='А', unloading_address='Б',
            weight_t=Decimal('1.000'), amount_no_vat=Decimal('1000.00'),
            cargo_name='Тестовий вантаж',
        )
        trip.confirm()
        trips.append(trip)
    return trips


@pytest.mark.django_db
def test_batch_generate_happy_path(client, batch_setup):
    response = client.post(
        '/registry/batch/', {'start': '2026-06-01', 'end': '2026-06-30'},
    )
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/zip'

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    assert 'manifest.txt' in names
    assert 'errors.txt' not in names
    assert sum(1 for n in names if n.startswith('TTN/') and n.endswith('.xlsx')) == 2
    assert any(n.startswith('registry_') for n in names)
    assert any(n.startswith('summary_') for n in names)

    manifest = zf.read('manifest.txt').decode('utf-8')
    assert 'Помилок: 0' in manifest


@pytest.mark.django_db
def test_batch_generate_partial_failure_is_logged_and_others_still_succeed(client, batch_setup, monkeypatch):
    broken_trip_pk = batch_setup[0].pk
    from documents import views as documents_views

    original = documents_views._generate_ttn_for_trip

    def flaky(trip):
        if trip.pk == broken_trip_pk:
            raise RuntimeError('навмисно зіпсований рейс для тесту')
        return original(trip)

    monkeypatch.setattr(documents_views, '_generate_ttn_for_trip', flaky)

    response = client.post(
        '/registry/batch/', {'start': '2026-06-01', 'end': '2026-06-30'},
    )
    assert response.status_code == 200

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    assert 'errors.txt' in names
    errors_text = zf.read('errors.txt').decode('utf-8')
    assert f'Рейс №{broken_trip_pk}' in errors_text
    assert 'навмисно зіпсований рейс' in errors_text

    # другий (справний) рейс усе одно має отримати свій ТТН у пакеті
    assert sum(1 for n in names if n.startswith('TTN/') and n.endswith('.xlsx')) == 1

    manifest = zf.read('manifest.txt').decode('utf-8')
    assert 'Помилок: 1' in manifest
