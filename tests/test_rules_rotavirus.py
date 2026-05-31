"""
CE+VL tests for RulesRotavirus — IN 2026 §5.
D1: ≤ 3m15d. D2: ≤ 7m29d. Minimum D1→D2 interval: 30 days.
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_rota01_2m_recomendar_d1():
    r = run_engine(birth_date_ago(months=2))
    assert any(v['vaccine'] == 'Rotavírus (VORH)' for v in r['recommended_vaccines'])


def test_rota02_3m14d_recomendar_d1_limite():
    # 105 dias = último dia permitido para D1 (regra: d <= 105)
    dn = birth_date_ago(days=105)
    r = run_engine(dn)
    assert any(v['vaccine'] == 'Rotavírus (VORH)' for v in r['recommended_vaccines'])


def test_rota03_3m15d_contraindica_d1():
    # 106 dias = após o limite para D1 (regra: d > 105 → contraindica)
    dn = birth_date_ago(days=106)
    r = run_engine(dn)
    assert any(v['vaccine'] == 'Rotavírus (VORH)' for v in r['contraindicated_vaccines'])
    assert not any(v['vaccine'] == 'Rotavírus (VORH)' for v in r['recommended_vaccines'])


def test_rota04_d1_ha_15d_agendar_d2():
    data_d1 = today() - relativedelta(days=15)
    doses = [dose('VORH', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=2), doses)
    apr = get_scheduled_for(r, 'Rotavírus (VORH)')
    assert apr is not None and apr['dose'] == 2


def test_rota05_7m28d_com_d1_recomendar_d2():
    # 7m28d — ainda dentro do limite para D2
    dn = birth_date_ago(months=7, days=28)
    data_d1 = dn + relativedelta(months=2)
    doses = [dose('VORH', data_d1, dose_num=1)]
    r = run_engine(dn, doses)
    assert any(v['vaccine'] == 'Rotavírus (VORH)' and v['dose'] == 2
               for v in r['recommended_vaccines'])


def test_rota06_7m29d_com_d1_contraindica_d2():
    # 7m29d — passou o limite; D2 é contraindicada
    dn = birth_date_ago(months=7, days=29)
    data_d1 = dn + relativedelta(months=2)
    doses = [dose('VORH', data_d1, dose_num=1)]
    r = run_engine(dn, doses)
    assert any(v['vaccine'] == 'Rotavírus (VORH)' for v in r['contraindicated_vaccines'])
