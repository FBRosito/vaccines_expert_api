"""
Comparação: Motor Especialista vs Baseline Literal IN 2026.

Baseline ingênuo implementa apenas as cláusulas explícitas da IN 2026,
omitindo as extensões documentadas via notas técnicas CTAI:
  - Influenza 10a–59a11m29d (extensão adultos)
  - COVID-19  20a–59a11m29d (extensão adultos)

Mesma coorte sintética do test_cohort.py (N=5.000, seed=42, sem doses).
Mesmo gabarito de referência (cohort_reference.py) com extensões CTAI.

Demonstra quantitativamente que o SE supera a implementação estritamente
normativa em Influenza e COVID-19 para a faixa etária adulta.
"""
import datetime
import random
from dateutil.relativedelta import relativedelta
from helpers import run_engine, get_recommended
from cohort_reference import gabarito_IN2026

random.seed(42)
today = datetime.date.today()

N_PACIENTES = 5000

# Mesmos matchers do test_cohort.py
VACINAS_AVALIADAS = [
    ('BCG',              lambda rec: 'BCG' in rec),
    ('Dengue',           lambda rec: 'Dengue' in rec),
    ('Influenza',        lambda rec: 'Influenza' in rec),
    ('COVID-19',         lambda rec: any('COVID' in v for v in rec)),
    ('Pneumocócica 23V', lambda rec: 'Pneumocócica 23V' in rec),
    ('Febre Amarela',    lambda rec: 'Febre Amarela' in rec),
]


def baseline_in2026_literal(data_nascimento):
    """
    Baseline ingênuo: somente IN 2026 §§1–19 sem notas CTAI.
    Retorna set de nomes de vacinas recomendadas.
    """
    delta = relativedelta(today, data_nascimento)
    anos = delta.years
    meses = delta.years * 12 + delta.months
    rec = set()

    if anos < 5:                   rec.add('BCG')
    if 10 <= anos < 15:            rec.add('Dengue')
    if meses >= 6 and anos < 6:    rec.add('Influenza')   # crianças (IN literal)
    if anos >= 60:                 rec.add('Influenza')   # idosos (IN literal)
    # Sem: Influenza 10–59a (extensão CTAI — omitida propositalmente)
    if meses >= 6 and anos < 5:    rec.add('COVID-19')    # crianças (IN literal)
    if anos >= 60:                 rec.add('COVID-19')    # idosos (IN literal)
    # Sem: COVID-19 20–59a (extensão CTAI — omitida propositalmente)
    if anos >= 60:                 rec.add('Pneumocócica 23V')
    if meses >= 9 and anos < 60:   rec.add('Febre Amarela')

    return rec


def gerar_paciente():
    dias_vida = random.randint(0, 80 * 365)
    return today - datetime.timedelta(days=dias_vida), []


def computar_metricas(resultados, vacina_ref, matcher, usar_baseline=False):
    """Computa P, R, F1, κ usando motor_rec ou baseline_rec."""
    tp = fp = fn = tn = 0
    for motor_rec, baseline_rec, ref_rec in resultados:
        rec = baseline_rec if usar_baseline else motor_rec
        pos = matcher(rec)
        ref_pos = vacina_ref in ref_rec
        if pos and ref_pos:       tp += 1
        elif pos and not ref_pos: fp += 1
        elif not pos and ref_pos: fn += 1
        else:                     tn += 1
    n = tp + fp + fn + tn
    precisao = tp / (tp + fp) if (tp + fp) else 1.0
    recall   = tp / (tp + fn) if (tp + fn) else 1.0
    f1       = (2 * precisao * recall / (precisao + recall)) if (precisao + recall) else 0.0
    po    = (tp + tn) / n if n else 1.0
    p_yes = (tp + fp) / n if n else 0.0
    r_yes = (tp + fn) / n if n else 0.0
    pe    = p_yes * r_yes + (1 - p_yes) * (1 - r_yes)
    kappa = (po - pe) / (1 - pe) if (1 - pe) > 0 else 1.0
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'F1': f1, 'κ': kappa}


def test_se_supera_baseline():
    """Motor SE domina baseline IN 2026 literal; Influenza e COVID mostram gap."""
    resultados = []
    for _ in range(N_PACIENTES):
        dn, doses = gerar_paciente()
        try:
            motor_rec = get_recommended(run_engine(dn, doses))
        except Exception:
            motor_rec = set()
        baseline_rec = baseline_in2026_literal(dn)
        ref = gabarito_IN2026(dn, doses)
        resultados.append((motor_rec, baseline_rec, ref['recomendadas']))

    print(f"\n{'Vacina':<20} {'F1_Baseline':>11} {'κ_Baseline':>10} "
          f"{'F1_SE':>7} {'κ_SE':>6}")
    print("-" * 60)

    falhas = []
    for vacina_ref, matcher in VACINAS_AVALIADAS:
        m_se = computar_metricas(resultados, vacina_ref, matcher, usar_baseline=False)
        m_bl = computar_metricas(resultados, vacina_ref, matcher, usar_baseline=True)

        print(f"{vacina_ref:<20} {m_bl['F1']:>11.3f} {m_bl['κ']:>10.3f} "
              f"{m_se['F1']:>7.3f} {m_se['κ']:>6.3f}")

        if m_se['F1'] < m_bl['F1']:
            falhas.append(
                f"{vacina_ref}: SE F1={m_se['F1']:.3f} < baseline F1={m_bl['F1']:.3f}"
            )

    assert not falhas, "SE inferior ao baseline em:\n" + "\n".join(falhas)
