"""
CE+VL tests for RegrasVip — IN 2026 §4.
Schedule: D1 (2m), D2 (4m), D3 (6m), Booster (15m). Contraindicated >= 5y (pediatric schedule).
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_vip01_menor2m_agendar_d1():
    r = run_engine(birth_date_ago(months=1))
    apr = get_scheduled_for(r, 'VIP (Poliomielite)')
    assert apr is not None and apr['dose'] == 1


def test_vip02_2m_recomendar_d1():
    r = run_engine(birth_date_ago(months=2))
    assert any(v['vacina'] == 'VIP (Poliomielite)' and v['dose'] == 1
               for v in r['vacinas_recomendadas'])


def test_vip03_d1_ha_15d_agendar_d2():
    data_d1 = today() - relativedelta(days=15)
    doses = [dose('VIP', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=2), doses)
    apr = get_scheduled_for(r, 'VIP (Poliomielite)')
    assert apr is not None and apr['dose'] == 2


def test_vip04_d1_d2_agendar_d3():
    # D2 applied 1 month ago → D3 scheduled next month
    data_d2 = today() - relativedelta(months=1)
    data_d1 = data_d2 - relativedelta(months=2)
    doses = [
        dose('VIP', data_d1, dose_num=1),
        dose('VIP', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(months=3), doses)
    # D3 should be scheduled (not yet due)
    apr = get_scheduled_for(r, 'VIP (Poliomielite)')
    assert apr is not None and apr['dose'] == 3


def test_vip05_d1_d2_d3_agendar_reforco():
    data_d1 = today() - relativedelta(months=8)
    data_d2 = data_d1 + relativedelta(months=2)
    data_d3 = data_d2 + relativedelta(months=2)
    doses = [
        dose('VIP', data_d1, dose_num=1),
        dose('VIP', data_d2, dose_num=2),
        dose('VIP', data_d3, dose_num=3),
    ]
    r = run_engine(birth_date_ago(months=8), doses)
    apr = get_scheduled_for(r, 'VIP (Poliomielite)')
    assert apr is not None and 'Reforço' in str(apr['dose'])


def test_vip06_reforco_aplicado_em_dia():
    data_d1 = today() - relativedelta(months=14)
    data_d2 = data_d1 + relativedelta(months=2)
    data_d3 = data_d2 + relativedelta(months=2)
    data_ref = data_d1 + relativedelta(months=13)
    doses = [
        dose('VIP', data_d1, dose_num=1),
        dose('VIP', data_d2, dose_num=2),
        dose('VIP', data_d3, dose_num=3),
        dose('VIP', data_ref, dose_num='Reforço'),
    ]
    r = run_engine(birth_date_ago(months=14), doses)
    assert 'VIP (Poliomielite)' in get_up_to_date(r)


def test_vip07_5anos_sem_reforco_contraindica():
    # VIP scheme is contraindicated >= 5a when Reforço wasn't applied
    r = run_engine(birth_date_ago(years=5))
    assert 'VIP (Poliomielite)' in get_contraindicated(r)


def test_vip08_crianca_4a_sem_d1_recomendar():
    r = run_engine(birth_date_ago(years=4))
    assert any(v['vacina'] == 'VIP (Poliomielite)'
               for v in r['vacinas_recomendadas'])


def test_vip09_d1_ha_2m_recomendar_d2():
    data_d1 = today() - relativedelta(months=2)
    doses = [dose('VIP', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=4), doses)
    assert any(v['vacina'] == 'VIP (Poliomielite)' and v['dose'] == 2
               for v in r['vacinas_recomendadas'])


def test_vip10_d1_d2_d3_reforco_recomendar_agora():
    # All 3 doses applied, reforço should be recommended at 15m (>= 15m now)
    dn = birth_date_ago(months=16)
    data_d1 = dn + relativedelta(months=2)
    data_d2 = dn + relativedelta(months=4)
    data_d3 = dn + relativedelta(months=6)
    doses = [
        dose('VIP', data_d1, dose_num=1),
        dose('VIP', data_d2, dose_num=2),
        dose('VIP', data_d3, dose_num=3),
    ]
    r = run_engine(dn, doses)
    assert any(v['vacina'] == 'VIP (Poliomielite)'
               for v in r['vacinas_recomendadas'])
