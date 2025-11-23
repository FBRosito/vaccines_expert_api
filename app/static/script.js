// --- CONFIGURAÇÃO: Opções de Dose por Vacina ---
const vaccineConfig = {
    'bcg': { apiCode: 'BCG', doses: [{ label: "Dose Única", value: 1 }] },
    'hepb': { apiCode: 'HEPATITE_B', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }] },
    'penta': { apiCode: 'PENTA', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }] },
    'dtp': { apiCode: 'DTP', doses: [{ label: "1º Reforço", value: 1 }, { label: "2ª Dose", value: 2 }] },
    'vip': { apiCode: 'VIP', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }, { label: "Reforço", value: 4 }] },
    'rota': { apiCode: 'VORH', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }] },
    'pneumo': { apiCode: 'PNEUMO10', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "Reforço", value: 3 }] },
    'meningo': { apiCode: 'MEN_C', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "Reforço", value: 3 }] },
    'meningo_acwy': { apiCode: 'MEN_ACWY', doses: [{ label: "Dose Única", value: 1 }] },
    'fa': { apiCode: 'FEBRE_AMARELA', doses: [{ label: "1ª Dose", value: 1 }, { label: "Reforço", value: 2 }, { label: "Única", value: "Única" }] },
    'scr': { apiCode: 'SCR', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }] },
    'tetra': { apiCode: 'TETRAVIRAL', doses: [{ label: "Dose Única", value: 1 }] },
    'varicela': { apiCode: 'VARICELA', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }] },
    'hepa': { apiCode: 'HEPATITE_A', doses: [{ label: "Dose Única", value: 1 }] },
    'hpv': { apiCode: 'HPV', doses: [{ label: "Dose Única", value: 1 }] },
    'dt': { apiCode: 'dT', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }, { label: "Reforço", value: "Reforço" }] },
    'influenza': { apiCode: 'INFLUENZA', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "Dose Única/Anual", value: "Única" }] },
    'covid': { apiCode: 'COVID19', doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }] },
};

// --- NAVEGAÇÃO SPA ---
function mudarTela(tela) {
    const viewNovo = document.getElementById('view-novo');
    const viewRegistros = document.getElementById('view-registros');
    const navNovo = document.getElementById('nav-novo');
    const navRegistros = document.getElementById('nav-registros');

    if (tela === 'novo') {
        viewNovo.classList.remove('hidden');
        viewRegistros.classList.add('hidden');
        navNovo.classList.add('active');
        navRegistros.classList.remove('active');
    } else {
        viewNovo.classList.add('hidden');
        viewRegistros.classList.remove('hidden');
        navNovo.classList.remove('active');
        navRegistros.classList.add('active');
        carregarRegistros();
    }
}

