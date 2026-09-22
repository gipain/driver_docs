"""Автозаповнення полів ТТН і акту на основі рейсу: габарити
автомобіля й реквізити контрагентів беруться напряму із зв'язаних
записів, а суми і текст словами - рахуються."""
from dataclasses import dataclass
from decimal import Decimal

from core.number_to_words import fractional_to_words_uk, money_to_words_uk
from core.vat import calculate_vat


@dataclass
class TTNContext:
    vehicle_brand_model: str
    vehicle_length_m: Decimal
    vehicle_width_m: Decimal
    vehicle_height_m: Decimal
    vehicle_capacity_t: Decimal
    carrier_name: str
    carrier_edrpou: str
    sender_name: str
    sender_edrpou: str
    receiver_name: str
    receiver_edrpou: str
    driver_full_name: str
    driver_license_number: str
    weight_words: str
    amount_no_vat: Decimal
    vat_amount: Decimal
    amount_with_vat: Decimal
    amount_with_vat_words: str


def build_ttn_context(trip) -> TTNContext:
    """Збирає всі дані, потрібні для заповнення ТТН, з уже пов'язаних
    записів рейсу - жодне з цих полів користувач вдруге не вводить."""
    vat_amount, amount_with_vat = calculate_vat(trip.amount_no_vat)
    return TTNContext(
        vehicle_brand_model=trip.vehicle.brand_model,
        vehicle_length_m=trip.vehicle.length_m,
        vehicle_width_m=trip.vehicle.width_m,
        vehicle_height_m=trip.vehicle.height_m,
        vehicle_capacity_t=trip.vehicle.capacity_t,
        carrier_name=trip.carrier.name,
        carrier_edrpou=trip.carrier.edrpou,
        sender_name=trip.sender.name,
        sender_edrpou=trip.sender.edrpou,
        receiver_name=trip.receiver.name,
        receiver_edrpou=trip.receiver.edrpou,
        driver_full_name=trip.driver.full_name,
        driver_license_number=trip.driver.license_number,
        weight_words=fractional_to_words_uk(trip.weight_t),
        amount_no_vat=trip.amount_no_vat,
        vat_amount=vat_amount,
        amount_with_vat=amount_with_vat,
        amount_with_vat_words=money_to_words_uk(amount_with_vat),
    )


@dataclass
class ActLineView:
    route_text: str
    vehicle_plate: str
    trailer_plate: str
    driver_name: str
    weight_t: Decimal
    amount: Decimal


@dataclass
class ActContext:
    number: str
    date: str
    place: str
    contract_number: str
    contract_date: str
    customer_name: str
    customer_representative: str
    customer_edrpou: str
    customer_inn: str
    customer_address: str
    customer_phone: str
    executor_name: str
    executor_representative: str
    executor_edrpou: str
    executor_inn: str
    executor_address: str
    executor_phone: str
    executor_bank_details: str
    lines: list
    amount_no_vat: Decimal
    amount_no_vat_words: str
    vat_amount: Decimal
    amount_with_vat: Decimal
    amount_with_vat_words: str


def build_act_context(act) -> ActContext:
    """Збирає дані для друкованого акту здачі-прийняття робіт із уже
    збереженого запису Act і його рядків ActLine - формат полів точно за
    наданим зразком акту №ОУ-0010 (шапка «ЗАТВЕРДЖУЮ» x2, опис рейсу
    одним реченням, підсумки трьома сумами)."""
    lines = [
        ActLineView(
            route_text=f'{line.trip.loading_address} - {line.trip.unloading_address}',
            vehicle_plate=line.trip.vehicle.plate_number,
            trailer_plate=line.trip.trailer.plate_number if line.trip.trailer else '',
            driver_name=line.trip.driver.full_name,
            weight_t=line.weight_t,
            amount=line.amount,
        )
        for line in act.lines.select_related(
            'trip', 'trip__vehicle', 'trip__trailer', 'trip__driver',
        ).all()
    ]
    return ActContext(
        number=act.number,
        date=f'{act.date:%d.%m.%Y}',
        place=act.executor.address,
        contract_number=act.contract.number,
        contract_date=f'{act.contract.date:%d.%m.%Y}',
        customer_name=act.customer.name,
        customer_representative=act.customer.director,
        customer_edrpou=act.customer.edrpou,
        customer_inn=act.customer.inn,
        customer_address=act.customer.address,
        customer_phone=act.customer.phone,
        executor_name=act.executor.name,
        executor_representative=act.executor.director,
        executor_edrpou=act.executor.edrpou,
        executor_inn=act.executor.inn,
        executor_address=act.executor.address,
        executor_phone=act.executor.phone,
        executor_bank_details=act.executor.bank_details,
        lines=lines,
        amount_no_vat=act.amount_no_vat,
        amount_no_vat_words=money_to_words_uk(act.amount_no_vat),
        vat_amount=act.vat_amount,
        amount_with_vat=act.amount_with_vat,
        amount_with_vat_words=money_to_words_uk(act.amount_with_vat),
    )
