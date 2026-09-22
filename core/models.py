from django.db import models

from core.validators import validate_edrpou, validate_inn


class Company(models.Model):
    """Профіль власної фірми - підставляється в документи як перевізник
    або виконавець за замовчуванням (сутність Company)."""

    name = models.CharField('назва', max_length=255)
    edrpou = models.CharField('ЄДРПОУ', max_length=8, unique=True, validators=[validate_edrpou])
    inn = models.CharField('ІПН', max_length=12, blank=True, validators=[validate_inn])
    address = models.CharField('адреса', max_length=500)
    bank_details = models.TextField('банківські реквізити', blank=True)
    director = models.CharField('директор', max_length=255)
    phone = models.CharField('телефон', max_length=32, blank=True)

    class Meta:
        verbose_name = 'компанія'
        verbose_name_plural = 'профіль компанії'

    def __str__(self):
        return self.name
