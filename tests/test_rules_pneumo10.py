"""
CE+VL tests for RegrasPneumo10 — IN 2026 §6.
Schedule: D1 (2m), D2 (2m after D1), Booster (12m). Catch-up single dose 1-4y.
Contraindicated >= 5y.
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_p10_01_menor2m_agendar_d1():
    r = run_engine(birth_date_ago(months=1))
    apr = get_scheduled_for(r, 'Pneumocócica 10V')
    assert apr is not None and apr['dose'] == 1


def test_p10_02_2m_recomendar_d1():
    r = run_engine(birth_date_ago(months=2))
    assert any(v['vacina'] == 'Pneumocócica 10V' and v['dose'] == 1
               for v in r['vacinas_recomendadas'])


def test_p10_03_d1_ha_15d_agendar_d2():
    data_d1 = today() - relativedelta(days=15)
    doses = [dose('PNEUMO10', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=2), doses)
    apr = get_scheduled_for(r, 'Pneumocócica 10V')
    assert apr is not None and apr['dose'] == 2


def test_p10_04_d1_ha_2m_recomendar_d2():
    data_d1 = today() - relativedelta(months=2)
    doses = [dose('PNEUMO10', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=4), doses)
    assert any(v['vacina'] == 'Pneumocócica 10V' and v['dose'] == 2
               for v in r['vacinas_recomendadas'])


def test_p10_05_d1_d2_agendar_reforco():
    data_d1 = today() - relativedelta(months=4)
    data_d2 = data_d1 + relativedelta(months=2)
    doses = [
        dose('PNEUMO10', data_d1, dose_num=1),
        dose('PNEUMO10', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(months=6), doses)
    apr = get_scheduled_for(r, 'Pneumocócica 10V')
    assert apr is not None and 'Reforço' in str(apr['dose'])


def test_p10_06_d1_d2_reforco_aplicado_em_dia():
    data_d1 = today() - relativedelta(months=12)
    data_d2 = data_d1 + relativedelta(months=2)
    data_ref = data_d1 + relativedelta(months=10)
    doses = [
        dose('PNEUMO10', data_d1, dose_num=1),
        dose('PNEUMO10', data_d2, dose_num=2),
        dose('PNEUMO10', data_ref, dose_num=3),
    ]
    r = run_engine(birth_date_ago(months=14), doses)
    assert 'Pneumocócica 10V' in get_up_to_date(r)


def test_p10_07_catchup_1a_sem_doses_dose_unica():
    r = run_engine(birth_date_ago(years=1))
    assert any(v['vacina'] == 'Pneumocócica 10V' and v['dose'] == 'Única'
               for v in r['vacinas_recomendadas'])


def test_p10_08_catchup_4a_sem_doses_dose_unica():
    r = run_engine(birth_date_ago(years=4))
    assert any(v['vacina'] == 'Pneumocócica 10V' and v['dose'] == 'Única'
               for v in r['vacinas_recomendadas'])


def test_p10_09_5anos_sem_doses_contraindica():
    r = run_engine(birth_date_ago(years=5))
    assert 'Pneumocócica 10V' in get_contraindicated(r)
    assert 'Pneumocócica 10V' not in get_recommended(r)


def test_p10_10_adulto_sem_doses_contraindica():
    r = run_engine(birth_date_ago(years=30))
    assert 'Pneumocócica 10V' in get_contraindicated(r)
