"""
CE+VL tests for RegrasDTAdulto — IN 2026 §17.
Booster every 10 years from age 7. Initial schedule: 3 doses (0, 30d, 180d).
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_dt01_7anos_sem_dt_recomendar():
    r = run_engine(birth_date_ago(years=7))
    assert any('dT' in v or 'Dupla' in v for v in get_recommended(r))


def test_dt02_adulto_30a_sem_dt_recomendar():
    r = run_engine(birth_date_ago(years=30))
    assert any('dT' in v or 'Dupla' in v for v in get_recommended(r))


def test_dt03_dt_d1_ha_20d_agendar_d2():
    data_d1 = today() - relativedelta(days=20)
    doses = [dose('dT', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=30), doses)
    apr = get_scheduled_for(r, 'dT (Dupla Adulto)')
    assert apr is not None and '2' in str(apr['dose'])


def test_dt04_esquema_completo_em_dia():
    data_d1 = today() - relativedelta(months=8)
    data_d2 = data_d1 + relativedelta(days=30)
    data_d3 = data_d1 + relativedelta(days=180)
    doses = [
        dose('dT', data_d1, dose_num=1),
        dose('dT', data_d2, dose_num=2),
        dose('dT', data_d3, dose_num=3),
    ]
    r = run_engine(birth_date_ago(years=30), doses)
    assert any('dT' in v or 'Dupla' in v for v in get_up_to_date(r))


def test_dt05_reforco_vencido_10anos_recomendar():
    data_reforco = today() - relativedelta(years=10)
    doses = [
        dose('dT', data_reforco - relativedelta(months=6), dose_num=1),
        dose('dT', data_reforco - relativedelta(months=5), dose_num=2),
        dose('dT', data_reforco, dose_num=3),
    ]
    r = run_engine(birth_date_ago(years=40), doses)
    assert any('dT' in v or 'Dupla' in v for v in get_recommended(r))


def test_dt06_reforco_recente_em_dia():
    data_reforco = today() - relativedelta(years=3)
    doses = [
        dose('dT', data_reforco - relativedelta(months=6), dose_num=1),
        dose('dT', data_reforco - relativedelta(months=5), dose_num=2),
        dose('dT', data_reforco, dose_num=3),
    ]
    r = run_engine(birth_date_ago(years=40), doses)
    assert any('dT' in v or 'Dupla' in v for v in get_up_to_date(r))


def test_dt07_menor7anos_nao_indicado_rotina():
    r = run_engine(birth_date_ago(years=6))
    assert not any('dT (Dupla' in v for v in get_recommended(r))
