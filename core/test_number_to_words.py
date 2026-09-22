"""Юніт-тести конвертера «число -> текст». Головні кейси звірені
з реальними зразками із наданої ТТН №НИ-0065 (сума й вага) і словесно
підтвердженою кількістю місць"""
from decimal import Decimal

import pytest

from core.number_to_words import (
    count_to_words_uk,
    fractional_to_words_uk,
    int_to_words_uk,
    money_to_words_uk,
    pluralize_uk,
)


@pytest.mark.parametrize('n,expected', [
    (1, 'один'), (5, "п'ять"), (11, 'одинадцять'), (19, "дев'ятнадцять"),
    (20, 'двадцять'), (21, 'двадцять один'), (100, 'сто'), (101, 'сто один'),
    (1000, 'одна тисяча'), (2000, 'дві тисячі'), (5000, "п'ять тисяч"),
    (31451, "тридцять одна тисяча чотириста п'ятдесят один"),
    (0, 'нуль'),
])
def test_int_to_words_uk_masculine(n, expected):
    assert int_to_words_uk(n) == expected


def test_int_to_words_uk_feminine_one_and_two():
    assert int_to_words_uk(1, gender='f') == 'одна'
    assert int_to_words_uk(2, gender='f') == 'дві'
    assert int_to_words_uk(3, gender='f') == 'три'  # від 3 рід не впливає


def test_int_to_words_uk_neuter_one():
    assert int_to_words_uk(1, gender='n') == 'одне'
    assert int_to_words_uk(2, gender='n') == 'два'  # як чоловічий


@pytest.mark.parametrize('n,expected', [(1, 'a'), (2, 'b'), (3, 'b'), (4, 'b'),
                                          (5, 'c'), (11, 'c'), (12, 'c'), (14, 'c'),
                                          (21, 'a'), (22, 'b'), (25, 'c')])
def test_pluralize_uk(n, expected):
    assert pluralize_uk(n, 'a', 'b', 'c') == expected


def test_money_to_words_matches_ttn_sample():
    # реальний приклад з ТТН №НИ-0065: "Усього відпущено... 31451.65 грн"
    assert money_to_words_uk(Decimal('31451.65')) == (
        "Тридцять одна тисяча чотириста п'ятдесят одна гривня шістдесят п'ять копійок"
    )


@pytest.mark.parametrize('amount,expected', [
    (Decimal('0.00'), 'Нуль гривень нуль копійок'),
    (Decimal('1.01'), 'Одна гривня одна копійка'),
    (Decimal('2.02'), 'Дві гривні дві копійки'),
])
def test_money_to_words_edge_cases(amount, expected):
    assert money_to_words_uk(amount) == expected


def test_fractional_to_words_matches_ttn_sample():
    # реальний приклад маси з ТТН №НИ-0065: "Нуль цілих сто двадцять
    # чотири тисячних"
    assert fractional_to_words_uk(Decimal('0.124')) == (
        'Нуль цілих сто двадцять чотири тисячних'
    )


@pytest.mark.parametrize('value,expected', [
    (Decimal('0.021'), 'Нуль цілих двадцять одна тисячна'),
    (Decimal('0.011'), 'Нуль цілих одинадцять тисячних'),
    (Decimal('12.5'), "Дванадцять цілих п'ять десятих"),
])
def test_fractional_to_words_edge_cases(value, expected):
    assert fractional_to_words_uk(value) == expected


def test_count_to_words_matches_ttn_sample():
    # реальний приклад з ТТН №НИ-0065: "кількість місць Дев'ять місць"
    assert count_to_words_uk(9, 'місце', 'місця', 'місць') == "Дев'ять місць"


@pytest.mark.parametrize('n,expected', [
    (1, 'Одне місце'),
    (2, 'Два місця'),
    (21, 'Двадцять одне місце'),
    (11, 'Одинадцять місць'),
])
def test_count_to_words_neuter_agreement(n, expected):
    assert count_to_words_uk(n, 'місце', 'місця', 'місць') == expected
