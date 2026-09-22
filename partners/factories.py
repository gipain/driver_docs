import random

import factory
from faker import Faker

from .models import Counterparty

fake = Faker('uk_UA')

# fake.company() для локалі uk_UA успадковує частину англомовних шаблонів
# базового провайдера Faker ("X, Y and Z", "X Inc") і підставляє в них
# українські прізвища - для демонстраційних даних, які показуються на
# захисті практики, це виглядає недоречно, тому назву компанії будуємо
# власними шаблонами суто українською.
_COMPANY_TEMPLATES = [
    lambda: f'{fake.last_name()}-Логістик',
    lambda: f'{fake.last_name()}-Транс',
    lambda: f'{fake.last_name()} та {fake.last_name()}',
    lambda: f'{fake.last_name()}-Карго',
]


def _uk_company_name() -> str:
    return random.choice(_COMPANY_TEMPLATES)()


class CounterpartyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Counterparty
        django_get_or_create = ('edrpou',)

    name = factory.LazyFunction(lambda: f'ТОВ "{_uk_company_name()}"')
    edrpou = factory.Sequence(lambda n: str(20000000 + n))
    inn = factory.LazyAttribute(lambda o: o.edrpou + '015')
    address = factory.LazyFunction(fake.address)
    bank_details = factory.LazyFunction(lambda: 'UA' + str(fake.random_number(digits=27, fix_len=True)))
    director = factory.LazyFunction(fake.name)
    phone = factory.LazyFunction(fake.phone_number)
