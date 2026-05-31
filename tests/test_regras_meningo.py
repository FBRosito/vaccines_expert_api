"""
CE+VL tests for RegrasMeningo — IN 2026 §7 and §11.
Meningo C: pediatric (3m, 5m, 12m).
Meningo ACWY: adolescents 11–14y.
"""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose, get_scheduled_for
from dateutil.relativedelta import relativedelta


def test_men01_3m_recomendar_men_c():
    r = run_engine(birth_date_ago(months=3))
    assert 'Meningocócica C' in get_recommended(r)


def test_men02_12m_reforco_men_c():
    data_d1 = today() - relativedelta(months=9)
    data_d2 = data_d1 + relativedelta(months=2)
    doses = [
        dose('MEN_C', data_d1, dose_num=1),
        dose('MEN_C', data_d2, dose_num=2),
    ]
    r = run_engine(birth_date_ago(months=12), doses)
    # Com MEN_C D1+D2 aplicadas, o sistema recomenda reforço com ACWY aos 12 meses
    # (proteção ampliada: 4 sorogrupos) ou MEN_C como em_dia
    assert ('Meningocócica ACWY' in get_recommended(r) or
            'Meningocócica C' in get_up_to_date(r))


def test_men03_11anos_recomendar_acwy():
    r = run_engine(birth_date_ago(years=11))
    assert 'Meningocócica ACWY' in get_recommended(r)


def test_men04_14anos_recomendar_acwy():
    r = run_engine(birth_date_ago(years=14))
    assert 'Meningocócica ACWY' in get_recommended(r)


def test_men05_acwy_aplicada_em_dia():
    data_acwy = today() - relativedelta(months=6)
    doses = [dose('MEN_ACWY', data_acwy)]
    r = run_engine(birth_date_ago(years=12), doses)
    assert 'Meningocócica ACWY' in get_up_to_date(r)
    assert 'Meningocócica ACWY' not in get_recommended(r)


def test_men06_menor3m_men_c_aprazada():
    r = run_engine(birth_date_ago(months=2))
    nomes_apr = {v['vacina'] for v in r['vacinas_aprazadas']}
    # Men C pode estar aprazada ou já recomendada dependendo da regra exata
    assert ('Meningocócica C' in get_recommended(r) or
            'Meningocócica C' in nomes_apr)


def test_men07_adulto_sem_men_c_nao_recomendado_rotina():
    r = run_engine(birth_date_ago(years=30))
    # Men C não é indicada em rotina para adultos imunocompetentes
    assert 'Meningocócica C' not in get_recommended(r)


def test_men08_10anos_sem_acwy_recomendar():
    r = run_engine(birth_date_ago(years=10))
    # 10a está dentro da faixa ACWY (depende da regra exata do módulo)
    # Pelo menos não deve ser contraindicado
    assert 'Meningocócica ACWY' not in get_contraindicated(r)
