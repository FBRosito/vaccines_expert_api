"""
CE+VL tests for RulesCovid19 — IN 2026 §9.
Routine: children 6m–4y11m29d + elderly ≥60y.
Extension (beyond literal IN): adults 20–59y (annual).
"""
from helpers import run_engine, get_recommended, get_scheduled, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


# COV-01  VL: 5m29d sem dose → AgendamentoFuturo (6m)
def test_cov01_menor6m_aprazada():
    dn = birth_date_ago(months=5, days=29)
    r = run_engine(dn)
    nomes = {v['vaccine'] for v in r['scheduled_vaccines']}
    assert any('COVID' in n for n in nomes)
    assert not any('COVID' in n for n in get_recommended(r))


# COV-02  VL: 6m sem dose → RecomendacaoImediata D1
def test_cov02_6m_recomendar_d1():
    r = run_engine(birth_date_ago(months=6))
    assert any('COVID' in v for v in get_recommended(r))


# COV-03  CE: 2a, Pfizer D1 há 3 semanas → AgendamentoFuturo D2 (D1+4sem)
def test_cov03_pfizer_d1_ha_3sem_agendar_d2():
    data_d1 = today() - relativedelta(weeks=3)
    doses = [dose('COVID19_PFIZER', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=2), doses)
    apr = get_scheduled_for(r, 'COVID-19 (Pfizer)')
    assert apr is not None and apr['dose'] == 2
    assert apr['min_date'] == data_d1 + relativedelta(weeks=4)


# COV-04  VL: Pfizer D1 há 28d → RecomendacaoImediata D2
def test_cov04_pfizer_d1_ha_28d_recomendar_d2():
    data_d1 = today() - relativedelta(days=28)
    doses = [dose('COVID19_PFIZER', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=2), doses)
    assert any(v['vaccine'] == 'COVID-19 (Pfizer)' and v['dose'] == 2
               for v in r['recommended_vaccines'])


# COV-05  CE: Pfizer D2 há 4 semanas → AgendamentoFuturo D3 (D2+8sem)
def test_cov05_pfizer_d2_ha_4sem_agendar_d3():
    data_d1 = today() - relativedelta(weeks=8)
    data_d2 = data_d1 + relativedelta(weeks=4)
    doses = [
        dose('COVID19_PFIZER', data_d1, dose_num=1),
        dose('COVID19_PFIZER', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=2), doses)
    apr = get_scheduled_for(r, 'COVID-19 (Pfizer)')
    assert apr is not None and apr['dose'] == 3
    assert apr['min_date'] == data_d2 + relativedelta(weeks=8)


# COV-06  VL: Pfizer D2 há 56d → RecomendacaoImediata D3
def test_cov06_pfizer_d2_ha_56d_recomendar_d3():
    data_d1 = today() - relativedelta(days=84)
    data_d2 = data_d1 + relativedelta(days=28)
    doses = [
        dose('COVID19_PFIZER', data_d1, dose_num=1),
        dose('COVID19_PFIZER', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=2), doses)
    assert any(v['vaccine'] == 'COVID-19 (Pfizer)' and v['dose'] == 3
               for v in r['recommended_vaccines'])


# COV-07  CE: Pfizer 3 doses → EsquemaCompleto
def test_cov07_pfizer_3doses_esquema_completo():
    data_d1 = today() - relativedelta(days=150)
    data_d2 = data_d1 + relativedelta(weeks=4)
    data_d3 = data_d2 + relativedelta(weeks=8)
    doses = [
        dose('COVID19_PFIZER', data_d1, dose_num=1),
        dose('COVID19_PFIZER', data_d2, dose_num=2),
        dose('COVID19_PFIZER', data_d3, dose_num=3),
    ]
    r = run_engine(birth_date_ago(years=2), doses)
    assert 'COVID-19 (Pfizer)' in get_up_to_date(r)


