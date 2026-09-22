"""проста статистична детекція аномалій суми чи
ваги рейсу за z-score по історії аналогічних рейсів."""
import statistics
from decimal import Decimal

Z_THRESHOLD = 2.0


def z_score_anomaly(value: Decimal, history: list[Decimal]) -> tuple[bool, float | None]:
    """Повертає (is_anomaly, z_score). Якщо історії замало (< 3 значень)
    для статистично осмисленої оцінки - анoмалія не фіксується."""
    if len(history) < 3:
        return False, None
    values = [float(v) for v in history]
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    if stdev == 0:
        return False, None
    z = (float(value) - mean) / stdev
    return abs(z) > Z_THRESHOLD, z


def trip_amount_anomaly(trip, queryset=None) -> tuple[bool, float | None]:
    """Порівнює суму рейсу з історією підтверджених рейсів за тим самим
    маршрутом (навантаження -> розвантаження), без самого рейсу."""
    from trips.models import Trip

    qs = queryset if queryset is not None else Trip.objects.filter(
        loading_address=trip.loading_address,
        unloading_address=trip.unloading_address,
        status=Trip.Status.CONFIRMED,
    ).exclude(pk=trip.pk)
    history = list(qs.values_list('amount_no_vat', flat=True))
    return z_score_anomaly(trip.amount_no_vat, history)
