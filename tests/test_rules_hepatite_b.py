"""
CE+VL tests for RegrasHepatiteB — IN 2026 §2.
Birth dose (monovalent). Adult schedule: 0-1-6 months.
From 2m: schedule via Penta (recognized by PENTA/DTP).
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_hb01_nascido_hoje_recomendar_ao_nascer():
    r = run_engine(today())
    assert any('Hepatite B' in v for v in get_recommended(r))


def test_hb02_1m_sem_dose_recomendar():
    r = run_engine(birth_date_ago(months=1))
    assert any('Hepatite B' in v for v in get_recommended(r))


def test_hb03_dose_nascer_aplicada_nao_recomenda_novamente():
    data_nascer = today() - relativedelta(months=1)
    doses = [dose('HEPATITE_B', data_nascer)]
    r = run_engine(birth_date_ago(months=1), doses)
    assert 'Hepatite B (ao nascer)' not in get_recommended(r)


def test_hb04_adulto_7anos_sem_hb_recomendar_esquema():
    r = run_engine(birth_date_ago(years=7))
    assert any('Hepatite B' in v for v in get_recommended(r))


def test_hb05_adulto_com_3doses_em_dia():
    data_d1 = today() - relativedelta(months=8)
    data_d2 = data_d1 + relativedelta(months=1)
    data_d3 = data_d1 + relativedelta(months=6)
    doses = [
        dose('HEPATITE_B', data_d1, dose_num=1),
        dose('HEPATITE_B', data_d2, dose_num=2),
        dose('HEPATITE_B', data_d3, dose_num=3),
    ]
    r = run_engine(birth_date_ago(years=30), doses)
    assert any('Hepatite B' in v for v in get_up_to_date(r))


def test_hb06_d1_agendar_d2():
    data_d1 = today() - relativedelta(days=15)
    doses = [dose('HEPATITE_B', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=25), doses)
    apr = get_scheduled_for(r, 'Hepatite B (esquema adulto)')
    assert apr is not None and apr['dose'] == 2


def test_hb07_d1_d2_agendar_d3():
    data_d1 = today() - relativedelta(months=3)
    data_d2 = data_d1 + relativedelta(months=1)
    doses = [
        dose('HEPATITE_B', data_d1, dose_num=1),
        dose('HEPATITE_B', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=25), doses)
    apr = get_scheduled_for(r, 'Hepatite B (esquema adulto)')
    assert apr is not None and apr['dose'] == 3
