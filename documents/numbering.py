"""Схема нумерації ТТН і Акту: окремі лічильники по префіксу
документа, за прикладом реальних номерів НИ-0065 і ОУ-0010 з наданих
робочих файлів компанії - формат «ПРЕФІКС-0000», номер зростає
послідовно в межах свого префікса.

compute_next_number - чиста функція без звернень до бази; next_ttn_number/next_act_number - тонкі обгортки, що
підставляють у неї queryset моделі.
"""
import re


def compute_next_number(existing_numbers, prefix, pad=4):
    """Повертає наступний вільний номер виду "PREFIX-0001" - шукає серед
    existing_numbers максимальний номер із заданим префіксом і додає 1.
    Значення, що не відповідають префіксу чи формату, ігноруються."""
    pattern = re.compile(rf'^{re.escape(prefix)}-(\d+)$')
    max_n = 0
    for value in existing_numbers:
        match = pattern.match(value or '')
        if match:
            max_n = max(max_n, int(match.group(1)))
    return f'{prefix}-{str(max_n + 1).zfill(pad)}'


def next_ttn_number():
    from documents.models import TTN
    return compute_next_number(TTN.objects.values_list('number', flat=True), 'НИ')


def next_act_number():
    from documents.models import Act
    return compute_next_number(Act.objects.values_list('number', flat=True), 'ОУ')
