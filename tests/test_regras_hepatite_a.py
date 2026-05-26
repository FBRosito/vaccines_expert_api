"""
Testes CE+VL para RegrasHepatiteA — IN 2026 §15.
Dose única aos 15 meses. Contraindicada após 4a11m29d.
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_hepa01_15m_recomendar():
    r = run_engine(birth_date_ago(months=15))
    assert 'Hepatite A' in get_recommended(r)


def test_hepa02_2anos_recomendar():
    r = run_engine(birth_date_ago(years=2))
    assert 'Hepatite A' in get_recommended(r)


def test_hepa03_4anos11m_recomendar():
    r = run_engine(birth_date_ago(years=4, months=11))
    assert 'Hepatite A' in get_recommended(r)


def test_hepa04_5anos_contraindica():
    r = run_engine(birth_date_ago(years=5))
    assert 'Hepatite A' in get_contraindicated(r)
    assert 'Hepatite A' not in get_recommended(r)


def test_hepa05_dose_aplicada_em_dia():
    data = birth_date_ago(years=2) + relativedelta(months=15)
    doses = [dose('HEPATITE_A', data)]
    r = run_engine(birth_date_ago(years=3), doses)
    assert 'Hepatite A' in get_up_to_date(r)
    assert 'Hepatite A' not in get_recommended(r)
