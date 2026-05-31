"""CE+VL tests for RulesBCG — IN 2026 §1. Target: 0 to 4y 11m 29d."""
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date
from helpers import today, birth_date_ago, dose


def test_bcg01_nascido_hoje_recomendar():
    r = run_engine(today())
    assert 'BCG' in get_recommended(r)


def test_bcg02_27d_recomendar():
    r = run_engine(birth_date_ago(days=27))
    assert 'BCG' in get_recommended(r)


def test_bcg03_2anos_sem_bcg_recomendar():
    r = run_engine(birth_date_ago(years=2))
    assert 'BCG' in get_recommended(r)


def test_bcg04_4anos11m29d_recomendar():
    # 4a11m29d = ainda dentro da janela
    dn = today() - __import__('dateutil.relativedelta', fromlist=['relativedelta']).relativedelta(years=4, months=11, days=29)
    r = run_engine(dn)
    assert 'BCG' in get_recommended(r)


def test_bcg05_5anos_contraindica():
    r = run_engine(birth_date_ago(years=5))
    assert 'BCG' in get_contraindicated(r)
    assert 'BCG' not in get_recommended(r)


def test_bcg06_bcg_aplicado_ao_nascer_em_dia():
    data_bcg = today() - __import__('dateutil.relativedelta', fromlist=['relativedelta']).relativedelta(years=1)
    doses = [dose('BCG', data_bcg)]
    r = run_engine(birth_date_ago(years=1), doses)
    assert 'BCG' in get_up_to_date(r)
    assert 'BCG' not in get_recommended(r)


def test_bcg07_bcg_aplicado_nao_recomenda_novamente():
    data_bcg = birth_date_ago(years=3)
    doses = [dose('BCG', data_bcg)]
    r = run_engine(birth_date_ago(years=3), doses)
    assert 'BCG' not in get_recommended(r)


def test_bcg08_6anos_sem_bcg_contraindica():
    r = run_engine(birth_date_ago(years=6))
    assert 'BCG' in get_contraindicated(r)
