"""
Normative Traceability Matrix Generator — IN 2026 × Expert System.

Maps each IN 2026 regulatory clause to:
  - The rule module that implements it (app/expert_system/regras/)
  - Derived test cases (CE+VL + property-based invariants + synthetic cohort)
  - Status: Covered | Divergent/Documented (extension beyond the literal IN text)

Run:
    PYTHONPATH=. python3 rastreabilidade/traceability_matrix.py
Output:
    rastreabilidade/traceability_matrix.csv
"""
import csv
import os

MATRIZ = [
    # ── BCG ──────────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-BCG-01',
        'Source': 'IN 2026 §1',
        'Clause': 'BCG: recomendar para 0a a 4a11m29d sem dose prévia',
        'Module': 'app/expert_system/regras/bcg.py — rule_bcg_recommend_now',
        'Test_Cases': 'BCG-01, BCG-02, BCG-03, BCG-04, INV-10',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-BCG-02',
        'Source': 'IN 2026 §1',
        'Clause': 'BCG: contraindicar ≥5a sem dose prévia',
        'Module': 'app/expert_system/regras/bcg.py — rule_bcg_contraindicated_by_age',
        'Test_Cases': 'BCG-05, BCG-08',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Hepatite B ───────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-HEPB-01',
        'Source': 'IN 2026 §2',
        'Clause': 'Hepatite B: D1 ao nascer; D2 (2m); D3 (6m)',
        'Module': 'app/expert_system/regras/hepatite_b.py',
        'Test_Cases': 'HEPB-01..HEPB-07',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-HEPB-02',
        'Source': 'IN 2026 §2',
        'Clause': 'Hepatite B: recomendar adulto sem esquema completo',
        'Module': 'app/expert_system/regras/hepatite_b.py — rule_hep_b_over7_recommend_now',
        'Test_Cases': 'HEPB-08, HEPB-09',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Penta + DTP ──────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-PENTA-01',
        'Source': 'IN 2026 §3',
        'Clause': 'Penta: D1 (2m), D2 (4m), D3 (6m); contraindicar ≥7a',
        'Module': 'app/expert_system/regras/penta_dtp.py — RegrasPentaDTP',
        'Test_Cases': 'PENTA-01..PENTA-10, PENTA-11, PENTA-12',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-DTP-01',
        'Source': 'IN 2026 §3',
        'Clause': 'DTP: R1 (15m), R2 (4a); contraindicar ≥7a sem Penta completa',
        'Module': 'app/expert_system/regras/penta_dtp.py — RegrasPentaDTP',
        'Test_Cases': 'PENTA-05..PENTA-09',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── VIP ──────────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-VIP-01',
        'Source': 'IN 2026 §4',
        'Clause': 'VIP (Poliomielite): D1 (2m), D2 (4m), D3 (6m), Reforço (15m); CI ≥5a',
        'Module': 'app/expert_system/regras/vip.py',
        'Test_Cases': 'VIP-01..VIP-10',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Rotavírus ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-ROTA-01',
        'Source': 'IN 2026 §5',
        'Clause': 'Rotavírus: D1 ≤3m15d de vida; D2 ≤7m29d; CI após limite etário',
        'Module': 'app/expert_system/regras/rotavirus.py',
        'Test_Cases': 'ROTA-01..ROTA-06',
        'Status': 'Covered',
        'Notes': 'Age limit VL: D1 contraindicated after >105 days of life (3m15d)',
    },
    # ── Pneumo10 ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-PNEUMO10-01',
        'Source': 'IN 2026 §6',
        'Clause': 'Pneumo10: D1 (2m), D2 (4m), Reforço (12m); dose única catch-up 1a–4a11m',
        'Module': 'app/expert_system/regras/pneumo10.py',
        'Test_Cases': 'P10-01..P10-10',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Meningocócica ─────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-MEN-01',
        'Source': 'IN 2026 §7',
        'Clause': 'Meningocócica C: D1 (3m), D2 (5m), Reforço (12m); ACWY catch-up adolescentes',
        'Module': 'app/expert_system/regras/meningo.py',
        'Test_Cases': 'MEN-01..MEN-08',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Influenza ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-INF-01',
        'Source': 'IN 2026 §8',
        'Clause': 'Influenza: crianças 6m–5a11m29d (primovacinação D1+D2; anual)',
        'Module': 'app/expert_system/regras/influenza.py',
        'Test_Cases': 'INF-01..INF-08, INV-10',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-INF-02',
        'Source': 'IN 2026 §8',
        'Clause': 'Influenza: idosos ≥60a (dose anual)',
        'Module': 'app/expert_system/regras/influenza.py — rule_influenza_elderly_annual',
        'Test_Cases': 'INF-13, INF-14, INV-10',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-INF-03',
        'Source': 'IN 2026 §8 (extension)',
        'Clause': 'Influenza: adultos 10a–59a11m29d (extensão além da rotina da IN)',
        'Module': 'app/expert_system/regras/influenza.py — rule_influenza_adolescent_adult_annual',
        'Test_Cases': 'INF-11, INF-12',
        'Status': 'Divergent/Documented',
        'Notes': 'IN 2026 §8 covers adults only in special groups (pregnant women, healthcare workers, etc.); implementation extended to the general population based on CTAI technical note',
    },
    {
        'ID_Req': 'REQ-INF-04',
        'Source': 'IN 2026 §8',
        'Clause': 'Influenza: gap etário 6a–9a11m29d contraindicada em rotina',
        'Module': 'app/expert_system/regras/influenza.py — rule_influenza_outside_target_group',
        'Test_Cases': 'INF-09, INF-10, INV-08',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── COVID-19 ──────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-COV-01',
        'Source': 'IN 2026 §9',
        'Clause': 'COVID-19: crianças 6m–4a11m29d (Pfizer ou Moderna, 2–3 doses)',
        'Module': 'app/expert_system/regras/covid19.py',
        'Test_Cases': 'COV-01..COV-09',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-COV-02',
        'Source': 'IN 2026 §9',
        'Clause': 'COVID-19: idosos ≥60a (reforço semestral)',
        'Module': 'app/expert_system/regras/covid19.py — rule_covid_elderly_recommend',
        'Test_Cases': 'COV-16, COV-17, COV-18',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-COV-03',
        'Source': 'IN 2026 §9 (extension)',
        'Clause': 'COVID-19: adultos 20a–59a11m29d (extensão além da rotina da IN)',
        'Module': 'app/expert_system/regras/covid19.py — rule_covid_adult_recommend',
        'Test_Cases': 'COV-12..COV-15',
        'Status': 'Divergent/Documented',
        'Notes': 'IN 2026 §9 does not include adults 20–59y in routine; implementation based on CTAI technical note',
    },
    {
        'ID_Req': 'REQ-COV-04',
        'Source': 'IN 2026 §9',
        'Clause': 'COVID-19: contraindicado em rotina para 5a–19a11m29d',
        'Module': 'app/expert_system/regras/covid19.py — rule_covid_not_recommended_priority',
        'Test_Cases': 'COV-10, COV-11, INV-07',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Febre Amarela ─────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-FA-01',
        'Source': 'IN 2026 §10',
        'Clause': 'Febre Amarela: D1 a partir de 9m de vida; reforço (4a)',
        'Module': 'app/expert_system/regras/virus_vivos_atenuados.py — RegrasVirusVivosAtenuados',
        'Test_Cases': 'VV-08, VV-09, VV-10',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-FA-02',
        'Source': 'IN 2026 §10',
        'Clause': 'Febre Amarela: contraindicada em rotina para ≥60a',
        'Module': 'app/expert_system/regras/virus_vivos_atenuados.py — rule_fa_contraindicated_elderly',
        'Test_Cases': 'VV-11, INV-05',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── SCR (Tríplice Viral) ──────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-SCR-01',
        'Source': 'IN 2026 §11',
        'Clause': 'SCR: D1 (12m), D2 (15m); recomendar adulto sem esquema completo (<30a)',
        'Module': 'app/expert_system/regras/virus_vivos_atenuados.py',
        'Test_Cases': 'VV-01..VV-05',
        'Status': 'Covered',
        'Notes': '',
    },
    {
        'ID_Req': 'REQ-SCR-02',
        'Source': 'IN 2026 §11',
        'Clause': 'Conflito SCR × FA em <2a: SCR priorizado (salience=100)',
        'Module': 'app/expert_system/regras/virus_vivos_atenuados.py — rule_priority_scr_over_fa',
        'Test_Cases': 'VV-12',
        'Status': 'Covered',
        'Notes': 'Mandatory 30-day interval between live-attenuated virus vaccines',
    },
    # ── Varicela ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-VAR-01',
        'Source': 'IN 2026 §12',
        'Clause': 'Varicela: D1 (15m), D2 (4a)',
        'Module': 'app/expert_system/regras/virus_vivos_atenuados.py',
        'Test_Cases': 'VV-06, VV-07',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Hepatite A ────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-HEPA-01',
        'Source': 'IN 2026 §13',
        'Clause': 'Hepatite A: dose única (15m); CI ≥5a',
        'Module': 'app/expert_system/regras/hepatite_a.py',
        'Test_Cases': 'HEPA-01..HEPA-05',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── HPV ──────────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-HPV-01',
        'Source': 'IN 2026 §14',
        'Clause': 'HPV: 2 doses (9–14a); 3 doses (15–45a); CI <9a e >45a',
        'Module': 'app/expert_system/regras/hpv.py',
        'Test_Cases': 'HPV-01..HPV-08',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── dT Adulto ────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-DT-01',
        'Source': 'IN 2026 §15',
        'Clause': 'dT: esquema primário D1+D2+D3 para ≥7a não vacinados; reforço decenal',
        'Module': 'app/expert_system/regras/dt_adulto.py',
        'Test_Cases': 'DT-01..DT-09',
        'Status': 'Covered',
        'Notes': '',
    },
    # ── Pneumo23 ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-P23-01',
        'Source': 'IN 2026 §16',
        'Clause': 'Pneumo23: D1 para ≥60a; D2 após 5 anos da D1',
        'Module': 'app/expert_system/regras/pneumo23.py',
        'Test_Cases': 'P23-01..P23-07, INV-06',
        'Status': 'Divergent/Documented',
        'Notes': 'IN 2026 §16 restricts to bedridden/institutionalised patients; implementation extended to all ≥60y',
    },
    # ── Dengue ───────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-DNG-01',
        'Source': 'IN 2026 §19',
        'Clause': 'Dengue: D1 para 10a–14a11m29d; D2 após 90 dias; aprazado <10a; CI ≥15a',
        'Module': 'app/expert_system/regras/dengue.py',
        'Test_Cases': 'DNG-01..DNG-10, INV-04, INV-09',
        'Status': 'Covered',
        'Notes': 'Inter-dose interval: 90 days (3 months)',
    },
]

