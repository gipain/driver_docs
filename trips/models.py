from django.db import models


class Trip(models.Model):
    """Рейс - центральна сутність схеми: спільне джерело даних і для
    ТТН, і для рядка акту (день 2)."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'чернетка'
        CONFIRMED = 'confirmed', 'підтверджено'

    contract = models.ForeignKey(
        'partners.Contract', on_delete=models.PROTECT,
        related_name='trips', verbose_name='договір',
    )
    driver = models.ForeignKey(
        'fleet.Driver', on_delete=models.PROTECT,
        related_name='trips', verbose_name='водій',
    )
    vehicle = models.ForeignKey(
        'fleet.Vehicle', on_delete=models.PROTECT,
        related_name='trips', verbose_name='автомобіль',
    )
    trailer = models.ForeignKey(
        'fleet.Trailer', on_delete=models.PROTECT,
        related_name='trips', verbose_name='причіп',
        null=True, blank=True,
    )

    carrier = models.ForeignKey(
        'partners.Counterparty', on_delete=models.PROTECT,
        related_name='trips_as_carrier', verbose_name='перевізник',
    )
    sender = models.ForeignKey(
        'partners.Counterparty', on_delete=models.PROTECT,
        related_name='trips_as_sender', verbose_name='вантажовідправник',
    )
    receiver = models.ForeignKey(
        'partners.Counterparty', on_delete=models.PROTECT,
        related_name='trips_as_receiver', verbose_name='вантажоодержувач',
    )

    date = models.DateField('дата рейсу')
    loading_address = models.CharField('пункт навантаження', max_length=500)
    unloading_address = models.CharField('пункт розвантаження', max_length=500)
    route_text = models.CharField('маршрут', max_length=500, blank=True)
    weight_t = models.DecimalField('маса брутто, т', max_digits=8, decimal_places=3)
    amount_no_vat = models.DecimalField('сума без ПДВ, грн', max_digits=12, decimal_places=2)

    # Реквізити вантажу (день 10) - потрібні для розділу "Відомості про
    # вантаж" ТТН; раніше Trip зберігав лише агреговану вагу й суму,
    # без опису самого вантажу.
    cargo_name = models.CharField('найменування вантажу', max_length=255, blank=True)
    cargo_unit = models.CharField('одиниця виміру', max_length=20, default='шт')
    places_count = models.PositiveIntegerField('кількість місць', default=1)
    cargo_packaging = models.CharField('вид пакування', max_length=100, blank=True)

    status = models.CharField(
        'статус', max_length=16, choices=Status.choices, default=Status.DRAFT,
    )

    class Meta:
        verbose_name = 'рейс'
        verbose_name_plural = 'рейси'
        ordering = ['-date', '-id']

    def __str__(self):
        return f'Рейс №{self.pk} від {self.date:%d.%m.%Y}'

    def confirm(self):
        """Переводить рейс зі статусу «чернетка» в «підтверджено» і додає
        запис у спрощений журнал змін (день 5). Перед переходом прогонює
        рейс через усі перевірки дня 7 (validate_trip_for_confirmation) -
        підтвердити рейс із неповними чи суперечливими даними не можна."""
        from trips.validation import validate_trip_for_confirmation

        if self.status != self.Status.DRAFT:
            raise ValueError('Підтвердити можна лише рейс у статусі "чернетка".')
        errors = validate_trip_for_confirmation(self)
        if errors:
            raise ValueError(' '.join(errors))
        old_status = self.status
        self.status = self.Status.CONFIRMED
        self.save(update_fields=['status'])
        self.status_logs.create(from_status=old_status, to_status=self.status)


class TripStatusLog(models.Model):
    """Спрощений журнал змін статусу рейсу (день 5) - хто/коли не
    зберігається, лише сам факт і час переходу, цього достатньо для
    журналу практики."""

    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name='status_logs', verbose_name='рейс',
    )
    from_status = models.CharField('з статусу', max_length=16, choices=Trip.Status.choices)
    to_status = models.CharField('у статус', max_length=16, choices=Trip.Status.choices)
    changed_at = models.DateTimeField('дата й час зміни', auto_now_add=True)

    class Meta:
        verbose_name = 'запис журналу змін рейсу'
        verbose_name_plural = 'журнал змін рейсів'
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.trip} : {self.from_status} -> {self.to_status}'
