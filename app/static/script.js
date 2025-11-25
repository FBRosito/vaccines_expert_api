// --- Dados e Doses por Vacina (Padrão RNDS/SIPNI) ---
// Códigos baseados na Tabela de Imunobiológicos do SIPNI/DataSUS
// URI do Sistema: http://www.saude.gov.br/fhir/rnds/CodeSystem/br-imunobiologico

const vaccineConfig = {
    'bcg': { 
        apiCode: '01', // BCG
        doses: [{ label: "Dose Única", value: 1 }] 
    },
    'hepb': { 
        apiCode: '06', // Hepatite B
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }] 
    },
    'penta': { 
        apiCode: '42', // Pentavalente (DTP/HB/Hib)
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }] 
    },
    'dtp': { 
        apiCode: '14', // DTP
        doses: [{ label: "1º Reforço", value: 1 }, { label: "2ª Dose", value: 2 }] 
    },
    'vip': { 
        apiCode: '22', // VIP (Poliomielite Inativada)
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }, { label: "Reforço", value: 4 }] 
    },
    'rota': { 
        apiCode: '41', // Rotavírus Humano
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }] 
    },
    'pneumo': { 
        apiCode: '17', // Pneumocócica 10V
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "Reforço", value: 3 }] 
    },
    'meningo': { 
        apiCode: '29', // Meningocócica C
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "Reforço", value: 3 }] 
    },
    'meningo_acwy': { 
        apiCode: '54', // Meningocócica ACWY
        doses: [{ label: "Dose Única", value: 1 }] 
    },
    'influenza': { 
        apiCode: '33', // Influenza (Geral)
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "Dose Única/Anual", value: "Única" }] 
    },
    'fa': { 
        apiCode: '05', // Febre Amarela
        doses: [{ label: "1ª Dose", value: 1 }, { label: "Reforço", value: 2 }, { label: "Única", value: "Única" }] 
    },
    'scr': { 
        apiCode: '21', // Tríplice Viral (SCR)
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }] 
    },
    'tetra': { 
        apiCode: '30', // Tetraviral (SCRV)
        doses: [{ label: "Dose Única", value: 1 }] 
    },
    'varicela': { 
        apiCode: '13', // Varicela
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }] 
    },
    'hepa': { 
        apiCode: '15', // Hepatite A
        doses: [{ label: "Dose Única", value: 1 }] 
    },
    'hpv': { 
        apiCode: '49', // HPV Quadrivalente
        doses: [{ label: "Dose Única", value: 1 }] 
    },
    'dt': { 
        apiCode: '37', // Dupla Adulto (dT)
        doses: [{ label: "1ª Dose", value: 1 }, { label: "2ª Dose", value: 2 }, { label: "3ª Dose", value: 3 }, { label: "Reforço", value: "Reforço" }] 
    },
    
    // --- COVID-19 (Códigos SIPNI Específicos) ---
    'covid_pfizer': { 
        apiCode: '103', // Comirnaty Pediátrica (6m a 4 anos)
        doses: [
            { label: "1ª Dose", value: 1 }, 
            { label: "2ª Dose", value: 2 }, 
            { label: "3ª Dose", value: 3 },
            { label: "Reforço/Anual", value: "Reforço Periódico" }
        ] 
    },
    'covid_moderna': { 
        apiCode: '107', // Spikevax (6m a 5 anos) - Código estimado/recente
        doses: [
            { label: "1ª Dose", value: 1 }, 
            { label: "2ª Dose", value: 2 },
            { label: "Reforço/Anual", value: "Reforço Periódico" }
        ] 
    }
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

// --- VISUALIZAÇÃO DE DETALHES ---
function verDetalhes(resultadoEncoded) {
    try {
        const fhirBundle = JSON.parse(decodeURIComponent(resultadoEncoded));
        
        // Converte o padrão FHIR para o objeto visual que o 'mostrarResultado' espera
        const dadosUI = adaptarRespostaFHIR(fhirBundle);
        
        mostrarResultado(dadosUI);

    } catch (e) {
        console.error(e);
        alert("Não foi possível processar os dados FHIR deste registro.");
    }
}

