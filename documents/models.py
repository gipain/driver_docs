from django.db import models


class TTN(models.Model):
    """Товарно-транспортна накладна (Форма №1-ТН). Зв'язок з Trip - 1:1
    (день 2): для одного рейсу існує рівно одна ТТН."""

    trip = models.OneToOneField(
        'trips.Trip', on_delete=models.PROTECT,
        related_name='ttn', verbose_name='рейс',
    )
    number = models.CharField('номер ТТН', max_length=32, unique=True)
    date = models.DateField('дата складання')
    place = models.CharField('місце складання', max_length=255)
    accompanying_docs = models.CharField(
        'супровідні документи на вантаж', max_length=500, blank=True,
    )

    class Meta:
        verbose_name = 'ТТН'
        verbose_name_plural = 'ТТН'
        ordering = ['-date']

    def __str__(self):
        return f'ТТН №{self.number}'


class CargoLine(models.Model):
    """Рядок розділу «Відомості про вантаж» (зворотний бік ТТН)."""

    ttn = models.ForeignKey(
        TTN, on_delete=models.CASCADE,
        related_name='cargo_lines', verbose_name='ТТН',
    )
    name = models.CharField('найменування вантажу', max_length=255)
    unit = models.CharField('одиниця виміру', max_length=20, default='шт')
    qty = models.DecimalField('кількість місць', max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(
        'ціна без ПДВ за одиницю, грн', max_digits=12, decimal_places=2,
    )
    amount = models.DecimalField('сума з ПДВ, грн', max_digits=12, decimal_places=2)
    packaging = models.CharField('вид пакування', max_length=100, blank=True)
    weight_t = models.DecimalField('маса брутто рядка, т', max_digits=8, decimal_places=3, default=0)

    class Meta:
        verbose_name = 'рядок вантажу ТТН'
        verbose_name_plural = 'рядки вантажу ТТН'

    def __str__(self):
        return f'{self.name} ({self.qty} {self.unit})'


class Act(models.Model):
    """Акт здачі-прийняття робіт (послуг) - підсумовує один або кілька
    рейсів по договору для виставлення контрагенту."""

    number = models.CharField('номер акту', max_length=32, unique=True)
    date = models.DateField('дата складання')
    contract = models.ForeignKey(
        'partners.Contract', on_delete=models.PROTECT,
        related_name='acts', verbose_name='договір',
    )
    customer = models.ForeignKey(
        'partners.Counterparty', on_delete=models.PROTECT,
        related_name='acts_as_customer', verbose_name='замовник',
    )
    executor = models.ForeignKey(
        'core.Company', on_delete=models.PROTECT,
        related_name='acts_as_executor', verbose_name='виконавець',
    )
    amount_no_vat = models.DecimalField('сума без ПДВ, грн', max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField('ПДВ 20%, грн', max_digits=12, decimal_places=2)
    amount_with_vat = models.DecimalField('сума з ПДВ, грн', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'акт здачі-прийняття робіт'
        verbose_name_plural = 'акти здачі-прийняття робіт'
        ordering = ['-date']

    def __str__(self):
        return f'Акт №{self.number}'


class ActLine(models.Model):
    """Рядок послуги в акті - посилається на конкретний рейс, з якого
    беруться опис маршруту, вага і сума (день 2)."""

    act = models.ForeignKey(
        Act, on_delete=models.CASCADE,
        related_name='lines', verbose_name='акт',
    )
    trip = models.ForeignKey(
        'trips.Trip', on_delete=models.PROTECT,
        related_name='act_lines', verbose_name='рейс',
    )
    description = models.CharField('опис послуги', max_length=500)
    weight_t = models.DecimalField('вага, т', max_digits=8, decimal_places=3)
    amount = models.DecimalField('сума, грн', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'рядок акту'
        verbose_name_plural = 'рядки акту'

    def __str__(self):
        return f'{self.description} - {self.amount} грн'
