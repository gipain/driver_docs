from django.db import models

from core.validators import validate_edrpou, validate_inn


class Counterparty(models.Model):
    """Єдиний довідник контрагентів для всіх ролей у рейсі й акті:
    перевізник, вантажовідправник, вантажоодержувач, замовник. Роль
    визначається тим, з якого поля Trip/Act на конкретний запис
    посилаються, а не окремим атрибутом цієї таблиці (день 2)."""

    name = models.CharField('назва', max_length=255)
    edrpou = models.CharField('ЄДРПОУ', max_length=8, unique=True, validators=[validate_edrpou])
    inn = models.CharField('ІПН', max_length=12, blank=True, validators=[validate_inn])
    address = models.CharField('адреса', max_length=500)
    bank_details = models.TextField('банківські реквізити', blank=True)
    director = models.CharField('директор', max_length=255, blank=True)
    phone = models.CharField('телефон', max_length=32, blank=True)

    class Meta:
        verbose_name = 'контрагент'
        verbose_name_plural = 'контрагенти'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (ЄДРПОУ {self.edrpou})'


class Contract(models.Model):
    counterparty = models.ForeignKey(
        Counterparty, on_delete=models.PROTECT, related_name='contracts',
        verbose_name='контрагент-замовник',
    )
    number = models.CharField('номер договору', max_length=50)
    date = models.DateField('дата договору')
    valid_until = models.DateField(
        'діє до', null=True, blank=True,
        help_text='Залиште порожнім, якщо договір безстроковий.',
    )

    class Meta:
        verbose_name = 'договір'
        verbose_name_plural = 'договори'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['counterparty', 'number'],
                name='uniq_contract_number_per_counterparty',
            ),
        ]

    def __str__(self):
        return f'Договір №{self.number} від {self.date:%d.%m.%Y}'