// --- ADAPTADOR FHIR (RNDS) -> UI ---
// Converte o Bundle FHIR complexo para o formato simples que a UI espera
function adaptarRespostaFHIR(bundle) {
    const resultado = {
        vacinas_recomendadas: [],
        vacinas_aprazadas: [],
        vacinas_contraindicadas: [],
        vacinas_em_dia: []
    };

    if (!bundle || !bundle.entry) return resultado;

    // Data de hoje para comparação (Formato YYYY-MM-DD para string comparison)
    const hoje = new Date();
    const hojeStr = hoje.toLocaleDateString('en-CA'); // Retorna YYYY-MM-DD

    bundle.entry.forEach(item => {
        const res = item.resource;
        
        if (res.resourceType === 'ImmunizationRecommendation') {
            const rec = res.recommendation[0];
            const status = rec.forecastStatus.coding[0].code; // 'due', 'contraindicated', 'complete'
            
            const vacinaNome = rec.vaccineCode.coding[0].display;
            const dose = rec.doseNumberString;
            const explicacao = rec.description;

            let dataRecomendada = null;
            let dataMinima = null;

            if (rec.dateCriterion) {
                rec.dateCriterion.forEach(c => {
                    const code = c.code.coding[0].code;
                    if (code === '30980-7') dataRecomendada = c.value; // Date forecast
                    if (code === '30981-5') dataMinima = c.value;   // Earliest date
                });
            }

            const objUI = {
                vacina: vacinaNome,
                dose: dose,
                explicacao: explicacao,
                data_recomendada: dataRecomendada,
                data_minima: dataMinima
            };

            if (status === 'due') {
                // Se 'due' (pendente), verificamos a data para separar em "Agora" ou "Futuro"
                if (dataRecomendada && dataRecomendada <= hojeStr) {
                    resultado.vacinas_recomendadas.push(objUI);
                } else {
                    resultado.vacinas_aprazadas.push(objUI);
                }
            } else if (status === 'contraindicated') {
                resultado.vacinas_contraindicadas.push(objUI);
            } else if (status === 'complete') {
                resultado.vacinas_em_dia.push(objUI);
            }
        }
    });

    // Ordena as aprazadas por data
    resultado.vacinas_aprazadas.sort((a, b) => {
        if (a.data_recomendada < b.data_recomendada) return -1;
        if (a.data_recomendada > b.data_recomendada) return 1;
        return 0;
    });

    return resultado;
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

    // 1. Validação de Campos Obrigatórios
    if (!nascimentoInput || !sexoInput) {
        alert("Por favor, preencha os dados obrigatórios (Nascimento e Sexo).");
        return;
    }

    // 2. Validação de Datas e Idade
    const dataNascimento = new Date(nascimentoInput + 'T00:00:00');
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);

    if (dataNascimento > hoje) {
        alert("Data de nascimento inválida: A data não pode ser no futuro.");
        return;
    }

    const diffAnos = hoje.getFullYear() - dataNascimento.getFullYear();
    const aniversarioPassou = (
        hoje.getMonth() > dataNascimento.getMonth() || 
        (hoje.getMonth() === dataNascimento.getMonth() && hoje.getDate() >= dataNascimento.getDate())
    );
    const idadeReal = aniversarioPassou ? diffAnos : diffAnos - 1;

    if (idadeReal > 130) {
        alert(`Data de nascimento inválida: A idade calculada (${idadeReal} anos) excede o limite aceitável.`);
        return;
    }

    // --- CONSTRUÇÃO DO PAYLOAD FHIR (BUNDLE) ---
    
    const fhirGender = sexoInput === 'M' ? 'male' : 'female';

    const fhirBundle = {
        resourceType: "Bundle",
        type: "collection",
        entry: []
    };

    fhirBundle.entry.push({
        resource: {
            resourceType: "Patient",
            gender: fhirGender,
            birthDate: nascimentoInput
        }
    });

    Object.keys(vaccineConfig).forEach(id => {
        const checkbox = document.getElementById(`check-${id}`);
        if (checkbox && checkbox.checked) {
            const rows = document.querySelectorAll(`#list-${id} .dose-row`);
            rows.forEach(row => {
                const dataVal = row.querySelector('.input-date').value;
                let doseVal = row.querySelector('.input-dose').value;

                if (dataVal) {
                    if (!isNaN(doseVal)) doseVal = parseInt(doseVal);

                    const immunizationResource = {
                        resourceType: "Immunization",
                        status: "completed",
                        vaccineCode: {
                            coding: [{
                                system: "http://www.saude.gov.br/fhir/rnds/CodeSystem/br-imunobiologico", 
                                code: vaccineConfig[id].apiCode,
                                display: id.toUpperCase().replace('_', ' ')
                            }]
                        },
                        occurrenceDateTime: dataVal,
                        protocolApplied: []
                    };

                    if (typeof doseVal === 'number') {
                        immunizationResource.protocolApplied.push({
                            doseNumberPositiveInt: doseVal
                        });
                    } else {
                        immunizationResource.protocolApplied.push({
                            doseNumberString: doseVal
                        });
                    }

                    fhirBundle.entry.push({
                        resource: immunizationResource
                    });
                }
            });
        }
    });

    // --- ENVIO DO PAYLOAD ---

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="ph ph-spinner ph-spin"></i> Processando...';

    try {
        const response = await fetch('/api/simulador/plano-vacinal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(fhirBundle) // Envia Bundle FHIR
        });

        if (!response.ok) {
            const err = await response.json();
            let msgErro = err.erros;
            if (typeof msgErro === 'object') {
                msgErro = JSON.stringify(msgErro, null, 2);
            }
            throw new Error(msgErro || "Erro desconhecido no servidor");
        }

        const bundleResposta = await response.json(); // Recebe Bundle FHIR
        
        // --- ADAPTAÇÃO FHIR PARA TELA ---
        const dadosParaTela = adaptarRespostaFHIR(bundleResposta);
        
        mostrarResultado(dadosParaTela);

    } catch (error) {
        console.error(error);
        alert("Erro na Análise: " + error.message);
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
                                ${v.explicacao ? `<span><strong>Motivo:</strong> ${v.explicacao}</span>` : ''}
                            </div>
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
