"""
CE+VL tests for RulesPentaDTP — IN 2026 §3.
Penta: D1 (2m), D2 (4m), D3 (6m). DTP R1 (15m), R2 (4y). Contraindicated >= 7y.
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_penta01_menor2m_agendar_d1():
    r = run_engine(birth_date_ago(months=1))
    apr = get_scheduled_for(r, 'Penta')
    assert apr is not None and apr['dose'] == 1


def test_penta02_2m_recomendar_d1():
    r = run_engine(birth_date_ago(months=2))
    assert any(v['vaccine'] == 'Penta' and v['dose'] == 1
               for v in r['recommended_vaccines'])


def test_penta03_d1_ha_30d_agendar_d2():
    data_d1 = today() - relativedelta(days=30)
    doses = [dose('PENTA', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=3), doses)
    apr = get_scheduled_for(r, 'Penta')
    assert apr is not None and apr['dose'] == 2


def test_penta04_d1_d2_agendar_d3():
    # D2 applied 1 month ago → D3 scheduled next month (still 1m from due date)
    data_d2 = today() - relativedelta(months=1)
    data_d1 = data_d2 - relativedelta(months=2)
    doses = [
        dose('PENTA', data_d1, dose_num=1),
        dose('PENTA', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(months=3), doses)
    apr = get_scheduled_for(r, 'Penta')
    assert apr is not None and apr['dose'] == 3


def test_penta05_d1_d2_d3_recomendar_dtp_r1():
    # 3 doses applied, child >= 15m and >= 6m from D3 → DTP R1 recommended
    dn = birth_date_ago(months=20)
    data_d1 = dn + relativedelta(months=2)
    data_d2 = dn + relativedelta(months=4)
    data_d3 = dn + relativedelta(months=6)
    doses = [
        dose('PENTA', data_d1, dose_num=1),
        dose('PENTA', data_d2, dose_num=2),
        dose('PENTA', data_d3, dose_num=3),
    ]
    r = run_engine(dn, doses)
    assert any(v['vaccine'] == 'DTP (Tríplice Bacteriana)'
               for v in r['recommended_vaccines'])


def test_penta06_dtp_r1_aplicado_agendar_r2():
    dn = birth_date_ago(years=2)
    data_d1 = dn + relativedelta(months=2)
    data_d2 = dn + relativedelta(months=4)
    data_d3 = dn + relativedelta(months=6)
    data_r1 = dn + relativedelta(months=15)
    doses = [
        dose('PENTA', data_d1, dose_num=1),
        dose('PENTA', data_d2, dose_num=2),
        dose('PENTA', data_d3, dose_num=3),
        dose('DTP', data_r1, dose_num=1),
    ]
    r = run_engine(dn, doses)
    apr = get_scheduled_for(r, 'DTP (Tríplice Bacteriana)')
    assert apr is not None and '2' in str(apr['dose'])


def test_penta07_dtp_r2_recomendar_4anos():
    dn = birth_date_ago(years=4)
    data_d1 = dn + relativedelta(months=2)
    data_d2 = dn + relativedelta(months=4)
    data_d3 = dn + relativedelta(months=6)
    data_r1 = dn + relativedelta(months=15)
    doses = [
        dose('PENTA', data_d1, dose_num=1),
        dose('PENTA', data_d2, dose_num=2),
        dose('PENTA', data_d3, dose_num=3),
        dose('DTP', data_r1, dose_num=1),
    ]
    r = run_engine(dn, doses)
    assert any(v['vaccine'] == 'DTP (Tríplice Bacteriana)'
               for v in r['recommended_vaccines'])


def test_penta08_dtp_r1_r2_esquema_completo():
    dn = birth_date_ago(years=5)
    data_d1 = dn + relativedelta(months=2)
    data_d2 = dn + relativedelta(months=4)
    data_d3 = dn + relativedelta(months=6)
    data_r1 = dn + relativedelta(months=15)
    data_r2 = dn + relativedelta(years=4)
    doses = [
        dose('PENTA', data_d1, dose_num=1),
        dose('PENTA', data_d2, dose_num=2),
        dose('PENTA', data_d3, dose_num=3),
        dose('DTP', data_r1, dose_num=1),
        dose('DTP', data_r2, dose_num=2),
    ]
    r = run_engine(dn, doses)
    assert 'DTP (Tríplice Bacteriana)' in get_up_to_date(r)


def test_penta09_7anos_sem_penta_contraindica():
    r = run_engine(birth_date_ago(years=7))
    assert 'Penta' in get_contraindicated(r)
    assert 'Penta' not in get_recommended(r)


def test_penta10_adulto_sem_penta_contraindica():
    r = run_engine(birth_date_ago(years=30))
    assert 'Penta' in get_contraindicated(r)


def test_penta11_2m_recomendar_d1_imediata():
    # VL: exatamente 2 meses → deve recomendar D1
    r = run_engine(birth_date_ago(months=2))
    assert any(v['vaccine'] == 'Penta' for v in r['recommended_vaccines'])


def test_penta12_penta_completa_dtp_r1_r2_recomendar():
    # Child 4 years 11 months, has all Penta + DTP R1, should recommend DTP R2
    dn = birth_date_ago(years=4, months=11)
    data_d1 = dn + relativedelta(months=2)
    data_d2 = dn + relativedelta(months=4)
    data_d3 = dn + relativedelta(months=6)
    data_r1 = dn + relativedelta(months=15)
    doses = [
        dose('PENTA', data_d1, dose_num=1),
        dose('PENTA', data_d2, dose_num=2),
        dose('PENTA', data_d3, dose_num=3),
        dose('DTP', data_r1, dose_num=1),
    ]
    r = run_engine(dn, doses)
    # DTP R2 should be recommended or scheduled
    dtp_output = (
        any(v['vaccine'] == 'DTP (Tríplice Bacteriana)' for v in r['recommended_vaccines']) or
        any(v['vaccine'] == 'DTP (Tríplice Bacteriana)' for v in r['scheduled_vaccines'])
    )
    assert dtp_output
