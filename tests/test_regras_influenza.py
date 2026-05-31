"""
CE+VL tests for RegrasInfluenza — IN 2026 §8.
Routine: children 6m–5y11m29d + elderly ≥60y.
Extension (beyond literal IN): adolescents/adults 10–59y.
First-time vaccination: 2 doses with a 30-day interval.
"""
import datetime
from helpers import run_engine, get_recommended, get_scheduled, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


# INF-01  VL: 5m29d sem dose → AgendamentoFuturo (data = 6m de vida)
def test_inf01_menor6m_aprazada():
    dn = birth_date_ago(months=5, days=29)
    r = run_engine(dn)
    assert 'Influenza' not in get_recommended(r)
    apr = get_scheduled_for(r, 'Influenza')
    assert apr is not None
    assert apr['data_minima'] == dn + relativedelta(months=6)


# INF-02  VL: 6m0d sem dose → RecomendacaoImediata D1 primovacinação
def test_inf02_6m_recomendar_d1():
    r = run_engine(birth_date_ago(months=6))
    assert 'Influenza' in get_recommended(r)


# INF-03  CE: 2a sem dose → RecomendacaoImediata D1 primovacinação
def test_inf03_2anos_recomendar_d1():
    r = run_engine(birth_date_ago(years=2))
    assert 'Influenza' in get_recommended(r)


# INF-04  CE: 2a, D1 há 15d (mesmo ano) → AgendamentoFuturo D2
def test_inf04_d1_ha_15d_agendar_d2():
    data_d1 = today() - relativedelta(days=15)
    doses = [dose('INFLUENZA', data_d1)]
    r = run_engine(birth_date_ago(years=2), doses)
    apr = get_scheduled_for(r, 'Influenza')
    assert apr is not None
    assert apr['data_minima'] == data_d1 + relativedelta(days=30)


# INF-05  VL: D1 há 29d (mesmo ano) → ainda AgendamentoFuturo D2
def test_inf05_d1_ha_29d_ainda_agendar():
    data_d1 = today() - relativedelta(days=29)
    doses = [dose('INFLUENZA', data_d1)]
    r = run_engine(birth_date_ago(years=2), doses)
    assert get_scheduled_for(r, 'Influenza') is not None


# INF-06  VL: D1 há 30d (mesmo ano) → RecomendacaoImediata D2
def test_inf06_d1_ha_30d_recomendar_d2():
    data_d1 = today() - relativedelta(days=30)
    doses = [dose('INFLUENZA', data_d1)]
    r = run_engine(birth_date_ago(years=2), doses)
    assert any(v['vacina'] == 'Influenza' and v['dose'] == '2 (Primovacinação)'
               for v in r['vacinas_recomendadas'])


# INF-07  CE: 2a, D1 no ano anterior → RecomendacaoImediata anual
def test_inf07_d1_ano_anterior_recomendar_anual():
    data_d1 = today().replace(year=today().year - 1)
    doses = [dose('INFLUENZA', data_d1)]
    r = run_engine(birth_date_ago(years=2), doses)
    assert 'Influenza' in get_recommended(r)


# INF-08  CE: 2a, D1+D2 este ano → EsquemaCompleto
def test_inf08_d1_d2_este_ano_esquema_completo():
    data_d1 = today() - relativedelta(days=60)
    data_d2 = data_d1 + relativedelta(days=30)
    doses = [
        dose('INFLUENZA', data_d1, dose_num=1),
        dose('INFLUENZA', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=2), doses)
    assert 'Influenza' in get_up_to_date(r)


# INF-09  VL: 6a0d sem dose → Contraindicacao (gap 6–9a IN 2026)
def test_inf09_6anos_contraindica():
    r = run_engine(birth_date_ago(years=6))
    assert 'Influenza' in get_contraindicated(r)


# INF-10  VL: 9a11m sem dose → Contraindicacao
def test_inf10_9anos11m_contraindica():
    r = run_engine(birth_date_ago(years=9, months=11))
    assert 'Influenza' in get_contraindicated(r)


# INF-11  VL: 10a0d sem dose → RecomendacaoImediata (extensão IN — 10-59a)
def test_inf11_10anos_recomendar():
    r = run_engine(birth_date_ago(years=10))
    assert 'Influenza' in get_recommended(r)


# INF-12  VL: 59a11m sem dose → RecomendacaoImediata
def test_inf12_59anos11m_recomendar():
    r = run_engine(birth_date_ago(years=59, months=11))
    assert 'Influenza' in get_recommended(r)


# INF-13  VL: 60a0d sem dose → RecomendacaoImediata (idoso — IN 2026 §8)
def test_inf13_60anos_recomendar_idoso():
    r = run_engine(birth_date_ago(years=60))
    assert 'Influenza' in get_recommended(r)


# INF-14  CE: 65a, dose este ano → EsquemaCompleto
def test_inf14_65anos_dose_este_ano_em_dia():
    data_dose = today() - relativedelta(months=1)
    doses = [dose('INFLUENZA', data_dose)]
    r = run_engine(birth_date_ago(years=65), doses)
    assert 'Influenza' in get_up_to_date(r)
