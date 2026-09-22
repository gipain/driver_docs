import random

import factory
from faker import Faker

from .models import Driver, Trailer, Vehicle

fake = Faker('uk_UA')

# Літери, які на українських номерах виглядають однаково в кирилиці й латиниці
PLATE_LETTERS = 'ABEIKMHOPCTX'

TRUCK_MODELS = ['RENAULT MASTER', 'MAN TGX', 'MERCEDES ACTROS', 'DAF XF', 'VOLVO FH', 'IVECO STRALIS']
TRAILER_MODELS = ['SCHMITZ CARGOBULL', 'KRONE', 'WIELTON', 'KOGEL']


def random_plate():
    letter = lambda: random.choice(PLATE_LETTERS)
    return f'{letter()}{letter()}{random.randint(1000, 9999)}{letter()}{letter()}'


class DriverFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Driver
        django_get_or_create = ('license_number',)

    full_name = factory.LazyFunction(fake.name)
    license_number = factory.Sequence(lambda n: f'BXP{100000 + n}')
    license_expiry = factory.LazyFunction(
        lambda: fake.date_between(start_date='+30d', end_date='+5y')
    )


class VehicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicle
        django_get_or_create = ('plate_number',)

    brand_model = factory.LazyFunction(lambda: random.choice(TRUCK_MODELS))
    plate_number = factory.LazyFunction(random_plate)
    vehicle_type = 'вантажний'
    capacity_t = factory.LazyFunction(lambda: round(random.uniform(1.5, 20), 3))
    length_m = factory.LazyFunction(lambda: round(random.uniform(5, 13.6), 3))
    width_m = factory.LazyFunction(lambda: round(random.uniform(2.2, 2.55), 3))
    height_m = factory.LazyFunction(lambda: round(random.uniform(2.3, 4.0), 3))
    inspection_expiry = factory.LazyFunction(
        lambda: fake.date_between(start_date='+10d', end_date='+2y')
    )


class TrailerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trailer
        django_get_or_create = ('plate_number',)

    brand_model = factory.LazyFunction(lambda: random.choice(TRAILER_MODELS))
    plate_number = factory.LazyFunction(random_plate)
