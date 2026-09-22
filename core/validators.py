"""Валідатори форматів і контрольних цифр, спільні для core і partners
(ЄДРПОУ/ІПН зустрічаються і в Company, і в Counterparty)"""
import re

from django.core.exceptions import ValidationError

EDRPOU_RE = re.compile(r'^\d{8}$')
INN_RE = re.compile(r'^\d{10}$|^\d{12}$')

# Ваги для перевірки контрольної цифри РНОКПП (ІПН фізособи) - mod 11,
# застосовуються до перших 9 цифр номера (день 4, п. "написати функцію
# перевірки контрольної цифри").
RNOKPP_WEIGHTS = (7, 3, 1, 7, 3, 1, 7, 3, 1)


def validate_edrpou(value):
    """ЄДРПОУ - рівно 8 цифр."""
    if not EDRPOU_RE.match(value or ''):
        raise ValidationError(
            'ЄДРПОУ має складатися рівно з 8 цифр (введено: %(value)r).',
            params={'value': value},
        )


def rnokpp_checksum_valid(value: str) -> bool:
    """Перевіряє контрольну цифру 10-значного РНОКПП (ІПН фізособи) за
    методом mod 11 з вагами 7,3,1,7,3,1,7,3,1 по перших 9 цифрах.

    Повертає True/False; не кидає винятків - зручно і для валідатора
    поля, і для юніт-тестів.
    """
    if not re.match(r'^\d{10}$', value or ''):
        return False
    digits = [int(c) for c in value]
    checksum = sum(d * w for d, w in zip(digits, RNOKPP_WEIGHTS)) % 11
    if checksum == 10:
        checksum %= 10
    return checksum == digits[9]


def validate_inn(value):
    """ІПН - 10 цифр (фізособа, з перевіркою контрольної цифри) або
    12 цифр (юрособа, без окремого алгоритму контрольної цифри - Держреєстр
    не публікує його як частину завдання практики)."""
    if not INN_RE.match(value or ''):
        raise ValidationError(
            'ІПН має бути 10 цифр (фізособа) або 12 цифр (юрособа) '
            '(введено: %(value)r).',
            params={'value': value},
        )
    if len(value) == 10 and not rnokpp_checksum_valid(value):
        raise ValidationError(
            'Невірна контрольна цифра РНОКПП: %(value)r не проходить '
            'перевірку mod 11.',
            params={'value': value},
        )


PLATE_RE = re.compile(r'^[A-ZА-ЯЄІЇ]{2}\d{4}[A-ZА-ЯЄІЇ]{2}$')


def validate_plate_number(value):
    """Формат державного номера України: 2 літери, 4 цифри, 2 літери
    (напр. AI1234AA). Унікальність - окремо, на рівні поля моделі
    (unique=True), тут перевіряється лише формат."""
    if not PLATE_RE.match((value or '').upper().replace(' ', '')):
        raise ValidationError(
            'Держ.номер має бути у форматі "AA0000AA" '
            '(введено: %(value)r).',
            params={'value': value},
        )
