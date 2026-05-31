"""
CE+VL tests for RulesHPV — IN 2026 §18.
9–14y: 2 doses. 15–19y: 3 doses. Contraindicated >19y (routine).
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_hpv01_menor9anos_nao_recomendado():
    r = run_engine(birth_date_ago(years=8))
    assert 'HPV' not in get_recommended(r)


def test_hpv02_9anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=9))
    assert 'HPV' in get_recommended(r)


def test_hpv03_12anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=12))
    assert 'HPV' in get_recommended(r)


def test_hpv04_14anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=14))
    assert 'HPV' in get_recommended(r)


def test_hpv05_15anos_3doses_recomendar_d1():
    r = run_engine(birth_date_ago(years=15))
    assert 'HPV' in get_recommended(r)


def test_hpv06_19anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=19))
    assert 'HPV' in get_recommended(r)


def test_hpv07_20anos_contraindica():
    r = run_engine(birth_date_ago(years=20))
    assert 'HPV' in get_contraindicated(r)
    assert 'HPV' not in get_recommended(r)


def test_hpv08_dose_aplicada_em_dia():
    data_d1 = today() - relativedelta(months=7)
    data_d2 = data_d1 + relativedelta(months=6)
    doses = [
        dose('HPV', data_d1, dose_num=1),
        dose('HPV', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=12), doses)
    assert 'HPV' in get_up_to_date(r)
