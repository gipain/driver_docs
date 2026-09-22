"""Власний конвертер «число -> текст словами» - без готових
бібліотек. Три публічні функції поверх спільного ядра (int_to_words_uk +
pluralize_uk): для суми грошей, для дробових величин (вага) і для
кількості (цілих) одиниць"""
from decimal import Decimal

UNITS_BASE = ['', 'один', 'два', 'три', 'чотири', "п'ять", 'шість', 'сім', 'вісім', "дев'ять"]
# лише «один» і «два» змінюються за родом - решта чисел рід не має
UNITS_BY_GENDER = {
    'm': UNITS_BASE,
    'f': ['одна' if i == 1 else ('дві' if i == 2 else w) for i, w in enumerate(UNITS_BASE)],
    'n': ['одне' if i == 1 else w for i, w in enumerate(UNITS_BASE)],
}
TEENS = [
    'десять', 'одинадцять', 'дванадцять', 'тринадцять', 'чотирнадцять',
    "п'ятнадцять", 'шістнадцять', 'сімнадцять', 'вісімнадцять', "дев'ятнадцять",
]
TENS = [
    '', '', 'двадцять', 'тридцять', 'сорок', "п'ятдесят",
    'шістдесят', 'сімдесят', 'вісімдесят', "дев'яносто",
]
HUNDREDS = [
    '', 'сто', 'двісті', 'триста', 'чотириста', "п'ятсот",
    'шістсот', 'сімсот', 'вісімсот', "дев'ятсот",
]
# (однина, множина для 2-4, множина для 5+/0) - genitive-plural forms used
# by pluralize_uk; сама тисяча/мільйон теж узгоджується з pluralize_uk.
SCALE_FORMS = [
    None,
    ('тисяча', 'тисячі', 'тисяч'),
    ('мільйон', 'мільйони', 'мільйонів'),
]


def pluralize_uk(n: int, one: str, few: str, many: str) -> str:
    """Стандартне українське узгодження числівника з іменником: 1 - one,
    2-4 - few, 5-20 і решта - many (крім винятку 11-14, які завжди many)."""
    n = abs(int(n))
    if n % 100 in range(11, 15):
        return many
    if n % 10 == 1:
        return one
    if n % 10 in (2, 3, 4):
        return few
    return many


def _three_digits_to_words(n: int, gender: str = 'm') -> list[str]:
    words = []
    h, rem = divmod(n, 100)
    if h:
        words.append(HUNDREDS[h])
    if rem >= 10 and rem < 20:
        words.append(TEENS[rem - 10])
    else:
        t, u = divmod(rem, 10)
        if t:
            words.append(TENS[t])
        if u:
            words.append(UNITS_BY_GENDER[gender][u])
    return words


def int_to_words_uk(n: int, gender: str = 'm') -> str:
    """Переводить ціле невід'ємне число в українські слова (0..999_999_999).
    gender ('m'/'f'/'n') узгоджує «один/два» як «одна/дві» чи «одне» -
    потрібно для іменників жіночого (гривня, тисячна) чи середнього
    (місце) роду; на числа 3 і більше рід не впливає."""
    if n == 0:
        return 'нуль'
    parts: list[str] = []
    scale = len(SCALE_FORMS) - 1
    remaining = n
    chunks = []
    while remaining > 0 or scale >= 0:
        remaining, chunk = divmod(remaining, 1000) if scale > 0 else (0, remaining)
        chunks.append(chunk)
        if scale == 0:
            break
        scale -= 1
    chunks = chunks[::-1]  # від старшого розряду до молодшого
    n_scales = len(chunks) - 1
    for i, chunk in enumerate(chunks):
        cur_scale = n_scales - i
        if chunk == 0:
            continue
        chunk_gender = gender if cur_scale == 0 else ('f' if cur_scale == 1 else 'm')  # тисяча - жіночий рід
        parts.extend(_three_digits_to_words(chunk, gender=chunk_gender))
        if cur_scale > 0:
            one, few, many = SCALE_FORMS[cur_scale]
            parts.append(pluralize_uk(chunk, one, few, many))
    return ' '.join(parts)


def money_to_words_uk(amount: Decimal) -> str:
    """«Тридцять одна тисяча чотириста п'ятдесят одна гривня шістдесят
    п'ять копійок» - і гривні, і копійки повністю словами."""
    amount = Decimal(amount).quantize(Decimal('0.01'))
    hryvnias = int(amount)
    kopecks = int((amount - hryvnias) * 100)
    hryvnia_word = pluralize_uk(hryvnias, 'гривня', 'гривні', 'гривень')
    kopeck_word = pluralize_uk(kopecks, 'копійка', 'копійки', 'копійок')
    integer_words = int_to_words_uk(hryvnias, gender='f')
    kopeck_words = int_to_words_uk(kopecks, gender='f')
    return f'{integer_words.capitalize()} {hryvnia_word} {kopeck_words} {kopeck_word}'


# Слово-знаменник дробової частини («тисячних» тощо) в українській мові
# при читанні десяткового дробу відмінюється лише за принципом
# «одна/решта» (одна тисячна, але дві/чотири/двадцять тисячних) - на
# відміну від звичайного узгодження іменника з числівником через
# pluralize_uk, форма «few» (2-4) тут не використовується взагалі.
_DENOMINATOR_FORMS = {
    1: ('десята', 'десятих'),
    2: ('сота', 'сотих'),
    3: ('тисячна', 'тисячних'),
}


def fractional_to_words_uk(value: Decimal) -> str:
    """«Нуль цілих сто двадцять чотири тисячних» - формат точно за зразком
    ваги з наданої ТТН. Кількість знаків після коми визначає слово-
    знаменник (десятих/сотих/тисячних)."""
    value = Decimal(value)
    sign, digits, exponent = value.as_tuple()
    decimals = -exponent if exponent < 0 else 0
    if decimals == 0 or decimals not in _DENOMINATOR_FORMS:
        # ціле число - просто «нуль цілих», без дробової частини
        integer_part = int(value)
        return f'{int_to_words_uk(integer_part).capitalize()} цілих'
    scaled = int(value * (10 ** decimals))
    integer_part = scaled // (10 ** decimals)
    fractional_part = scaled % (10 ** decimals)
    one, many = _DENOMINATOR_FORMS[decimals]
    fractional_words = int_to_words_uk(fractional_part, gender='f')
    is_one = fractional_part % 10 == 1 and fractional_part % 100 != 11
    denom_word = one if is_one else many
    return f'{int_to_words_uk(integer_part).capitalize()} цілих {fractional_words} {denom_word}'


def count_to_words_uk(n: int, one: str, few: str, many: str, gender: str = 'n') -> str:
    """«Дев'ять місць» - ціле число словами + узгоджений іменник.
    gender за замовчуванням - середній рід («місце»), бо саме для нього
    ця функція й задумана в дорожній карті; для іншого іменника можна
    передати gender='m'/'f'."""
    word = pluralize_uk(n, one, few, many)
    return f'{int_to_words_uk(n, gender=gender).capitalize()} {word}'
