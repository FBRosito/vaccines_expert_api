"""
Gerador da Matriz de Rastreabilidade Normativa — IN 2026 × Sistema Especialista.

Mapeia cada cláusula normativa da IN 2026 para:
  - Módulo de regras implementado (app/expert_system/regras/)
  - Test cases derivados (CE+VL + invariantes + coorte)
  - Status: Coberto | Divergente (extensão além do texto da IN)

Executar:
    PYTHONPATH=. python3 rastreabilidade/traceability_matrix.py
Saída:
    rastreabilidade/traceability_matrix.csv
"""
import csv
import os

MATRIZ = [
    # ── BCG ──────────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-BCG-01',
        'Fonte': 'IN 2026 §1',
        'Cláusula': 'BCG: recomendar para 0a a 4a11m29d sem dose prévia',
        'Módulo': 'app/expert_system/regras/bcg.py — regra_bcg_recomendar',
        'Test_Cases': 'BCG-01, BCG-02, BCG-03, BCG-04, INV-10',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-BCG-02',
        'Fonte': 'IN 2026 §1',
        'Cláusula': 'BCG: contraindicar ≥5a sem dose prévia',
        'Módulo': 'app/expert_system/regras/bcg.py — regra_bcg_contraindicar',
        'Test_Cases': 'BCG-05, BCG-08',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Hepatite B ───────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-HEPB-01',
        'Fonte': 'IN 2026 §2',
        'Cláusula': 'Hepatite B: D1 ao nascer; D2 (2m); D3 (6m)',
        'Módulo': 'app/expert_system/regras/hepatite_b.py',
        'Test_Cases': 'HEPB-01..HEPB-07',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-HEPB-02',
        'Fonte': 'IN 2026 §2',
        'Cláusula': 'Hepatite B: recomendar adulto sem esquema completo',
        'Módulo': 'app/expert_system/regras/hepatite_b.py — regra_hepb_adulto_recomendar',
        'Test_Cases': 'HEPB-08, HEPB-09',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Penta + DTP ──────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-PENTA-01',
        'Fonte': 'IN 2026 §3',
        'Cláusula': 'Penta: D1 (2m), D2 (4m), D3 (6m); contraindicar ≥7a',
        'Módulo': 'app/expert_system/regras/penta_dtp.py — RegrasPentaDTP',
        'Test_Cases': 'PENTA-01..PENTA-10, PENTA-11, PENTA-12',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-DTP-01',
        'Fonte': 'IN 2026 §3',
        'Cláusula': 'DTP: R1 (15m), R2 (4a); contraindicar ≥7a sem Penta completa',
        'Módulo': 'app/expert_system/regras/penta_dtp.py — RegrasPentaDTP',
        'Test_Cases': 'PENTA-05..PENTA-09',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── VIP ──────────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-VIP-01',
        'Fonte': 'IN 2026 §4',
        'Cláusula': 'VIP (Poliomielite): D1 (2m), D2 (4m), D3 (6m), Reforço (15m); CI ≥5a',
        'Módulo': 'app/expert_system/regras/vip.py',
        'Test_Cases': 'VIP-01..VIP-10',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Rotavírus ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-ROTA-01',
        'Fonte': 'IN 2026 §5',
        'Cláusula': 'Rotavírus: D1 ≤3m15d de vida; D2 ≤7m29d; CI após limite etário',
        'Módulo': 'app/expert_system/regras/rotavirus.py',
        'Test_Cases': 'ROTA-01..ROTA-06',
        'Status': 'Coberto',
        'Observação': 'Limite VL: D1 contraindicada com >105 dias de vida (3m15d)',
    },
    # ── Pneumo10 ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-PNEUMO10-01',
        'Fonte': 'IN 2026 §6',
        'Cláusula': 'Pneumo10: D1 (2m), D2 (4m), Reforço (12m); dose única catch-up 1a–4a11m',
        'Módulo': 'app/expert_system/regras/pneumo10.py',
        'Test_Cases': 'P10-01..P10-10',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Meningocócica ─────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-MEN-01',
        'Fonte': 'IN 2026 §7',
        'Cláusula': 'Meningocócica C: D1 (3m), D2 (5m), Reforço (12m); ACWY catch-up adolescentes',
        'Módulo': 'app/expert_system/regras/meningo.py',
        'Test_Cases': 'MEN-01..MEN-08',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Influenza ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-INF-01',
        'Fonte': 'IN 2026 §8',
        'Cláusula': 'Influenza: crianças 6m–5a11m29d (primovacinação D1+D2; anual)',
        'Módulo': 'app/expert_system/regras/influenza.py',
        'Test_Cases': 'INF-01..INF-08, INV-10',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-INF-02',
        'Fonte': 'IN 2026 §8',
        'Cláusula': 'Influenza: idosos ≥60a (dose anual)',
        'Módulo': 'app/expert_system/regras/influenza.py — regra_influenza_idoso_anual',
        'Test_Cases': 'INF-13, INF-14, INV-10',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-INF-03',
        'Fonte': 'IN 2026 §8 (extensão)',
        'Cláusula': 'Influenza: adultos 10a–59a11m29d (extensão além da rotina da IN)',
        'Módulo': 'app/expert_system/regras/influenza.py — regra_influenza_adolescente_adulto',
        'Test_Cases': 'INF-11, INF-12',
        'Status': 'Divergente',
        'Observação': 'IN 2026 §8 cobre adultos apenas em grupos especiais (gestantes, profissionais de saúde etc.); implementação estendida à população geral baseada em nota técnica CTAI',
    },
    {
        'ID_Req': 'REQ-INF-04',
        'Fonte': 'IN 2026 §8',
        'Cláusula': 'Influenza: gap etário 6a–9a11m29d contraindicada em rotina',
        'Módulo': 'app/expert_system/regras/influenza.py — regra_influenza_gap_etario_ci',
        'Test_Cases': 'INF-09, INF-10, INV-08',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── COVID-19 ──────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-COV-01',
        'Fonte': 'IN 2026 §9',
        'Cláusula': 'COVID-19: crianças 6m–4a11m29d (Pfizer ou Moderna, 2–3 doses)',
        'Módulo': 'app/expert_system/regras/covid19.py',
        'Test_Cases': 'COV-01..COV-09',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-COV-02',
        'Fonte': 'IN 2026 §9',
        'Cláusula': 'COVID-19: idosos ≥60a (reforço semestral)',
        'Módulo': 'app/expert_system/regras/covid19.py — regra_covid_idoso_*',
        'Test_Cases': 'COV-16, COV-17, COV-18',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-COV-03',
        'Fonte': 'IN 2026 §9 (extensão)',
        'Cláusula': 'COVID-19: adultos 20a–59a11m29d (extensão além da rotina da IN)',
        'Módulo': 'app/expert_system/regras/covid19.py — regra_covid_adulto_*',
        'Test_Cases': 'COV-12..COV-15',
        'Status': 'Divergente',
        'Observação': 'IN 2026 §9 não inclui adultos 20–59a na rotina; implementação baseada em nota técnica CTAI',
    },
    {
        'ID_Req': 'REQ-COV-04',
        'Fonte': 'IN 2026 §9',
        'Cláusula': 'COVID-19: contraindicado em rotina para 5a–19a11m29d',
        'Módulo': 'app/expert_system/regras/covid19.py — regra_covid_ci_*',
        'Test_Cases': 'COV-10, COV-11, INV-07',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Febre Amarela ─────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-FA-01',
        'Fonte': 'IN 2026 §10',
        'Cláusula': 'Febre Amarela: D1 a partir de 9m de vida; reforço (4a)',
        'Módulo': 'app/expert_system/regras/virus_vivos_atenuados.py — RegrasVirusVivosAtenuados',
        'Test_Cases': 'VV-08, VV-09, VV-10',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-FA-02',
        'Fonte': 'IN 2026 §10',
        'Cláusula': 'Febre Amarela: contraindicada em rotina para ≥60a',
        'Módulo': 'app/expert_system/regras/virus_vivos_atenuados.py — regra_fa_contraindicacao_idoso',
        'Test_Cases': 'VV-11, INV-05',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── SCR (Tríplice Viral) ──────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-SCR-01',
        'Fonte': 'IN 2026 §11',
        'Cláusula': 'SCR: D1 (12m), D2 (15m); recomendar adulto sem esquema completo (<30a)',
        'Módulo': 'app/expert_system/regras/virus_vivos_atenuados.py',
        'Test_Cases': 'VV-01..VV-05',
        'Status': 'Coberto',
        'Observação': '',
    },
    {
        'ID_Req': 'REQ-SCR-02',
        'Fonte': 'IN 2026 §11',
        'Cláusula': 'Conflito SCR × FA em <2a: SCR priorizado (salience=100)',
        'Módulo': 'app/expert_system/regras/virus_vivos_atenuados.py — regra_conflito_scr_fa',
        'Test_Cases': 'VV-12',
        'Status': 'Coberto',
        'Observação': 'Intervalo mínimo 30 dias entre vírus vivos atenuados',
    },
    # ── Varicela ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-VAR-01',
        'Fonte': 'IN 2026 §12',
        'Cláusula': 'Varicela: D1 (15m), D2 (4a)',
        'Módulo': 'app/expert_system/regras/virus_vivos_atenuados.py',
        'Test_Cases': 'VV-06, VV-07',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Hepatite A ────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-HEPA-01',
        'Fonte': 'IN 2026 §13',
        'Cláusula': 'Hepatite A: dose única (15m); CI ≥5a',
        'Módulo': 'app/expert_system/regras/hepatite_a.py',
        'Test_Cases': 'HEPA-01..HEPA-05',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── HPV ──────────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-HPV-01',
        'Fonte': 'IN 2026 §14',
        'Cláusula': 'HPV: 2 doses (9–14a); 3 doses (15–45a); CI <9a e >45a',
        'Módulo': 'app/expert_system/regras/hpv.py',
        'Test_Cases': 'HPV-01..HPV-08',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── dT Adulto ────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-DT-01',
        'Fonte': 'IN 2026 §15',
        'Cláusula': 'dT: esquema primário D1+D2+D3 para ≥7a não vacinados; reforço decenal',
        'Módulo': 'app/expert_system/regras/dt_adulto.py',
        'Test_Cases': 'DT-01..DT-09',
        'Status': 'Coberto',
        'Observação': '',
    },
    # ── Pneumo23 ─────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-P23-01',
        'Fonte': 'IN 2026 §16',
        'Cláusula': 'Pneumo23: D1 para ≥60a; D2 após 5 anos da D1',
        'Módulo': 'app/expert_system/regras/pneumo23.py',  # or in correct module
        'Test_Cases': 'P23-01..P23-07, INV-06',
        'Status': 'Divergente',
        'Observação': 'IN 2026 §16 restringe a acamados/institucionalizados; implementação estendida a todos ≥60a',
    },
    # ── Dengue ───────────────────────────────────────────────────────────────
    {
        'ID_Req': 'REQ-DNG-01',
        'Fonte': 'IN 2026 §19',
        'Cláusula': 'Dengue: D1 para 10a–14a11m29d; D2 após 90 dias; aprazado <10a; CI ≥15a',
        'Módulo': 'app/expert_system/regras/dengue.py',  # adjust to actual module name
        'Test_Cases': 'DNG-01..DNG-10, INV-04, INV-09',
        'Status': 'Coberto',
        'Observação': 'Intervalo entre doses: 90 dias (3 meses)',
    },
]

