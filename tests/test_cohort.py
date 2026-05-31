"""
Synthetic cohort simulation — N=5,000 patients with no vaccination history.
Patients with birth dates uniformly distributed over 0–80 years.
Compares expert system output against the IN 2026 reference + documented extensions.
Metrics: Precision, Recall, F1 and Cohen's κ per traceable vaccine.
Pass criteria: F1 >= 0.90 and κ >= 0.80 for all mapped vaccines.
"""
import datetime
import random
import pytest
from helpers import run_engine, get_recommended, get_contraindicated
from cohort_reference import gabarito_IN2026

random.seed(42)
today = datetime.date.today()

N_PACIENTES = 5000

# (nome_gabarito, motor_matcher_fn)
# motor_matcher_fn(motor_rec: set) -> bool
# COVID usa prefixo pois o motor emite nomes distintos por faixa etária:
#   crianças → 'COVID-19 (Pfizer ou Moderna)', adultos → 'COVID-19', idosos → 'COVID-19 (Reforço)'
VACINAS_AVALIADAS = [
    ('BCG',              lambda rec: 'BCG' in rec),
    ('Dengue',           lambda rec: 'Dengue' in rec),
    ('Influenza',        lambda rec: 'Influenza' in rec),
    ('COVID-19',         lambda rec: any('COVID' in v for v in rec)),
    ('Pneumocócica 23V', lambda rec: 'Pneumocócica 23V' in rec),
    ('Febre Amarela',    lambda rec: 'Febre Amarela' in rec),
]


def gerar_paciente():
    """
    Gera paciente sintético sem histórico vacinal.
    A coorte testa exclusivamente a lógica etária do motor,
    isolando-a da lógica de intervalos entre doses.
    """
    dias_vida = random.randint(0, 80 * 365)
    dn = today - datetime.timedelta(days=dias_vida)
    return dn, []


def computar_kappa(tp, fp, fn, tn):
    """Cohen's Kappa — agreement beyond chance (Landis & Koch 1977)."""
    n = tp + fp + fn + tn
    if n == 0:
        return 1.0
    po = (tp + tn) / n
    p_motor_yes = (tp + fp) / n
    p_ref_yes   = (tp + fn) / n
    pe = p_motor_yes * p_ref_yes + (1 - p_motor_yes) * (1 - p_ref_yes)
    return (po - pe) / (1 - pe) if (1 - pe) > 0 else 1.0


def computar_metricas(resultados, vacina_ref, motor_matcher):
    tp = fp = fn = tn = 0
    for motor_rec, motor_ci, ref_rec, ref_ci in resultados:
        motor_positivo = motor_matcher(motor_rec)
        ref_positivo = vacina_ref in ref_rec
        if motor_positivo and ref_positivo:
            tp += 1
        elif motor_positivo and not ref_positivo:
            fp += 1
        elif not motor_positivo and ref_positivo:
            fn += 1
        else:
            tn += 1
    precisao = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precisao * recall / (precisao + recall)) if (precisao + recall) > 0 else 0.0
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'Precisão': precisao, 'Recall': recall, 'F1': f1}


def test_cohort_f1_por_vacina():
    """F1 >= 0.90 and κ >= 0.80 for all vaccines traceable to IN 2026 across N=5,000 patients."""
    resultados = []
    for _ in range(N_PACIENTES):
        dn, doses = gerar_paciente()
        try:
            r = run_engine(dn, doses)
            motor_rec = get_recommended(r)
            motor_ci = get_contraindicated(r)
        except Exception:
            motor_rec = set()
            motor_ci = set()
        ref = gabarito_IN2026(dn, doses)
        resultados.append((motor_rec, motor_ci, ref['recomendadas'], ref['contraindicadas']))

    falhas = []
    for vacina_ref, motor_matcher in VACINAS_AVALIADAS:
        m = computar_metricas(resultados, vacina_ref, motor_matcher)
        f1 = m['F1']
        kappa = computar_kappa(m['TP'], m['FP'], m['FN'], m['TN'])
        print(f"\n{vacina_ref}: P={m['Precisão']:.3f} R={m['Recall']:.3f} "
              f"F1={f1:.3f} κ={kappa:.3f} "
              f"TP={m['TP']} FP={m['FP']} FN={m['FN']} TN={m['TN']}")
        if f1 < 0.90:
            falhas.append(f"{vacina_ref}: F1={f1:.3f} < 0.90")
        if kappa < 0.80:
            falhas.append(f"{vacina_ref}: κ={kappa:.3f} < 0.80")

    assert not falhas, "Vacinas abaixo do limiar F1 >= 0.90:\n" + "\n".join(falhas)