# COV-08  CE: 2a, Moderna D1 há 3 semanas → AgendamentoFuturo D2
def test_cov08_moderna_d1_ha_3sem_agendar_d2():
    data_d1 = today() - relativedelta(weeks=3)
    doses = [dose('COVID19_MODERNA', data_d1, dose_num=1)]
    r = run_engine(birth_date_ago(years=2), doses)
    apr = get_scheduled_for(r, 'COVID-19 (Moderna)')
    assert apr is not None and apr['dose'] == 2


# COV-09  CE: 2a, Moderna D1+D2 → EsquemaCompleto
def test_cov09_moderna_2doses_esquema_completo():
    data_d1 = today() - relativedelta(days=60)
    data_d2 = data_d1 + relativedelta(weeks=4)
    doses = [
        dose('COVID19_MODERNA', data_d1, dose_num=1),
        dose('COVID19_MODERNA', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(years=2), doses)
    assert 'COVID-19 (Moderna)' in get_up_to_date(r)


# COV-10  VL: 5a sem dose → Contraindicacao (5–19a fora da rotina)
def test_cov10_5anos_contraindica():
    r = run_engine(birth_date_ago(years=5))
    assert any('COVID-19' in v for v in get_contraindicated(r))
    assert not any('COVID-19' in v for v in get_recommended(r))


# COV-11  VL: 19a11m sem dose → Contraindicacao
def test_cov11_19anos11m_contraindica():
    r = run_engine(birth_date_ago(years=19, months=11))
    assert any('COVID-19' in v for v in get_contraindicated(r))


# COV-12  VL: 20a sem dose → RecomendacaoImediata (extensão além da IN)
def test_cov12_20anos_recomendar():
    r = run_engine(birth_date_ago(years=20))
    assert any('COVID-19' in v for v in get_recommended(r))


# COV-13  CE: 35a, dose há 11 meses → EsquemaCompleto (< 12m)
def test_cov13_35anos_dose_ha_11m_em_dia():
    data_dose = today() - relativedelta(months=11)
    doses = [dose('COVID19_PFIZER', data_dose)]
    r = run_engine(birth_date_ago(years=35), doses)
    assert any('COVID-19' in v for v in get_up_to_date(r))


# COV-14  VL: 35a, dose há 12 meses → RecomendacaoImediata (≥ 12m)
def test_cov14_35anos_dose_ha_12m_recomendar():
    data_dose = today() - relativedelta(months=12)
    doses = [dose('COVID19_PFIZER', data_dose)]
    r = run_engine(birth_date_ago(years=35), doses)
    assert any('COVID-19' in v for v in get_recommended(r))


# COV-15  VL: 59a11m, dose há 13m → RecomendacaoImediata
def test_cov15_59anos11m_dose_ha_13m_recomendar():
    data_dose = today() - relativedelta(months=13)
    doses = [dose('COVID19_PFIZER', data_dose)]
    r = run_engine(birth_date_ago(years=59, months=11), doses)
    assert any('COVID-19' in v for v in get_recommended(r))


# COV-16  VL: 60a sem dose → RecomendacaoImediata (idoso semestral — IN 2026 §9)
def test_cov16_60anos_recomendar_idoso():
    r = run_engine(birth_date_ago(years=60))
    assert any('COVID-19' in v for v in get_recommended(r))


# COV-17  CE: 65a, dose há 5 meses → EsquemaCompleto (< 6m)
def test_cov17_65anos_dose_ha_5m_em_dia():
    data_dose = today() - relativedelta(months=5)
    doses = [dose('COVID19_PFIZER', data_dose)]
    r = run_engine(birth_date_ago(years=65), doses)
    assert any('COVID-19' in v for v in get_up_to_date(r))


# COV-18  VL: 65a, dose há 6 meses → RecomendacaoImediata
def test_cov18_65anos_dose_ha_6m_recomendar():
    data_dose = today() - relativedelta(months=6)
    doses = [dose('COVID19_PFIZER', data_dose)]
    r = run_engine(birth_date_ago(years=65), doses)
    assert any('COVID-19' in v for v in get_recommended(r))
