import pytest

from documents.numbering import compute_next_number, next_act_number, next_ttn_number


def test_compute_next_number_empty_starts_at_1():
    assert compute_next_number([], 'НИ') == 'НИ-0001'


def test_compute_next_number_continues_sequence():
    assert compute_next_number(['НИ-0001', 'НИ-0002'], 'НИ') == 'НИ-0003'


def test_compute_next_number_takes_max_not_count():
    # навмисний розрив у нумерації - береться максимум, а не кількість записів
    assert compute_next_number(['НИ-0001', 'НИ-0005'], 'НИ') == 'НИ-0006'


def test_compute_next_number_ignores_other_prefix():
    assert compute_next_number(['ОУ-0010', 'ОУ-0011'], 'НИ') == 'НИ-0001'


def test_compute_next_number_ignores_malformed_values():
    assert compute_next_number(['НИ-abc', 'щось інше', None, 'НИ-0007'], 'НИ') == 'НИ-0008'


def test_compute_next_number_matches_real_example_from_ttn():
    # реальний зразок з наданого документа - НИ-0065
    assert compute_next_number(['НИ-0065'], 'НИ') == 'НИ-0066'


def test_compute_next_number_matches_real_example_from_act():
    # реальний зразок з наданого документа - ОУ-0010
    assert compute_next_number(['ОУ-0010'], 'ОУ') == 'ОУ-0011'


# next_ttn_number()/next_act_number() - тонкі обгортки над цією ж функцією,
# що звертаються вже до реальної бази (TTN.objects/Act.objects). Спочатку
# їх не тестувала: pytest-django для тестів з позначкою django_db створює
# окрему тестову базу (CREATE DATABASE test_driver_docs), а робочий
# користувач driver_docs_user права CREATEDB не мав. Після того, як
# користувачу видали ALTER ROLE driver_docs_user CREATEDB, додала й ці
# два інтеграційні тести - вони створюють мінімальний ланцюжок реальних
# записів (контрагент → договір → водій → авто → рейс → ТТН) у тестовій
# базі й перевіряють, що функція справді читає чергу номерів із бази,
# а не лише з чистого списку рядків.


@pytest.mark.django_db
def test_next_ttn_number_empty_db():
    assert next_ttn_number() == 'НИ-0001'


@pytest.mark.django_db
def test_next_act_number_empty_db():
    assert next_act_number() == 'ОУ-0001'


@pytest.mark.django_db
def test_next_ttn_number_increments_after_real_record():
    from documents.models import TTN
    from fleet.models import Driver, Vehicle
    from partners.models import Contract, Counterparty
    from trips.models import Trip

    counterparty = Counterparty.objects.create(
        name='ТОВ "Тестовий Контрагент"', edrpou='11112222', address='м. Тест, вул. Тестова, 1',
    )
    contract = Contract.objects.create(counterparty=counterparty, number='Т-1', date='2026-01-01')
    driver = Driver.objects.create(
        full_name='Тестовий Тест Тестович', license_number='TEST0001', license_expiry='2030-01-01',
    )
    vehicle = Vehicle.objects.create(
        brand_model='TEST MODEL', plate_number='AI0001AA', capacity_t=10,
        length_m=8, width_m=2.4, height_m=3, inspection_expiry='2030-01-01',
    )
    trip = Trip.objects.create(
        contract=contract, driver=driver, vehicle=vehicle,
        carrier=counterparty, sender=counterparty, receiver=counterparty,
        date='2026-01-01', loading_address='А', unloading_address='Б',
        weight_t=1, amount_no_vat=100,
    )
    TTN.objects.create(trip=trip, number='НИ-0001', date='2026-01-01', place='м. Тест')

    assert next_ttn_number() == 'НИ-0002'


@pytest.mark.django_db
def test_next_act_number_increments_after_real_record():
    from documents.models import Act
    from partners.models import Contract, Counterparty
    from core.models import Company

    counterparty = Counterparty.objects.create(
        name='ТОВ "Тестовий Замовник"', edrpou='33334444', address='м. Тест, вул. Тестова, 2',
    )
    contract = Contract.objects.create(counterparty=counterparty, number='Т-2', date='2026-01-01')
    company = Company.objects.create(
        name='ТОВ "Тестовий Виконавець"', edrpou='55556666', address='м. Тест, вул. Тестова, 3',
        director='Директор Д. Д.',
    )
    Act.objects.create(
        number='ОУ-0010', date='2026-01-01', contract=contract, customer=counterparty,
        executor=company, amount_no_vat=100, vat_amount=20, amount_with_vat=120,
    )

    assert next_act_number() == 'ОУ-0011'
