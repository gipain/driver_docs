"""Координати комірок заготовки ТТН.xlsx - зафіксовані виміром
наданого зразка ТТН №НИ-0065 через openpyxl. Ключі - умовні назви полів, значення - адреса комірки
на єдиному аркуші «Sheet1» (лицьовий і зворотний бік ТТН у наданому
файлі - це один аркуш, а не два: зворотний бік просто розташований
нижче).

Рядок AW36/Z36/AH36 - перший (і поки єдиний) рядок «Відомості про
вантаж»; при кількох позиціях вантажу такі рядки вставляються нижче
за тим самим шаблоном колонок, а TTN_TOTAL_ROW - рядок
підсумкової формули SUM.
"""

TTN_CELLS = {
    'header_line': 'A3',           # "№ НИ-0065 4 Вересня 2026 р."
    'place_of_drafting': 'G4',
    'vehicle_line': 'E6',          # марка, модель, тип, держ.номер одним рядком
    'trailer_line': 'AB6',
    'transport_type': 'AS6',
    'carrier_address': 'L8',
    'carrier_line': 'J10',         # назва + ЄДРПОУ
    'driver_line': 'AP10',         # ПІБ + номер посвідчення
    'sender_line': 'H12',
    'receiver_line': 'H14',
    'loading_address': 'H16',
    'unloading_address': 'AI16',
    'places_words': 'F18',
    'weight_words': 'T18',
    'driver_signature_name': 'AN18',
    'vehicle_length': 'S20',
    'vehicle_width': 'AB20',
    'vehicle_height': 'AH20',
    'vehicle_total_weight': 'AO20',
    'amount_words': 'M22',
    'vat_line': 'AS22',
    'accompanying_docs': 'K24',
}

TTN_CARGO_LINE_ROW = 36  # перший рядок блоку «Відомості про вантаж»
TTN_CARGO_LINE_COLUMNS = {
    'cargo_name': 'C',
    'cargo_unit': 'W',
    'cargo_qty': 'Z',
    'cargo_unit_price': 'AC',
    'cargo_amount': 'AH',
    'cargo_packaging': 'AN',
    'cargo_docs': 'AR',
    'cargo_weight': 'AW',
}
TTN_TOTAL_ROW = 37  # "Всього:" - тут будуть формули SUM (день 10)

TTN_SIGNATORY_CELLS = {
    'sender_signatory': 'A41',
    'loading_weight': 'J49',
}

ALL_DATA_CELLS = (
    list(TTN_CELLS.values())
    + [f'{col}{TTN_CARGO_LINE_ROW}' for col in TTN_CARGO_LINE_COLUMNS.values()]
    + [f'{col}{TTN_TOTAL_ROW}' for col in ('Z', 'AH', 'AW')]
    + list(TTN_SIGNATORY_CELLS.values())
)
