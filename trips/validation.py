"""Алгоритми перевірки рейсу перед підтвердженням (день 7) - усі функції
повертають список текстів помилок (порожній список - усе гаразд), щоб
їх було зручно і показати користувачу, і покрити тестами окремо."""
from decimal import Decimal

from core.vat import calculate_vat

# Поля, які обов'язково мають бути заповнені перед підтвердженням рейсу -
# без них неможливо сформувати ТТН за Додатком 7 Правил перевезень
# вантажів автомобільним транспортом.
REQUIRED_TRIP_FIELDS = [
    'contract', 'driver', 'vehicle', 'carrier', 'sender', 'receiver',
    'date', 'loading_address', 'unloading_address', 'weight_t', 'amount_no_vat',
    'cargo_name',
]


def validate_required_fields(trip) -> list[str]:
    """Перевірка повноти обов'язкових реквізитів ТТН - жодне поле форми
    №1-ТН не залишається порожнім при спробі підтвердити документ."""
    errors = []
    for field_name in REQUIRED_TRIP_FIELDS:
        value = getattr(trip, field_name, None)
        if value in (None, ''):
            verbose_name = trip._meta.get_field(field_name).verbose_name
            errors.append(f'Не заповнено обов’язкове поле «{verbose_name}».')
    return errors


def validate_documents_validity(trip) -> list[str]:
    """Перевірка дії посвідчення водія й техогляду авто саме на дату
    рейсу (а не на сьогодні), і що договір ще діє на цю дату."""
    errors = []
    if trip.driver_id and trip.date and trip.driver.license_expiry < trip.date:
        errors.append(
            f'Посвідчення водія {trip.driver.full_name} прострочене '
            f'на дату рейсу ({trip.driver.license_expiry:%d.%m.%Y}).'
        )
    if trip.vehicle_id and trip.date and trip.vehicle.inspection_expiry < trip.date:
        errors.append(
            f'Техогляд автомобіля {trip.vehicle.plate_number} прострочений '
            f'на дату рейсу ({trip.vehicle.inspection_expiry:%d.%m.%Y}).'
        )
    if trip.contract_id and trip.contract.valid_until and trip.date and trip.contract.valid_until < trip.date:
        errors.append(
            f'Договір №{trip.contract.number} не діє на дату рейсу '
            f'(діяв до {trip.contract.valid_until:%d.%m.%Y}).'
        )
    return errors


def validate_capacity(trip) -> list[str]:
    """Маса брутто рейсу не повинна перевищувати вантажопідйомність
    обраного автомобіля."""
    if trip.vehicle_id and trip.weight_t is not None and trip.weight_t > trip.vehicle.capacity_t:
        return [
            f'Маса рейсу ({trip.weight_t} т) перевищує вантажопідйомність '
            f'автомобіля {trip.vehicle.plate_number} ({trip.vehicle.capacity_t} т).'
        ]
    return []


def validate_amount_consistency(amount_no_vat: Decimal, vat_amount: Decimal, amount_with_vat: Decimal) -> list[str]:
    """сума_з_ПДВ має дорівнювати сума_без_ПДВ x 1.2 (з округленням до
    копійки) - та сама формула, що й в core.vat.calculate_vat."""
    expected_vat, expected_total = calculate_vat(amount_no_vat)
    errors = []
    if vat_amount != expected_vat:
        errors.append(f'ПДВ вказано {vat_amount}, а має бути {expected_vat}.')
    if amount_with_vat != expected_total:
        errors.append(f'Сума з ПДВ вказана {amount_with_vat}, а має бути {expected_total}.')
    return errors


def validate_act_amount_matches_trips(act) -> list[str]:
    """Сума в акті має збігатися із сумою пов'язаних рейсів (через рядки
    ActLine)."""
    trips_total = sum(
        (line.trip.amount_no_vat for line in act.lines.select_related('trip').all()),
        Decimal('0'),
    )
    if act.amount_no_vat != trips_total:
        return [
            f'Сума акту без ПДВ ({act.amount_no_vat}) не збігається із сумою '
            f'пов’язаних рейсів ({trips_total}).'
        ]
    return []


def validate_trip_for_confirmation(trip) -> list[str]:
    """Повний набір перевірок перед підтвердженням рейсу - викликається
    з Trip.confirm()."""
    errors = []
    errors += validate_required_fields(trip)
    errors += validate_documents_validity(trip)
    errors += validate_capacity(trip)
    return errors