# ── Cross-cutting property-based invariants ────────────────────────────────
INVARIANTES = [
    {'ID': 'INV-01', 'Invariant': 'recommended ∩ up_to_date = ∅', 'Examples': 800},
    {'ID': 'INV-02', 'Invariant': 'recommended ∩ contraindicated = ∅', 'Examples': 800},
    {'ID': 'INV-03', 'Invariant': 'data_minima in scheduled ≥ today', 'Examples': 800},
    {'ID': 'INV-04', 'Invariant': 'patient <10y → Dengue ∉ recommended', 'Examples': 800},
    {'ID': 'INV-05', 'Invariant': 'elderly ≥60y without FA → FA ∈ contraindicated', 'Examples': 800},
    {'ID': 'INV-06', 'Invariant': 'elderly ≥60y without Pneumo23 → Pneumo23 ∈ recommended', 'Examples': 800},
    {'ID': 'INV-07', 'Invariant': '5y≤age<20y → COVID contraindicated or absent from recommended', 'Examples': 800},
    {'ID': 'INV-08', 'Invariant': '6y≤age<10y → Influenza ∈ contraindicated', 'Examples': 800},
    {'ID': 'INV-09', 'Invariant': '≥15y without Dengue D1 → Dengue ∈ contraindicated', 'Examples': 800},
    {'ID': 'INV-10', 'Invariant': 'any patient → total outputs > 0', 'Examples': 800},
]


def generate_csv():
    """Generate traceability_matrix.csv and invariants_matrix.csv in this directory."""
    out_dir = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(out_dir, 'traceability_matrix.csv')

    campos = ['ID_Req', 'Source', 'Clause', 'Module', 'Test_Cases', 'Status', 'Notes']
    with open(caminho, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(MATRIZ)

    print(f"Traceability matrix written : {caminho}")
    print(f"  Requirements mapped       : {len(MATRIZ)}")
    print(f"  Covered                   : {sum(1 for r in MATRIZ if r['Status'] == 'Covered')}")
    print(f"  Divergent/Documented      : {sum(1 for r in MATRIZ if r['Status'] == 'Divergent/Documented')}")

    inv_path = os.path.join(out_dir, 'invariants_matrix.csv')
    with open(inv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ID', 'Invariant', 'Examples'])
        writer.writeheader()
        writer.writerows(INVARIANTES)
    print(f"Invariants matrix written   : {inv_path}")
    print(f"  Property-based invariants : {len(INVARIANTES)} × {INVARIANTES[0]['Examples']} examples = {len(INVARIANTES) * INVARIANTES[0]['Examples']:,} executions")


if __name__ == '__main__':
    generate_csv()
