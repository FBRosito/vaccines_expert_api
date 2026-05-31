"""
CE+VL tests for RulesPneumo23 — IN 2026 §16.
Target: ≥60y (implemented for all; IN restricts to bedridden/institutionalized).
Schedule: 2 doses, minimum 5-year interval.
"""
from helpers import run_engine, get_recommended, get_scheduled, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


# P23-01  VL: 59a11m sem dose → Pneumo23 ausente em recomendadas
def test_p23_01_menor60_nao_recomendada():
    r = run_engine(birth_date_ago(years=59, months=11))
    assert 'Pneumocócica 23V' not in get_recommended(r)


# P23-02  VL: 60a sem dose → RecomendacaoImediata D1 (IN 2026 §16)
def test_p23_02_60anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=60))
    assert 'Pneumocócica 23V' in get_recommended(r)


# P23-03  CE: 65a sem dose → RecomendacaoImediata D1
def test_p23_03_65anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=65))
    assert 'Pneumocócica 23V' in get_recommended(r)


# P23-04  CE: 65a, D1 há 3 anos → AgendamentoFuturo D2 em D1+5anos
def test_p23_04_d1_ha_3anos_agendar_d2():
    data_d1 = today() - relativedelta(years=3)
    doses = [dose('PNEUMO23', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=65), doses)
    apr = get_scheduled_for(r, 'Pneumocócica 23V')
    assert apr is not None
    assert apr['dose'] == 2
    assert apr['min_date'] == data_d1 + relativedelta(years=5)


# P23-05  VL: D1 há 4a11m → ainda AgendamentoFuturo D2
def test_p23_05_d1_ha_4a11m_ainda_agendar():
    data_d1 = today() - relativedelta(years=4, months=11)
    doses = [dose('PNEUMO23', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=65), doses)
    apr = get_scheduled_for(r, 'Pneumocócica 23V')
    assert apr is not None and apr['dose'] == 2


# P23-06  VL: D1 há 5a → RecomendacaoImediata D2
def test_p23_06_d1_ha_5anos_recomendar_d2():
    data_d1 = today() - relativedelta(years=5)
    doses = [dose('PNEUMO23', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=65), doses)
    assert any(v['vaccine'] == 'Pneumocócica 23V' and v['dose'] == 2
               for v in r['recommended_vaccines'])


# P23-07  CE: D1+D2 → EsquemaCompleto
def test_p23_07_d1_d2_esquema_completo():
    data_d1 = today() - relativedelta(years=6)
    data_d2 = data_d1 + relativedelta(years=5)
    doses = [
        dose('PNEUMO23', data_d1, dose_num=1),
        dose('PNEUMO23', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=70), doses)
    assert 'Pneumocócica 23V' in get_up_to_date(r)
    assert 'Pneumocócica 23V' not in get_recommended(r)
