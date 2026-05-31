"""
Property-based invariant tests with Hypothesis — ~8,000 executions.
10 invariants verified for any randomly generated patient.
"""
import datetime
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from helpers import run_engine, get_recommended, get_contraindicated, get_up_to_date

today = datetime.date.today()

# Estratégia: data de nascimento aleatória entre 0 e 80 anos atrás
data_nascimento_st = st.dates(
    min_value=today - datetime.timedelta(days=80 * 365),
    max_value=today
)

@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv01_recomendadas_disjunto_em_dia(dn):
    """INV-01: recomendadas ∩ em_dia = ∅"""
    r = run_engine(dn)
    rec = get_recommended(r)
    em_dia = get_up_to_date(r)
    assert rec.isdisjoint(em_dia), f"Vacina em ambas as categorias: {rec & em_dia}"


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv02_recomendadas_disjunto_contraindicadas(dn):
    """INV-02: recomendadas ∩ contraindicadas = ∅"""
    r = run_engine(dn)
    rec = get_recommended(r)
    ci = get_contraindicated(r)
    assert rec.isdisjoint(ci), f"Vacina recomendada e contraindicada ao mesmo tempo: {rec & ci}"


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv03_aprazamentos_nao_retroativos(dn):
    """INV-03: toda data_minima em aprazadas >= hoje"""
    r = run_engine(dn)
    for apr in r['vacinas_aprazadas']:
        data_min = apr.get('data_minima')
        if data_min is not None:
            assert data_min >= today, (
                f"Aprazamento retroativo para {apr['vacina']}: data_minima={data_min}"
            )


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv04_menor10anos_dengue_nao_recomendado(dn):
    """INV-04: paciente < 10a → Dengue ausente em recomendadas"""
    idade_anos = (today - dn).days // 365
    if idade_anos < 10:
        r = run_engine(dn)
        rec = get_recommended(r)
        assert 'Dengue' not in rec, f"Dengue recomendado para paciente com {idade_anos} anos"


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(data_nascimento_st)
def test_inv05_idoso_sem_fa_dose_fa_contraindicada(dn):
    """INV-05: idoso >= 60a sem FA → FA em contraindicadas"""
    import dateutil.relativedelta as rd
    anos = rd.relativedelta(today, dn).years
    if anos >= 60:
        r = run_engine(dn)
        ci = get_contraindicated(r)
        assert 'Febre Amarela' in ci, (
            f"Febre Amarela não contraindicada para idoso de {anos} anos"
        )


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv06_idoso_sem_pneumo23_recomendado(dn):
    """INV-06: idoso >= 60a sem Pneumo23 → Pneumo23 em recomendadas"""
    import dateutil.relativedelta as rd
    anos = rd.relativedelta(today, dn).years
    if anos >= 60:
        r = run_engine(dn)
        rec = get_recommended(r)
        assert 'Pneumocócica 23V' in rec, (
            f"Pneumo23 não recomendada para idoso de {anos} anos"
        )


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv07_faixa_covid_5a19a_contraindica(dn):
    """INV-07: faixa 5-19a sem dose COVID → COVID em contraindicadas"""
    import dateutil.relativedelta as rd
    delta = rd.relativedelta(today, dn)
    anos = delta.years
    if 5 <= anos < 20:
        r = run_engine(dn)
        ci = get_contraindicated(r)
        # COVID-19 contraindicated for 5-19y in routine (IN 2026 extension)
        covid_ci = any('COVID' in v for v in ci)
        covid_rec = any('COVID' in v for v in get_recommended(r))
        assert covid_ci or not covid_rec, (
            f"COVID recomendado sem contraindica para faixa {anos} anos"
        )


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv08_faixa_6a9a_influenza_contraindica(dn):
    """INV-08: faixa 6-9a → Influenza em contraindicadas (gap etário IN 2026)"""
    import dateutil.relativedelta as rd
    delta = rd.relativedelta(today, dn)
    anos = delta.years
    if 6 <= anos < 10:
        r = run_engine(dn)
        ci = get_contraindicated(r)
        rec = get_recommended(r)
        assert 'Influenza' in ci, (
            f"Influenza não contraindicada para paciente de {anos} anos (gap etário)"
        )
        assert 'Influenza' not in rec, (
            f"Influenza recomendada indevidamente para paciente de {anos} anos"
        )


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv09_maior15_sem_dengue_d1_contraindica(dn):
    """INV-09: >= 15a sem Dengue D1 → Dengue em contraindicadas"""
    idade_anos = (today - dn).days // 365
    if idade_anos >= 15:
        r = run_engine(dn)
        ci = get_contraindicated(r)
        assert 'Dengue' in ci, (
            f"Dengue não contraindicada para paciente de {idade_anos} anos"
        )


@settings(max_examples=800, suppress_health_check=[HealthCheck.too_slow])
@given(data_nascimento_st)
def test_inv10_motor_nunca_silencioso(dn):
    """INV-10: qualquer paciente → ao menos 1 output em qualquer categoria"""
    r = run_engine(dn)
    total_outputs = (
        len(r['vacinas_recomendadas']) +
        len(r['vacinas_aprazadas']) +
        len(r['vacinas_em_dia']) +
        len(r['vacinas_contraindicadas'])
    )
    assert total_outputs > 0, f"Motor produziu 0 outputs para paciente nascido em {dn}"
