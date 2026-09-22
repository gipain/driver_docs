from django.db import models
from django.utils import timezone

from core.validators import validate_plate_number


class Driver(models.Model):
    full_name = models.CharField('ПІБ', max_length=255)
    license_number = models.CharField('номер посвідчення', max_length=32, unique=True)
    license_expiry = models.DateField('посвідчення дійсне до')

    class Meta:
        verbose_name = 'водій'
        verbose_name_plural = 'водії'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    @property
    def is_license_expired(self):
        """Позначка «прострочено» для посвідчення водія (день 4)."""
        return self.license_expiry < timezone.localdate()


class Vehicle(models.Model):
    brand_model = models.CharField('марка / модель', max_length=100)
    plate_number = models.CharField(
        'державний номер', max_length=16, unique=True, validators=[validate_plate_number],
    )
    vehicle_type = models.CharField('тип', max_length=50, default='вантажний')
    capacity_t = models.DecimalField('вантажопідйомність, т', max_digits=6, decimal_places=3)
    length_m = models.DecimalField('довжина, м', max_digits=5, decimal_places=3)
    width_m = models.DecimalField('ширина, м', max_digits=5, decimal_places=3)
    height_m = models.DecimalField('висота, м', max_digits=5, decimal_places=3)
    inspection_expiry = models.DateField('техогляд дійсний до')

    class Meta:
        verbose_name = 'автомобіль'
        verbose_name_plural = 'автомобілі'
        ordering = ['plate_number']

    def __str__(self):
        return f'{self.brand_model} ({self.plate_number})'

    @property
    def is_inspection_expired(self):
        """Позначка «прострочено» для техогляду автомобіля (день 4)."""
        return self.inspection_expiry < timezone.localdate()


class Trailer(models.Model):
    brand_model = models.CharField('марка / модель', max_length=100)
    plate_number = models.CharField(
        'державний номер', max_length=16, unique=True, validators=[validate_plate_number],
    )

    class Meta:
        verbose_name = 'причіп'
        verbose_name_plural = 'причепи'
        ordering = ['plate_number']

    def __str__(self):
        return f'{self.brand_model} ({self.plate_number})'
