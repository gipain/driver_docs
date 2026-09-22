"""Юніт-тести валідаторів. Власні тестові РНОКПП рахуються прямо
тут за тим самим алгоритмом, що і в validators.py"""
import pytest
from django.core.exceptions import ValidationError

from core.validators import (
    RNOKPP_WEIGHTS,
    rnokpp_checksum_valid,
    validate_edrpou,
    validate_inn,
    validate_plate_number,
)


def make_valid_rnokpp(prefix9: str) -> str:
    """Допоміжна функція тесту: рахує коректну контрольну цифру для
    заданих перших 9 цифр і повертає повний 10-значний РНОКПП."""
    digits = [int(c) for c in prefix9]
    checksum = sum(d * w for d, w in zip(digits, RNOKPP_WEIGHTS)) % 11
    if checksum == 10:
        checksum %= 10
    return prefix9 + str(checksum)


# ---------- validate_edrpou ----------

@pytest.mark.parametrize('value', ['12345678', '00000001', '99999999'])
def test_edrpou_valid(value):
    validate_edrpou(value)  # не має кидати виняток


@pytest.mark.parametrize('value', [
    '1234567',      # 7 цифр
    '123456789',    # 9 цифр
    '1234567a',     # не цифра
    '',
    None,
])
def test_edrpou_invalid(value):
    with pytest.raises(ValidationError):
        validate_edrpou(value)


# ---------- rnokpp_checksum_valid / validate_inn (10 цифр, фізособа) ----------

@pytest.mark.parametrize('prefix9', [
    '312233445', '100200300', '987654321', '000000001',
])
def test_rnokpp_checksum_valid_for_generated_numbers(prefix9):
    rnokpp = make_valid_rnokpp(prefix9)
    assert rnokpp_checksum_valid(rnokpp) is True
    validate_inn(rnokpp)  # не має кидати виняток


@pytest.mark.parametrize('prefix9', ['312233445', '100200300'])
def test_rnokpp_checksum_rejects_wrong_last_digit(prefix9):
    valid = make_valid_rnokpp(prefix9)
    wrong_digit = str((int(valid[-1]) + 1) % 10)
    broken = valid[:-1] + wrong_digit
    assert rnokpp_checksum_valid(broken) is False
    with pytest.raises(ValidationError):
        validate_inn(broken)


@pytest.mark.parametrize('value', ['123', '12345678901', 'abcdefghij', '', None])
def test_rnokpp_checksum_invalid_format(value):
    assert rnokpp_checksum_valid(value) is False


# ---------- validate_inn (12 цифр, юрособа) ----------

def test_inn_12_digits_legal_entity_accepted():
    validate_inn('301122330123')  # не має кидати виняток


@pytest.mark.parametrize('value', ['1234567890123', '12345', 'abcdefabcdef'])
def test_inn_invalid_length_or_format(value):
    with pytest.raises(ValidationError):
        validate_inn(value)


# ---------- validate_plate_number ----------

@pytest.mark.parametrize('value', ['AI1234AA', 'BC0001XT', 'ai1234aa'])
def test_plate_number_valid(value):
    validate_plate_number(value)  # не має кидати виняток


@pytest.mark.parametrize('value', ['AI12345A', 'A1234AA', '', 'AI1234AAA'])
def test_plate_number_invalid(value):
    with pytest.raises(ValidationError):
        validate_plate_number(value)
