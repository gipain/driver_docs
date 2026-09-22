from decimal import Decimal

from core.anomaly import z_score_anomaly


def test_no_anomaly_with_too_little_history():
    is_anomaly, z = z_score_anomaly(Decimal('1000'), [Decimal('900'), Decimal('1100')])
    assert is_anomaly is False
    assert z is None


def test_no_anomaly_for_typical_value():
    history = [Decimal('1000'), Decimal('1050'), Decimal('950'), Decimal('1020'), Decimal('980')]
    is_anomaly, z = z_score_anomaly(Decimal('1010'), history)
    assert is_anomaly is False


def test_anomaly_for_value_far_from_history():
    history = [Decimal('1000'), Decimal('1050'), Decimal('950'), Decimal('1020'), Decimal('980')]
    is_anomaly, z = z_score_anomaly(Decimal('5000'), history)  # у 5 разів більше за середнє
    assert is_anomaly is True
    assert z > 2.0


def test_no_anomaly_when_all_history_identical():
    history = [Decimal('1000')] * 5
    is_anomaly, z = z_score_anomaly(Decimal('1000'), history)
    assert is_anomaly is False
