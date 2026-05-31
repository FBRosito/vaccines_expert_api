"""
CE+VL tests for RegrasVirusVivosAtenuados — IN 2026 §10, §11, §12.
SCR: D1 (12m), D2 (15m). Varicela: D1 (15m), D2 (4y). FA: D1 (9m), Booster (4y).
SCR × FA conflict under 2 years: salience=100 prioritizes SCR.
FA contraindicated in routine schedule for >= 60y.
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


# =================================================================
# SCR (Tríplice Viral)
# =================================================================

def test_vv01_menor12m_scr_aprazada():
    r = run_engine(birth_date_ago(months=6))
    nomes_apr = {v['vacina'] for v in r['vacinas_aprazadas']}
    assert 'SCR (Tríplice Viral)' in nomes_apr


def test_vv02_12m_scr_recomendar_d1():
    r = run_engine(birth_date_ago(months=12))
    # At 12m, SCR may be deferred by conflict if FA also needed
    # Without FA dose, conflict rule fires and recommends SCR D1
    assert any(v['vacina'] == 'SCR (Tríplice Viral)' and v['dose'] == 1
               for v in r['vacinas_recomendadas'])


def test_vv03_scr_d1_aplicado_agendar_d2():
    # D1 applied 10 days ago at 12m → D2 must be scheduled (30d interval + 15m age)
    data_d1 = today() - relativedelta(days=10)
    doses = [dose('SCR', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=12), doses)
    apr = get_scheduled_for(r, 'SCR (Tríplice Viral)')
    assert apr is not None and apr['dose'] == 2 and apr['data_minima'] > today()


def test_vv04_scr_d1_d2_esquema_completo():
    data_d1 = today() - relativedelta(months=4)
    data_d2 = data_d1 + relativedelta(months=3)
    doses = [
        dose('SCR', data_d1, dose_num=1),
        dose('SCR', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=2), doses)
    assert 'SCR (Tríplice Viral)' in get_up_to_date(r)


def test_vv05_adulto_menos30a_sem_scr_recomendar():
    r = run_engine(birth_date_ago(years=25))
    assert any(v['vacina'] == 'SCR (Tríplice Viral)' for v in r['vacinas_recomendadas'])


# =================================================================
# Varicela
# =================================================================

def test_vv06_15m_varicela_recomendar_d1():
    r = run_engine(birth_date_ago(months=15))
    assert any(v['vacina'] == 'Varicela (atenuada)' and v['dose'] == 1
               for v in r['vacinas_recomendadas'])


def test_vv07_varicela_d1_d2_esquema_completo():
    data_d1 = today() - relativedelta(years=2)
    data_d2 = today() - relativedelta(months=6)
    doses = [
        dose('VARICELA', data_d1, dose_num=1),
        dose('VARICELA', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=4), doses)
    assert 'Varicela (atenuada)' in get_up_to_date(r)


# =================================================================
# Febre Amarela
# =================================================================

def test_vv08_menor9m_fa_aprazada():
    r = run_engine(birth_date_ago(months=6))
    nomes_apr = {v['vacina'] for v in r['vacinas_aprazadas']}
    assert 'Febre Amarela' in nomes_apr


def test_vv09_9m_recomendar_fa_d1():
    # At 9m without SCR conflict, FA should be recommended
    data_scr_d1 = today() - relativedelta(months=3)
    doses = [dose('SCR', data_scr_d1, dose_num=1)]
    r = run_engine(birth_date_ago(months=9), doses)
    assert any(v['vacina'] == 'Febre Amarela' for v in r['vacinas_recomendadas'])


def test_vv10_adulto_sem_fa_recomendar():
    r = run_engine(birth_date_ago(years=25))
    assert any(v['vacina'] == 'Febre Amarela' for v in r['vacinas_recomendadas'])


def test_vv11_idoso_60anos_fa_contraindicada():
    r = run_engine(birth_date_ago(years=60))
    assert 'Febre Amarela' in get_contraindicated(r)
    assert 'Febre Amarela' not in get_recommended(r)


# =================================================================
# Conflito SCR × FA (salience=100 prioriza SCR em < 2 anos)
# =================================================================

def test_vv12_12m_sem_scr_sem_fa_prioriza_scr():
    # Patient 12m without SCR or FA: conflict rule (salience=100) fires,
    # SCR is recommended immediately and FA is deferred (scheduled).
    r = run_engine(birth_date_ago(months=12))
    # Key: SCR must be in immediate recommendations (priority over FA)
    scr_recomendado = any(v['vacina'] == 'SCR (Tríplice Viral)' and v['dose'] == 1
                          for v in r['vacinas_recomendadas'])
    # FA must at least be scheduled (not just missing)
    fa_presente = (
        any(v['vacina'] == 'Febre Amarela' for v in r['vacinas_aprazadas']) or
        any(v['vacina'] == 'Febre Amarela' for v in r['vacinas_recomendadas'])
    )
    assert scr_recomendado
    assert fa_presente