// --- LISTAGEM DE REGISTROS ---
async function carregarRegistros() {
    const tbody = document.getElementById('table-body');
    
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px; color: var(--text-muted);"><i class="ph ph-spinner ph-spin"></i> Carregando histórico...</td></tr>';

    try {
        const response = await fetch('/api/auditoria');
        
        if (!response.ok) {
            const erroJson = await response.json().catch(() => ({}));
            throw new Error(erroJson.erro || erroJson.error || `Erro do servidor (${response.status})`);
        }

        const registros = await response.json();

        if (!Array.isArray(registros)) {
            throw new Error("Formato de resposta inválido recebido da API.");
        }

        tbody.innerHTML = '';

        if (registros.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 30px; color: var(--text-muted);"><i>Nenhum registro de auditoria encontrado no banco de dados.</i></td></tr>';
            return;
        }

        registros.forEach(reg => {
            const dataLog = new Date(reg.timestamp).toLocaleString('pt-BR', {
                day: '2-digit', month: '2-digit', year: 'numeric', 
                hour: '2-digit', minute: '2-digit'
            });

            const dataNascObj = new Date(reg.paciente_data_nascimento + 'T12:00:00');
            const nascFmt = dataNascObj.toLocaleDateString('pt-BR');
            
            const sexoClass = reg.paciente_sexo === 'Masculino' ? 'M' : 'F';
            const sexoLabel = reg.paciente_sexo === 'Masculino' ? 'Masc' : 'Fem';

            const resultadoStr = encodeURIComponent(JSON.stringify(reg.response_output));

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong style="color: var(--primary)">#${reg.id}</strong></td>
                <td>${dataLog}</td>
                <td>
                    <div style="font-weight:600; font-size: 0.9rem">${nascFmt}</div>
                    <div style="margin-top:4px"><span class="badge-sexo ${sexoClass}">${sexoLabel}</span></div>
                </td>
                <td>
                    <div style="font-size:1.1rem; font-weight:700; color: var(--text-main)">${reg.numero_doses_recebidas}</div>
                    <div class="text-muted" style="font-size:0.75rem">vacinas informadas</div>
                </td>
                <td>
                    <button class="btn-small" onclick="verDetalhes('${resultadoStr}')">
                        <i class="ph-bold ph-eye"></i> Ver Análise
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error("Erro ao buscar registros:", error);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color: var(--danger); padding: 20px;"><i class="ph-bold ph-warning-circle"></i> ${error.message}</td></tr>`;
    }
}

function verDetalhes(resultadoEncoded) {
    try {
        const resultado = JSON.parse(decodeURIComponent(resultadoEncoded));
        mostrarResultado(resultado);
    } catch (e) {
        console.error(e);
        alert("Não foi possível abrir os detalhes deste registro.");
    }
}

// --- FUNÇÕES DE FORMULÁRIO ---
document.querySelectorAll('.vaccine-check').forEach(check => {
    check.addEventListener('change', function() {
        const vacinaId = this.id.replace('check-', '');
        const cardId = 'card-' + vacinaId;
        const card = document.getElementById(cardId);
        const list = document.getElementById(`list-${vacinaId}`);
        if (this.checked) {
            card.classList.add('active');
            if (list && list.children.length === 0) addDose(vacinaId);
        } else {
            card.classList.remove('active');
        }
    });
});

function toggleVaccine(vacinaId) {
    const checkbox = document.getElementById(`check-${vacinaId}`);
    if (event.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event('change'));
    }
}

function addDose(vacinaId) {
    const listContainer = document.getElementById(`list-${vacinaId}`);
    const config = vaccineConfig[vacinaId];
    if (!config) return;

    const row = document.createElement('div');
    row.className = 'dose-row';
    
    const optionsHtml = config.doses.map(d => 
        `<option value="${d.value}">${d.label}</option>`).join('');

    row.innerHTML = `
        <input type="date" class="input-date" required>
        <select class="input-dose">${optionsHtml}</select>
        <button type="button" class="btn-remove-dose" onclick="this.parentElement.remove()" title="Remover">
            <i class="ph-bold ph-trash"></i>
        </button>
    `;
    listContainer.appendChild(row);
}

async function analisarVacinas() {
    const btn = document.getElementById('btn-analisar');
    const nascimentoInput = document.getElementById('nascimento').value;
    const sexoInput = document.getElementById('sexo').value;

    if (!nascimentoInput || !sexoInput) {
        alert("Por favor, preencha os dados obrigatórios (Nascimento e Sexo).");
        return;
    }

    const sexoMapeado = sexoInput === 'M' ? 'Masculino' : 'Feminino';
    const carteiraVacinacao = [];
    
    Object.keys(vaccineConfig).forEach(id => {
        const checkbox = document.getElementById(`check-${id}`);
        if (checkbox && checkbox.checked) {
            const rows = document.querySelectorAll(`#list-${id} .dose-row`);
            rows.forEach(row => {
                const dataVal = row.querySelector('.input-date').value;
                let doseVal = row.querySelector('.input-dose').value;

                if (dataVal) {
                     if (!isNaN(doseVal)) doseVal = parseInt(doseVal);
                     carteiraVacinacao.push({
                        vacina_codigo: vaccineConfig[id].apiCode,
                        data_aplicacao: dataVal,
                        dose: doseVal
                    });
                }
            });
        }
    });

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="ph ph-spinner ph-spin"></i> Processando...';

    try {
        const payload = {
            paciente: { data_nascimento: nascimentoInput, sexo: sexoMapeado },
            carteira_vacinacao: carteiraVacinacao
        };

        const response = await fetch('/api/simulador/plano-vacinal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.erro || err.error || "Erro desconhecido no servidor");
        }

        const data = await response.json();
        mostrarResultado(data);

    } catch (error) {
        console.error(error);
        alert("Erro: " + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
    }
}

function mostrarResultado(data) {
    const modal = document.getElementById('resultado-card');
    const contentArea = modal.querySelector('.result-scroll-area');
    let htmlContent = '';

    const renderBlock = (list, typeClass, title, iconClass) => {
        if (list && list.length > 0) {
            return `
                <div class="result-group ${typeClass}">
                    <h3><i class="${iconClass}"></i> ${title}</h3>
                    ${list.map(v => `
                        <div class="result-item ${typeClass}">
                            <h4>${v.vacina}</h4>
                            <div class="meta">
                                ${v.dose ? `<span><strong>Dose:</strong> ${v.dose}</span>` : ''}
                                ${v.data_recomendada ? `<span><strong>Data:</strong> ${new Date(v.data_recomendada).toLocaleDateString('pt-BR', { timeZone: 'UTC' })}</span>` : ''}
                                ${v.motivo ? `<span><strong>Motivo:</strong> ${v.motivo}</span>` : ''}
                            </div>
                            <p class="desc">${v.explicacao}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        return '';
    };

    data.vacinas_recomendadas = data.vacinas_recomendadas || [];
    data.vacinas_aprazadas = data.vacinas_aprazadas || [];
    data.vacinas_contraindicadas = data.vacinas_contraindicadas || [];
    data.vacinas_em_dia = data.vacinas_em_dia || [];

    htmlContent += renderBlock(data.vacinas_recomendadas, 'type-green', 'Tomar Agora', 'ph-fill ph-check-circle');
    htmlContent += renderBlock(data.vacinas_aprazadas, 'type-yellow', 'Agendadas (Futuro)', 'ph-fill ph-clock');
    htmlContent += renderBlock(data.vacinas_contraindicadas, 'type-red', 'Contraindicadas', 'ph-fill ph-prohibit');
    htmlContent += renderBlock(data.vacinas_em_dia, 'type-blue', 'Em Dia', 'ph-fill ph-thumbs-up');

    if (htmlContent === '') {
        htmlContent = '<p style="text-align:center; padding: 20px; color: var(--text-muted);">Nenhuma recomendação específica encontrada.</p>';
    }

    contentArea.innerHTML = htmlContent;

    modal.classList.remove('hidden');

    setTimeout(() => {
        if (contentArea) {
            contentArea.scrollTop = 0;
        }
    }, 10);
}

function fecharModal() {
    document.getElementById('resultado-card').classList.add('hidden');
}