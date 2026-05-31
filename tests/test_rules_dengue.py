"""
CE+VL tests for RegrasDengue — IN 2026 §19.
Target: 10 to 14 years, 11 months and 29 days.
Schedule: 2 doses, minimum interval of 90 days.
"""
import pytest
from helpers import run_engine, get_recommended, get_scheduled, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


# ---------------------------------------------------------------------------
# DNG-01  VL: 9a11m sem dose → Dengue em aprazadas (10º aniversário)
# ---------------------------------------------------------------------------
def test_dng01_menor10_dengue_aprazada():
    dn = birth_date_ago(years=9, months=11)
    r = run_engine(dn)
    assert 'Dengue' not in get_recommended(r)
    assert 'Dengue' not in get_contraindicated(r)
    apr = get_scheduled_for(r, 'Dengue')
    assert apr is not None
    data_esperada = dn + relativedelta(years=10)
    assert apr['data_minima'] == data_esperada


# ---------------------------------------------------------------------------
# DNG-02  VL: 10a0d sem dose → RecomendacaoImediata D1  (IN 2026 §19)
# ---------------------------------------------------------------------------
def test_dng02_10anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=10))
    assert 'Dengue' in get_recommended(r)


# ---------------------------------------------------------------------------
# DNG-03  CE: 12a sem dose → RecomendacaoImediata D1
# ---------------------------------------------------------------------------
def test_dng03_12anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=12))
    assert 'Dengue' in get_recommended(r)


# ---------------------------------------------------------------------------
# DNG-04  VL: 14a11m sem dose → ainda RecomendacaoImediata D1
# ---------------------------------------------------------------------------
def test_dng04_14anos11m_recomendar_d1():
    dn = birth_date_ago(years=14, months=11)
    r = run_engine(dn)
    assert 'Dengue' in get_recommended(r)


# ---------------------------------------------------------------------------
# DNG-05  VL: 15a0d sem D1 → Contraindicacao (janela etária encerrada)
# ---------------------------------------------------------------------------
def test_dng05_15anos_contraindica_sem_d1():
    r = run_engine(birth_date_ago(years=15))
    assert 'Dengue' in get_contraindicated(r)
    assert 'Dengue' not in get_recommended(r)


# ---------------------------------------------------------------------------
# DNG-06  CE: 25a sem D1 → Contraindicacao
# ---------------------------------------------------------------------------
def test_dng06_25anos_contraindica_sem_d1():
    r = run_engine(birth_date_ago(years=25))
    assert 'Dengue' in get_contraindicated(r)


# ---------------------------------------------------------------------------
# DNG-07  CE: 12a, D1 há 1 mês → AgendamentoFuturo D2 (D1+90d)
# ---------------------------------------------------------------------------
def test_dng07_d1_ha_1mes_agendar_d2():
    data_d1 = today() - relativedelta(months=1)
    doses = [dose('DENGUE', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=12), doses)
    apr = get_scheduled_for(r, 'Dengue')
    assert apr is not None
    assert apr['dose'] == 2
    data_esperada = data_d1 + relativedelta(days=90)
    assert apr['data_minima'] == data_esperada


# ---------------------------------------------------------------------------
# DNG-08  VL: D1 há 89d → ainda AgendamentoFuturo D2
# ---------------------------------------------------------------------------
def test_dng08_d1_ha_89d_ainda_agendar():
    data_d1 = today() - relativedelta(days=89)
    doses = [dose('DENGUE', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=12), doses)
    apr = get_scheduled_for(r, 'Dengue')
    assert apr is not None
    assert apr['dose'] == 2


# ---------------------------------------------------------------------------
# DNG-09  VL: D1 há 90d → RecomendacaoImediata D2
# ---------------------------------------------------------------------------
def test_dng09_d1_ha_90d_recomendar_d2():
    data_d1 = today() - relativedelta(days=90)
    doses = [dose('DENGUE', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=12), doses)
    assert any(v['vacina'] == 'Dengue' and v['dose'] == 2
               for v in r['vacinas_recomendadas'])


# ---------------------------------------------------------------------------
# DNG-10  CE: D1+D2 completas → EsquemaCompleto
# ---------------------------------------------------------------------------
def test_dng10_d1_d2_esquema_completo():
    data_d1 = today() - relativedelta(days=200)
    data_d2 = data_d1 + relativedelta(days=90)
    doses = [
        dose('DENGUE', data_d1, dose_num=1),
        dose('DENGUE', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=12), doses)
    assert 'Dengue' in get_up_to_date(r)
    assert 'Dengue' not in get_recommended(r)
