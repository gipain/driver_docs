"""Тести fill_ttn() - перевіряють, що заповнена заготовка
містить правильні значення на зафіксованих координатах, включно з
формулою SUM у підсумковому рядку."""
from datetime import date
from decimal import Decimal

import pytest

from fleet.models import Driver, Trailer, Vehicle
from partners.models import Contract, Counterparty
from trips.models import Trip

from .fill_ttn import fill_ttn
from .models import TTN, CargoLine
from .ttn_cells import TTN_CARGO_LINE_ROW, TTN_TOTAL_ROW


@pytest.fixture
def ttn_with_cargo(db):
    carrier = Counterparty.objects.create(
        name='ТОВ "Перевізник"', edrpou='11111111', address='м. Одеса, вул. 1', director='Директор П.',
    )
    sender = Counterparty.objects.create(
        name='ТОВ "Відправник"', edrpou='22222222', address='м. Одеса, вул. 2', director='Директор В.',
    )
    receiver = Counterparty.objects.create(
        name='ТОВ "Одержувач"', edrpou='33333333', address='м. Київ, вул. 3', director='Директор О.',
    )
    contract = Contract.objects.create(counterparty=sender, number='Д-1', date=date(2026, 1, 1))
    driver = Driver.objects.create(
        full_name='Іванов Іван Іванович', license_number='BXP000001', license_expiry=date(2030, 1, 1),
    )
    vehicle = Vehicle.objects.create(
        brand_model='RENAULT MASTER', plate_number='AI1234AA', vehicle_type='вантажний',
        capacity_t=Decimal('2.389'), length_m=Decimal('6.198'), width_m=Decimal('2.470'),
        height_m=Decimal('2.475'), inspection_expiry=date(2030, 1, 1),
    )
    trailer = Trailer.objects.create(brand_model='WIELTON', plate_number='BC5678BC')
    trip = Trip.objects.create(
        contract=contract, driver=driver, vehicle=vehicle, trailer=trailer,
        carrier=carrier, sender=sender, receiver=receiver,
        date=date(2026, 9, 4), loading_address='вул. Млинна, 21-А, м. Миколаїв',
        unloading_address='вул. Радистів, 54, м. Запоріжжя',
        weight_t=Decimal('0.124'), amount_no_vat=Decimal('26209.71'),
        cargo_name='Автозапчастини в асортименті', cargo_unit='шт',
        places_count=9, cargo_packaging='мішки',
    )
    ttn = TTN.objects.create(
        trip=trip, number='НИ-0100', date=trip.date,
        place='м. Миколаїв', accompanying_docs='Видат. накл. НИ-0100',
    )
    CargoLine.objects.create(
        ttn=ttn, name=trip.cargo_name, unit=trip.cargo_unit, qty=trip.places_count,
        unit_price=Decimal('0'), amount=Decimal('31451.65'),
        packaging=trip.cargo_packaging, weight_t=trip.weight_t,
    )
    return ttn


@pytest.mark.django_db
def test_fill_ttn_header_and_signatures(ttn_with_cargo):
    wb = fill_ttn(ttn_with_cargo)
    ws = wb.active
    assert ws['A3'].value == '№ НИ-0100 4 Вересня 2026 р.'
    assert ws['G4'].value == 'м. Миколаїв'
    assert 'RENAULT MASTER' in ws['E6'].value
    assert 'AI1234AA' in ws['E6'].value
    assert ws['AB6'].value == 'BC5678BC'


@pytest.mark.django_db
def test_fill_ttn_matches_ttn_sample_words(ttn_with_cargo):
    wb = fill_ttn(ttn_with_cargo)
    ws = wb.active
    # ті самі числа, що й у наданому зразку НИ-0065 - слова мають збігтись дослівно
    assert ws['F18'].value == "Дев'ять місць"
    assert ws['T18'].value == 'Нуль цілих сто двадцять чотири тисячних'
    assert ws['M22'].value == "Тридцять одна тисяча чотириста п'ятдесят одна гривня шістдесят п'ять копійок"


@pytest.mark.django_db
def test_fill_ttn_vehicle_dimensions(ttn_with_cargo):
    wb = fill_ttn(ttn_with_cargo)
    ws = wb.active
    assert ws['S20'].value == 6.198
    assert ws['AB20'].value == 2.47
    assert ws['AH20'].value == 2.475


@pytest.mark.django_db
def test_fill_ttn_cargo_line_and_total_formula(ttn_with_cargo):
    wb = fill_ttn(ttn_with_cargo)
    ws = wb.active
    row = TTN_CARGO_LINE_ROW
    assert ws[f'C{row}'].value == 'Автозапчастини в асортименті'
    assert ws[f'Z{row}'].value == 9
    assert ws[f'AH{row}'].value == 31451.65
    assert ws[f'AN{row}'].value == 'мішки'

    total_row = TTN_TOTAL_ROW
    assert ws[f'Z{total_row}'].value == f'=SUM(Z{row}:Z{row})'
    assert ws[f'AH{total_row}'].value == f'=SUM(AH{row}:AH{row})'
    assert ws[f'AW{total_row}'].value == f'=SUM(AW{row}:AW{row})'


@pytest.mark.django_db
def test_fill_ttn_no_leftover_template_placeholders(ttn_with_cargo):
    """Жодна з 34 комірок-даних не повинна лишитись порожньою після
    заповнення - інакше заготовка дня 8 і функція дня 10 розійшлися."""
    from .ttn_cells import ALL_DATA_CELLS

    wb = fill_ttn(ttn_with_cargo)
    ws = wb.active
    empty = [c for c in ALL_DATA_CELLS if ws[c].value in (None, '')]
    # sender_signatory/loading_weight і рядок вантажу заповнюються окремо від TTN_CELLS,
    # тому виключно ALL_DATA_CELLS, що не входять у жоден з циклів, тут бути не повинно
    assert empty == []


@pytest.mark.django_db
def test_fill_ttn_zero_places_and_small_fractional_weight(ttn_with_cargo):
    """Межовий випадок дня 12: нульова кількість місць і дуже мала дробова
    вага не повинні ламати заповнення чи текстове представлення чисел."""
    trip = ttn_with_cargo.trip
    trip.places_count = 0
    trip.weight_t = Decimal('0.001')
    trip.save()

    wb = fill_ttn(ttn_with_cargo)
    ws = wb.active
    assert ws['F18'].value == 'Нуль місць'
    assert ws['T18'].value == 'Нуль цілих одна тисячна'


@pytest.mark.django_db
def test_fill_ttn_handles_long_counterparty_name(ttn_with_cargo):
    """Межовий випадок дня 12: назва контрагента на всю довжину поля (255
    символів) не повинна обрізатись чи спричиняти помилку заповнення -
    заготовка не має жорстко заданої довжини тексту в комірці."""
    long_name = 'ТОВ "' + 'Дуже Довга Назва Контрагента ' * 7 + 'Лтд"'
    assert len(long_name) <= 255
    trip = ttn_with_cargo.trip
    trip.carrier.name = long_name
    trip.carrier.save()

    wb = fill_ttn(ttn_with_cargo)
    ws = wb.active
    assert long_name in ws['J10'].value
