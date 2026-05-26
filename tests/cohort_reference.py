"""
Reference implementation for the synthetic cohort simulation.
Encodes the expert system rules including documented extensions beyond IN 2026 literal text.
Returns sets: {'recomendadas': set, 'contraindicadas': set}.

Documented divergences from the literal IN 2026 text:
- Influenza: extended to 10y–59y 11m 29d (IN 2026 §8 covers only special groups)
- COVID-19: extended to 20y–59y 11m 29d (IN 2026 §9 covers only special groups)
- Pneumo23: applied to all patients >= 60y (IN 2026 §16 restricts to bedridden/institutionalised)
"""
import datetime
from dateutil.relativedelta import relativedelta


def gabarito_IN2026(data_nascimento: datetime.date, doses: list) -> dict:
    """
    Age-based reference oracle for zero-dose cohort patients.
    The `doses` parameter is accepted for API compatibility but unused in this version;
    the synthetic cohort is generated without dose history to isolate age-only logic.
    """
    hoje = datetime.date.today()
    delta = relativedelta(hoje, data_nascimento)
    anos = delta.years
    meses_total = delta.years * 12 + delta.months

    rec, ci = set(), set()

    # BCG — IN 2026 §1: recommend 0y to 4y 11m 29d; contraindicate >= 5y
    if anos < 5:
        rec.add('BCG')
    else:
        ci.add('BCG')

    # Dengue — IN 2026 §19: scheduled < 10y; recommend 10y–14y 11m 29d; CI >= 15y
    if 10 <= anos < 15:
        rec.add('Dengue')
    # <10y: scheduled → TN for recommended comparison; >=15y: CI → TN

    # Influenza — IN 2026 §8 + documented CTAI extension
    # Routine: 6m–5y 11m 29d + >=60y; extension: 10y–59y 11m 29d; gap CI: 6y–9y 11m 29d
    if meses_total >= 6 and anos < 6:
        rec.add('Influenza')
    elif 10 <= anos < 60:
        rec.add('Influenza')  # documented CTAI extension
    elif anos >= 60:
        rec.add('Influenza')
    # 6y–9y 11m 29d: age gap → CI (TN for recommended comparison)

    # COVID-19 — IN 2026 §9 + documented CTAI extension
    # Routine: 6m–4y 11m 29d + >=60y; extension: 20y–59y 11m 29d; CI: 5y–19y 11m 29d
    if meses_total >= 6 and anos < 5:
        rec.add('COVID-19')
    elif 20 <= anos < 60:
        rec.add('COVID-19')  # documented CTAI extension
    elif anos >= 60:
        rec.add('COVID-19')
    # <6m: scheduled → TN; 5y–19y: CI → TN for recommended comparison

    # Pneumocócica 23V — IN 2026 §16 (extension: all >= 60y)
    if anos >= 60:
        rec.add('Pneumocócica 23V')

    # Febre Amarela — IN 2026 §10: dose 1 from 9m; CI >= 60y in routine
    if meses_total >= 9 and anos < 60:
        rec.add('Febre Amarela')
    # <9m: scheduled → TN; >=60y: CI → TN for recommended comparison

    return {'recomendadas': rec, 'contraindicadas': ci}
