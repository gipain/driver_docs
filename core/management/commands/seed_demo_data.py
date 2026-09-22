from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Company
from fleet.factories import DriverFactory, TrailerFactory, VehicleFactory
from partners.factories import CounterpartyFactory


class Command(BaseCommand):
    help = (
        'Наповнює базу демонстраційними даними для дня 3: профіль компанії, '
        'контрагенти, водії, автомобілі, причепи (вигадані дані, не реальні контрагенти).'
    )

    def add_arguments(self, parser):
        parser.add_argument('--drivers', type=int, default=8)
        parser.add_argument('--vehicles', type=int, default=5)
        parser.add_argument('--trailers', type=int, default=5)
        parser.add_argument('--counterparties', type=int, default=6)

    @transaction.atomic
    def handle(self, *args, **options):
        company, created = Company.objects.get_or_create(
            edrpou='30112233',
            defaults=dict(
                name='ТОВ "АвтоЛогістик Сервіс"',
                inn='301122330123',
                address='м. Миколаїв, вул. Транспортна, буд. 10',
                bank_details='UA000000000000000000000000000',
                director='Ковальчук Олександр Петрович',
                phone='+380500000000',
            ),
        )
        self.stdout.write(self.style.SUCCESS(
            f'Company: {company} ({"створено" if created else "вже існує"})'
        ))

        counterparties = CounterpartyFactory.create_batch(options['counterparties'])
        drivers = DriverFactory.create_batch(options['drivers'])
        vehicles = VehicleFactory.create_batch(options['vehicles'])
        trailers = TrailerFactory.create_batch(options['trailers'])

        self.stdout.write(self.style.SUCCESS(
            f"Створено: контрагентів {len(counterparties)}, водіїв {len(drivers)}, "
            f"автомобілів {len(vehicles)}, причепів {len(trailers)}"
        ))