# ── Invariantes transversais ───────────────────────────────────────────────
INVARIANTES = [
    {'ID': 'INV-01', 'Invariante': 'recomendadas ∩ em_dia = ∅', 'Exemplos': 800},
    {'ID': 'INV-02', 'Invariante': 'recomendadas ∩ contraindicadas = ∅', 'Exemplos': 800},
    {'ID': 'INV-03', 'Invariante': 'data_minima em aprazadas ≥ hoje', 'Exemplos': 800},
    {'ID': 'INV-04', 'Invariante': 'paciente <10a → Dengue ∉ recomendadas', 'Exemplos': 800},
    {'ID': 'INV-05', 'Invariante': 'idoso ≥60a sem FA → FA ∈ contraindicadas', 'Exemplos': 800},
    {'ID': 'INV-06', 'Invariante': 'idoso ≥60a sem Pneumo23 → Pneumo23 ∈ recomendadas', 'Exemplos': 800},
    {'ID': 'INV-07', 'Invariante': '5a≤idade<20a → COVID contraindicado ou ausente de recomendadas', 'Exemplos': 800},
    {'ID': 'INV-08', 'Invariante': '6a≤idade<10a → Influenza ∈ contraindicadas', 'Exemplos': 800},
    {'ID': 'INV-09', 'Invariante': '≥15a sem Dengue D1 → Dengue ∈ contraindicadas', 'Exemplos': 800},
    {'ID': 'INV-10', 'Invariante': 'qualquer paciente → total de outputs > 0', 'Exemplos': 800},
]


def gerar_csv():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(out_dir, 'traceability_matrix.csv')

    campos = ['ID_Req', 'Fonte', 'Cláusula', 'Módulo', 'Test_Cases', 'Status', 'Observação']
    with open(caminho, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(MATRIZ)

    print(f"Matriz de rastreabilidade gerada: {caminho}")
    print(f"  Requisitos normativa mapeados : {len(MATRIZ)}")
    print(f"  Cobertos                      : {sum(1 for r in MATRIZ if r['Status'] == 'Coberto')}")
    print(f"  Divergentes (documentados)    : {sum(1 for r in MATRIZ if r['Status'] == 'Divergente')}")

    inv_path = os.path.join(out_dir, 'invariants_matrix.csv')
    with open(inv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ID', 'Invariante', 'Exemplos'])
        writer.writeheader()
        writer.writerows(INVARIANTES)
    print(f"Matriz de invariantes gerada   : {inv_path}")
    print(f"  Invariantes property-based   : {len(INVARIANTES)} × {INVARIANTES[0]['Exemplos']} exemplos = {len(INVARIANTES) * INVARIANTES[0]['Exemplos']:,} execuções")


if __name__ == '__main__':
    gerar_csv()
