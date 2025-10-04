class SistemaConferencia {
    constructor() {
        this.baseURL = '/api';
        this.statusAtual = null; // Status fixo atual
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadData();
        
        // Focar no campo de código ao carregar a página
        document.getElementById('codigo-input').focus();
    }

    bindEvents() {
        // Importar rastreios
        document.getElementById('importar-btn').addEventListener('click', () => this.importarRastreios());
        
        // Bipar mercadoria
        document.getElementById('bipar-btn').addEventListener('click', () => this.biparMercadoria());
        document.getElementById('codigo-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.biparMercadoria();
            }
        });
        
        // Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Ações
        document.getElementById('resetar-sistema-btn').addEventListener('click', () => this.resetarSistema());
        document.getElementById('resetar-dashboard-btn').addEventListener('click', () => this.resetarDashboard());
        document.getElementById('atualizar-btn').addEventListener('click', () => this.loadData());
        
        // Copiar bipadas por status
        document.getElementById('copiar-coleta-btn').addEventListener('click', () => this.copiarBipadasPorStatus('coleta'));
        document.getElementById('copiar-insucesso-btn').addEventListener('click', () => this.copiarBipadasPorStatus('insucesso'));
        document.getElementById('copiar-sem-status-btn').addEventListener('click', () => this.copiarBipadasPorStatus('sem_status'));
        
        // Status buttons - agora para seleção fixa
        document.getElementById('status-coleta-btn').addEventListener('click', () => this.selecionarStatus('coleta'));
        document.getElementById('status-insucesso-btn').addEventListener('click', () => this.selecionarStatus('insucesso'));
        
        // Exportar Excel
        document.getElementById('exportar-excel-btn').addEventListener('click', () => this.showExportModal());
        document.getElementById('confirmar-export-btn').addEventListener('click', () => this.exportarExcel());
        document.getElementById('cancelar-export-btn').addEventListener('click', () => this.hideExportModal());
        document.getElementById('atualizar-dashboard-btn').addEventListener('click', () => this.forcarAtualizacaoDashboard());
        
        // Excluir faltantes em lote
        document.getElementById('excluir-faltantes-btn').addEventListener('click', () => this.excluirFaltantesSelecionados());
        
        // Fechar modal ao clicar fora
        document.getElementById('export-modal').addEventListener('click', (e) => {
            if (e.target.id === 'export-modal') {
                this.hideExportModal();
            }
        });
        
        // Auto-refresh das estatísticas a cada 30 segundos
        setInterval(() => this.loadEstatisticas(), 30000);
        
        // Auto-refresh do dashboard a cada 60 segundos
        setInterval(() => this.loadDashboard(), 60000);
    }

    async makeRequest(endpoint, options = {}) {
        this.showLoading();
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.erro || 'Erro na requisição');
            }
            
            return data;
        } catch (error) {
            this.showNotification(error.message, 'error');
            throw error;
        } finally {
            this.hideLoading();
        }
    }

    async loadData() {
        try {
            await Promise.all([
                this.loadEstatisticas(),
                this.loadDashboard(),
                this.loadFaltantes(),
                this.loadConferidas(),
                this.loadBipadas()
            ]);
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
        }
    }

    async loadEstatisticas() {
        try {
            const data = await this.makeRequest('/estatisticas');
            
            document.getElementById('total-esperados').textContent = data.total_esperados;
            document.getElementById('total-conferidos').textContent = data.total_conferidos;
            document.getElementById('total-pendentes').textContent = data.total_pendentes;
            document.getElementById('percentual-conferido').textContent = `${data.percentual_conferido}%`;
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
        }
    }

    async loadDashboard() {
        try {
            const data = await this.makeRequest('/dashboard');
            
            // Atualizar contadores por transportadora
            document.getElementById('jt-count').textContent = data.transportadoras['J&T'] || 0;
            document.getElementById('jadlog-count').textContent = data.transportadoras['JADLOG'] || 0;
            document.getElementById('dialogo-count').textContent = data.transportadoras['DIALOGO'] || 0;
            document.getElementById('correios-count').textContent = data.transportadoras['CORREIOS'] || 0;
            document.getElementById('correios-pa-count').textContent = data.transportadoras['CORREIOS PA'] || 0;
            document.getElementById('logan-count').textContent = data.transportadoras['LOGAN'] || 0;
            document.getElementById('favela-log-count').textContent = data.transportadoras['FAVELA LOG'] || 0;
            document.getElementById('sac-service-count').textContent = data.transportadoras['SAC SERVICE'] || 0;
            document.getElementById('dissudes-count').textContent = data.transportadoras['DISSUDES'] || 0;
            
            // Atualizar resumo do dia
            document.getElementById('total-hoje').textContent = data.total_hoje || 0;
            document.getElementById('coleta-hoje').textContent = data.coleta_hoje || 0;
            document.getElementById('insucesso-hoje').textContent = data.insucesso_hoje || 0;
            
            // Atualizar chart de status
            document.getElementById('coleta-hoje-chart').textContent = data.coleta_hoje || 0;
            document.getElementById('insucesso-hoje-chart').textContent = data.insucesso_hoje || 0;
            
            // Calcular e atualizar percentuais
            const total = data.total_hoje || 0;
            if (total > 0) {
                const coletaPercent = Math.round((data.coleta_hoje || 0) / total * 100);
                const insucessoPercent = Math.round((data.insucesso_hoje || 0) / total * 100);
                
                document.getElementById('coleta-percentage').textContent = `${coletaPercent}%`;
                document.getElementById('insucesso-percentage').textContent = `${insucessoPercent}%`;
            } else {
                document.getElementById('coleta-percentage').textContent = '0%';
                document.getElementById('insucesso-percentage').textContent = '0%';
            }
            
            // Atualizar barras de progresso das transportadoras
            this.updateTransportadoraBars(data.transportadoras);
            
            // Mostrar informações sobre o cache
            if (data.cache_info) {
                console.log(`Dashboard carregado do: ${data.cache_info.fonte}`);
                console.log(`Última atualização: ${data.cache_info.ultima_atualizacao}`);
            }
            
        } catch (error) {
            console.error('Erro ao carregar dashboard:', error);
            
            // Em caso de erro, zerar todos os contadores
            this.zerarContadoresDashboard();
        }
    }

    updateTransportadoraBars(transportadoras) {
        // Calcular o valor máximo para normalizar as barras
        const values = Object.values(transportadoras);
        const maxValue = Math.max(...values, 1); // Mínimo de 1 para evitar divisão por zero
        
        // Atualizar cada barra
        const transportadoraIds = ['jt', 'jadlog', 'dialogo', 'correios', 'correios-pa', 'logan', 'favela-log', 'sac-service', 'dissudes'];
        
        transportadoraIds.forEach(id => {
            const barElement = document.getElementById(`${id}-bar`);
            if (barElement) {
                const value = transportadoras[this.getTransportadoraName(id)] || 0;
                const percentage = (value / maxValue) * 100;
                barElement.style.width = `${percentage}%`;
            }
        });
    }

    getTransportadoraName(id) {
        const names = {
            'jt': 'J&T',
            'jadlog': 'JADLOG',
            'dialogo': 'DIALOGO',
            'correios': 'CORREIOS',
            'correios-pa': 'CORREIOS PA',
            'logan': 'LOGAN',
            'favela-log': 'FAVELA LOG',
            'sac-service': 'SAC SERVICE',
            'dissudes': 'DISSUDES'
        };
        return names[id] || id;
    }

    async forcarAtualizacaoDashboard() {
        try {
            const data = await this.makeRequest('/dashboard/atualizar', {
                method: 'POST'
            });
            
            this.showNotification('Dashboard atualizado com sucesso!', 'success');
            
            // Aguardar um pouco para garantir que o cache foi atualizado
            setTimeout(async () => {
                // Recarregar dashboard com dados atualizados
                await this.loadDashboard();
            }, 500);
            
        } catch (error) {
            console.error('Erro ao forçar atualização do dashboard:', error);
            this.showNotification('Erro ao atualizar dashboard.', 'error');
        }
    }

    zerarContadoresDashboard() {
        // Zerar contadores por transportadora
        document.getElementById('jt-count').textContent = '0';
        document.getElementById('jadlog-count').textContent = '0';
        document.getElementById('dialogo-count').textContent = '0';
        document.getElementById('correios-count').textContent = '0';
        document.getElementById('correios-pa-count').textContent = '0';
        document.getElementById('logan-count').textContent = '0';
        document.getElementById('favela-log-count').textContent = '0';
        document.getElementById('sac-service-count').textContent = '0';
        document.getElementById('dissudes-count').textContent = '0';
        
        // Zerar resumo do dia
        document.getElementById('total-hoje').textContent = '0';
        document.getElementById('coleta-hoje').textContent = '0';
        document.getElementById('insucesso-hoje').textContent = '0';
        
        // Zerar chart de status
        document.getElementById('coleta-hoje-chart').textContent = '0';
        document.getElementById('insucesso-hoje-chart').textContent = '0';
        
        // Zerar percentuais
        document.getElementById('coleta-percentage').textContent = '0%';
        document.getElementById('insucesso-percentage').textContent = '0%';
        
        // Zerar barras de progresso
        const transportadoraIds = ['jt', 'jadlog', 'dialogo', 'correios', 'correios-pa', 'logan', 'favela-log', 'sac-service', 'dissudes'];
        transportadoraIds.forEach(id => {
            const barElement = document.getElementById(`${id}-bar`);
            if (barElement) {
                barElement.style.width = '0%';
            }
        });
    }

    async loadFaltantes() {
        try {
            const data = await this.makeRequest('/mercadorias/faltantes');
            
            document.getElementById('faltantes-count').textContent = data.total;
            
            const container = document.getElementById('faltantes-list');
            
            if (data.faltantes.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-check-circle"></i>
                        <p>Todas as mercadorias foram conferidas!</p>
                    </div>
                `;
                // Ocultar botão de exclusão
                document.getElementById('excluir-faltantes-btn').style.display = 'none';
            } else {
                container.innerHTML = data.faltantes.map(item => `
                    <div class="item-with-checkbox" data-codigo="${item.codigo}">
                        <label class="checkbox-container">
                            <input type="checkbox" class="faltante-checkbox" data-codigo="${item.codigo}">
                            <span class="checkmark"></span>
                        </label>
                        <div class="item-content">
                            <span class="item-code">${item.codigo}</span>
                            <span class="item-status status-pendente">PENDENTE</span>
                        </div>
                    </div>
                `).join('');
                
                // Adicionar event listeners para checkboxes
                this.setupFaltantesCheckboxes();
            }
        } catch (error) {
            console.error('Erro ao carregar faltantes:', error);
        }
    }

    setupFaltantesCheckboxes() {
        const checkboxes = document.querySelectorAll('.faltante-checkbox');
        const excluirBtn = document.getElementById('excluir-faltantes-btn');
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const itemContainer = checkbox.closest('.item-with-checkbox');
                if (checkbox.checked) {
                    itemContainer.classList.add('selected');
                } else {
                    itemContainer.classList.remove('selected');
                }
                
                // Verificar se há checkboxes selecionados
                const checkedBoxes = document.querySelectorAll('.faltante-checkbox:checked');
                if (checkedBoxes.length > 0) {
                    excluirBtn.style.display = 'flex';
                    excluirBtn.textContent = `Excluir Selecionados (${checkedBoxes.length})`;
                } else {
                    excluirBtn.style.display = 'none';
                }
            });
        });
    }

    async excluirFaltantesSelecionados() {
        const checkedBoxes = document.querySelectorAll('.faltante-checkbox:checked');
        
        if (checkedBoxes.length === 0) {
            this.showNotification('Nenhum item selecionado para exclusão.', 'warning');
            return;
        }
        
        const codigos = Array.from(checkedBoxes).map(checkbox => checkbox.dataset.codigo);
        
        if (confirm(`Tem certeza que deseja excluir ${codigos.length} rastreio(s) da base?\n\nCódigos: ${codigos.join(', ')}`)) {
            try {
                // Excluir cada rastreio da base
                for (const codigo of codigos) {
                    await this.makeRequest('/rastreios/excluir', {
                        method: 'DELETE',
                        body: JSON.stringify({ codigo_rastreio: codigo })
                    });
                }
                
                this.showNotification(`${codigos.length} rastreio(s) excluído(s) com sucesso!`, 'success');
                
                // Recarregar listas
                await this.loadFaltantes();
                await this.loadConferidas();
                await this.loadBipadas();
                await this.loadDashboard();
                
            } catch (error) {
                console.error('Erro ao excluir rastreios:', error);
                this.showNotification('Erro ao excluir rastreios.', 'error');
            }
        }
    }

    async loadConferidas() {
        try {
            const data = await this.makeRequest('/mercadorias/conferidas');
            
            document.getElementById('conferidas-count').textContent = data.total;
            
            const container = document.getElementById('conferidas-list');
            
            if (data.conferidas.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-barcode"></i>
                        <p>Nenhuma mercadoria foi conferida ainda.</p>
                    </div>
                `;
            } else {
                // Ordenar por timestamp (mais recente primeiro)
                const conferidasOrdenadas = data.conferidas.sort((a, b) => {
                    return new Date(b.timestamp) - new Date(a.timestamp);
                });
                
                container.innerHTML = conferidasOrdenadas.map(item => {
                    const timestamp = new Date(item.timestamp).toLocaleString('pt-BR', {
                        timeZone: 'America/Sao_Paulo',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    const statusClass = item.status_base === 'na_base' ? 'status-na-base' : 'status-fora-base';
                    const statusText = item.status_base === 'na_base' ? 'NA BASE' : 'FORA DA BASE';
                    const transportadora = item.transportadora || 'Não definida';
                    
                    return `
                        <div class="item">
                            <div class="item-with-delete">
                                <div class="item-content-main">
                                    <div>
                                        <span class="item-code">${item.codigo}</span>
                                        <div class="item-time">${timestamp}</div>
                                        <div class="item-transportadora">${transportadora}</div>
                                    </div>
                                    <span class="item-status ${statusClass}">${statusText}</span>
                                </div>
                                <button class="btn-delete" onclick="sistema.excluirMercadoria('${item.codigo}')" title="Excluir mercadoria - Permite bipar novamente">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        } catch (error) {
            console.error('Erro ao carregar conferidas:', error);
        }
    }

    async loadBipadas() {
        try {
            const data = await this.makeRequest('/mercadorias/bipadas');
            
            document.getElementById('bipadas-count').textContent = data.total;
            document.getElementById('bipadas-coleta-count').textContent = data.total_coleta;
            document.getElementById('bipadas-insucesso-count').textContent = data.total_insucesso;
            document.getElementById('bipadas-sem-status-count').textContent = data.total_sem_status;
            
            // Carregar seção Coleta
            const containerColeta = document.getElementById('bipadas-coleta-list');
            if (data.bipadas_coleta.length === 0) {
                containerColeta.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-truck"></i>
                        <p>Nenhuma mercadoria com status Coleta.</p>
                    </div>
                `;
            } else {
                // Ordenar por timestamp (mais recente primeiro)
                const coletaOrdenadas = data.bipadas_coleta.sort((a, b) => {
                    return new Date(b.timestamp) - new Date(a.timestamp);
                });
                
                containerColeta.innerHTML = coletaOrdenadas.map(item => {
                    const timestamp = new Date(item.timestamp).toLocaleString('pt-BR', {
                        timeZone: 'America/Sao_Paulo',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    const transportadora = item.transportadora || 'Não definida';
                    return `
                        <div class="item">
                            <div class="item-content">
                                <div>
                                    <span class="item-code">${item.codigo}</span>
                                    <div class="item-time">${timestamp}</div>
                                    <div class="item-transportadora">${transportadora}</div>
                                </div>
                                <span class="item-status status-coleta">COLETA</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            // Carregar seção Insucesso
            const containerInsucesso = document.getElementById('bipadas-insucesso-list');
            if (data.bipadas_insucesso.length === 0) {
                containerInsucesso.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-times-circle"></i>
                        <p>Nenhuma mercadoria com status Insucesso.</p>
                    </div>
                `;
            } else {
                // Ordenar por timestamp (mais recente primeiro)
                const insucessoOrdenadas = data.bipadas_insucesso.sort((a, b) => {
                    return new Date(b.timestamp) - new Date(a.timestamp);
                });
                
                containerInsucesso.innerHTML = insucessoOrdenadas.map(item => {
                    const timestamp = new Date(item.timestamp).toLocaleString('pt-BR', {
                        timeZone: 'America/Sao_Paulo',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    const transportadora = item.transportadora || 'Não definida';
                    return `
                        <div class="item">
                            <div class="item-content">
                                <div>
                                    <span class="item-code">${item.codigo}</span>
                                    <div class="item-time">${timestamp}</div>
                                    <div class="item-transportadora">${transportadora}</div>
                                </div>
                                <span class="item-status status-insucesso">INSUCESSO</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            // Carregar seção Sem Status
            const containerSemStatus = document.getElementById('bipadas-sem-status-list');
            if (data.bipadas_sem_status.length === 0) {
                containerSemStatus.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-question-circle"></i>
                        <p>Nenhuma mercadoria sem status definido.</p>
                    </div>
                `;
            } else {
                // Ordenar por timestamp (mais recente primeiro)
                const semStatusOrdenadas = data.bipadas_sem_status.sort((a, b) => {
                    return new Date(b.timestamp) - new Date(a.timestamp);
                });
                
                containerSemStatus.innerHTML = semStatusOrdenadas.map(item => {
                    const timestamp = new Date(item.timestamp).toLocaleString('pt-BR', {
                        timeZone: 'America/Sao_Paulo',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    const transportadora = item.transportadora || 'Não definida';
                    return `
                        <div class="item">
                            <div class="item-content">
                                <div>
                                    <span class="item-code">${item.codigo}</span>
                                    <div class="item-time">${timestamp}</div>
                                    <div class="item-transportadora">${transportadora}</div>
                                </div>
                                <span class="item-status status-sem-status">SEM STATUS</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        } catch (error) {
            console.error('Erro ao carregar bipadas:', error);
        }
    }

    async importarRastreios() {
        const textarea = document.getElementById('rastreios-input');
        const limparBase = document.getElementById('limpar-base').checked;
        
        const texto = textarea.value.trim();
        if (!texto) {
            this.showNotification('Digite os códigos de rastreio para importar', 'warning');
            return;
        }
        
        const rastreios = texto.split('\n')
            .map(linha => linha.trim())
            .filter(linha => linha.length > 0);
        
        if (rastreios.length === 0) {
            this.showNotification('Nenhum código de rastreio válido encontrado', 'warning');
            return;
        }
        
        try {
            const data = await this.makeRequest('/rastreios/importar', {
                method: 'POST',
                body: JSON.stringify({
                    rastreios: rastreios,
                    limpar_base: limparBase
                })
            });
            
            this.showNotification(data.mensagem, 'success');
            textarea.value = '';
            document.getElementById('limpar-base').checked = false;
            
            // Recarregar dados
            await this.loadData();
            
        } catch (error) {
            console.error('Erro ao importar rastreios:', error);
        }
    }

    async biparMercadoria() {
        const input = document.getElementById('codigo-input');
        const codigo = input.value.trim().toUpperCase();
        
        if (!codigo) {
            this.showNotification('Digite um código de rastreio', 'warning');
            input.focus();
            return;
        }
        
        try {
            const data = await this.makeRequest('/mercadorias/bipar', {
                method: 'POST',
                body: JSON.stringify({
                    codigo_rastreio: codigo
                })
            });
            
            const resultDiv = document.getElementById('scan-result');
            resultDiv.style.display = 'block';
            
            let resultClass = '';
            let icon = '';
            
            switch (data.status) {
                case 'encontrado':
                    resultClass = 'success';
                    icon = '<i class="fas fa-check-circle"></i>';
                    this.showNotification('Mercadoria conferida com sucesso!', 'success');
                    
                    // Aplicar status automaticamente se houver um selecionado
                    if (this.statusAtual) {
                        await this.aplicarStatusAutomatico(codigo, this.statusAtual);
                    }
                    break;
                case 'nao_encontrado':
                    resultClass = 'error';
                    icon = '<i class="fas fa-exclamation-triangle"></i>';
                    this.showNotification('Mercadoria não encontrada na base!', 'error');
                    break;
                case 'ja_conferido':
                    resultClass = 'warning';
                    icon = '<i class="fas fa-info-circle"></i>';
                    this.showNotification('Mercadoria já foi conferida anteriormente', 'warning');
                    break;
            }
            
            resultDiv.className = `scan-result ${resultClass}`;
            resultDiv.innerHTML = `${icon} ${data.mensagem}`;
            
            // Limpar campo e focar
            input.value = '';
            input.focus();
            
            // Recarregar dados
            await this.loadData();
            
            // Esconder resultado após 5 segundos
            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 5000);
            
        } catch (error) {
            console.error('Erro ao bipar mercadoria:', error);
            input.focus();
        }
    }

    async resetarSistema() {
        if (!confirm('Tem certeza que deseja resetar o sistema? Isso irá limpar todos os rastreios esperados e TODAS as mercadorias bipadas/conferidas. O dashboard do dia será mantido.')) {
            return;
        }
        
        try {
            const data = await this.makeRequest('/rastreios/resetar', {
                method: 'POST'
            });
            
            this.showNotification(data.mensagem || 'Sistema resetado com sucesso!', 'success');
            
            // Limpar resultado da bipagem
            const scanResultEl = document.getElementById('scan-result');
            if (scanResultEl) {
                scanResultEl.style.display = 'none';
                scanResultEl.innerHTML = '';
            }
            
            // Recarregar dados (SEM recarregar dashboard - ele será mantido)
            await Promise.all([
                this.loadEstatisticas(),
                this.loadFaltantes(),
                this.loadConferidas(),
                this.loadBipadas()
            ]);
            
            // O dashboard não é recarregado para manter os contadores do dia
        } catch (error) {
            console.error('Erro ao resetar sistema:', error);
            this.showNotification('Erro ao resetar sistema.', 'error');
        }
    }

    async resetarDashboard() {
        if (!confirm('Tem certeza que deseja resetar o dashboard? Isso irá limpar os contadores de transportadoras e o resumo do dia.')) {
            return;
        }
        
        try {
            const data = await this.makeRequest('/dashboard/resetar', {
                method: 'POST'
            });
            
            this.showNotification(data.mensagem, 'success');
            
            // Recarregar dados
            await this.loadDashboard();
            
        } catch (error) {
            console.error('Erro ao resetar dashboard:', error);
        }
    }

    async copiarBipadasPorStatus(status) {
        try {
            const data = await this.makeRequest(`/mercadorias/bipadas/${status}`);
            
            if (data.bipadas.length === 0) {
                this.showNotification(`Nenhuma mercadoria com status ${status} para copiar`, 'warning');
                return;
            }
            
            const lista = data.bipadas.map(item => item.codigo).join('\n');
            const statusText = status === 'coleta' ? 'Coleta' : status === 'insucesso' ? 'Insucesso' : 'Sem Status';
            
            // Tentar usar a API moderna do clipboard primeiro
            if (navigator.clipboard && window.isSecureContext) {
                try {
                    await navigator.clipboard.writeText(lista);
                    this.showNotification(`${data.bipadas.length} códigos de ${statusText} copiados para a área de transferência`, 'success');
                    return;
                } catch (clipboardError) {
                    console.log('Clipboard API falhou, tentando método alternativo');
                }
            }
            
            // Método alternativo usando textarea temporária
            const textarea = document.createElement('textarea');
            textarea.value = lista;
            textarea.style.position = 'fixed';
            textarea.style.left = '-999999px';
            textarea.style.top = '-999999px';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    this.showNotification(`${data.bipadas.length} códigos de ${statusText} copiados para a área de transferência`, 'success');
                } else {
                    this.mostrarListaParaCopia(lista, statusText);
                }
            } catch (err) {
                this.mostrarListaParaCopia(lista, statusText);
            } finally {
                document.body.removeChild(textarea);
            }
            
        } catch (error) {
            console.error('Erro ao copiar bipadas por status:', error);
            this.showNotification('Erro ao carregar lista de bipadas', 'error');
        }
    }

    async copiarBipadas() {
        try {
            const data = await this.makeRequest('/mercadorias/bipadas');
            
            if (data.total === 0) {
                this.showNotification('Nenhuma mercadoria bipada para copiar', 'warning');
                return;
            }
            
            // Criar lista com todas as bipadas
            const todasBipadas = [
                ...data.bipadas_coleta,
                ...data.bipadas_insucesso,
                ...data.bipadas_sem_status
            ];
            
            const lista = todasBipadas.map(item => item.codigo).join('\n');
            
            // Tentar usar a API moderna do clipboard primeiro
            if (navigator.clipboard && window.isSecureContext) {
                try {
                    await navigator.clipboard.writeText(lista);
                    this.showNotification(`${todasBipadas.length} códigos copiados para a área de transferência`, 'success');
                    return;
                } catch (clipboardError) {
                    console.log('Clipboard API falhou, tentando método alternativo');
                }
            }
            
            // Método alternativo usando textarea temporária
            const textarea = document.createElement('textarea');
            textarea.value = lista;
            textarea.style.position = 'fixed';
            textarea.style.left = '-999999px';
            textarea.style.top = '-999999px';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    this.showNotification(`${todasBipadas.length} códigos copiados para a área de transferência`, 'success');
                } else {
                    this.mostrarListaParaCopia(lista);
                }
            } catch (err) {
                this.mostrarListaParaCopia(lista);
            } finally {
                document.body.removeChild(textarea);
            }
            
        } catch (error) {
            console.error('Erro ao copiar bipadas:', error);
            this.showNotification('Erro ao carregar lista de bipadas', 'error');
        }
    }

    mostrarListaParaCopia(lista, statusText = 'Bipados') {
        // Criar modal com a lista para cópia manual
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            padding: 20px;
            border-radius: 10px;
            max-width: 500px;
            width: 90%;
            max-height: 80%;
            overflow-y: auto;
        `;
        
        content.innerHTML = `
            <h3>Lista de Códigos ${statusText}</h3>
            <p>Selecione todo o texto abaixo e copie manualmente (Ctrl+C):</p>
            <textarea readonly style="width: 100%; height: 200px; font-family: monospace; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">${lista}</textarea>
            <div style="margin-top: 15px; text-align: right;">
                <button onclick="this.closest('.modal').remove()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Fechar</button>
            </div>
        `;
        
        modal.className = 'modal';
        modal.appendChild(content);
        document.body.appendChild(modal);
        
        // Selecionar automaticamente o texto
        const textarea = content.querySelector('textarea');
        textarea.focus();
        textarea.select();
        
        // Fechar modal ao clicar fora
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        this.showNotification(`Lista de ${statusText} exibida para cópia manual`, 'info');
    }

    selecionarStatus(status) {
        // Remover seleção anterior
        document.getElementById('status-coleta-btn').classList.remove('selected');
        document.getElementById('status-insucesso-btn').classList.remove('selected');
        
        // Selecionar novo status
        if (this.statusAtual === status) {
            // Se clicar no mesmo status, deselecionar
            this.statusAtual = null;
            this.showNotification('Status deselecionado', 'info');
        } else {
            // Selecionar novo status
            this.statusAtual = status;
            document.getElementById(`status-${status}-btn`).classList.add('selected');
            this.showNotification(`Status "${status}" selecionado - todos os rastreios bipados receberão este status`, 'success');
        }
    }

    async aplicarStatusAutomatico(codigo, status) {
        try {
            await this.makeRequest('/status/atualizar', {
                method: 'POST',
                body: JSON.stringify({
                    codigo_rastreio: codigo,
                    status: status
                })
            });
            
            console.log(`Status "${status}" aplicado automaticamente ao código ${codigo}`);
            
            // Atualizar dashboard após mudança de status
            setTimeout(async () => {
                await this.loadDashboard();
            }, 300);
            
        } catch (error) {
            console.error('Erro ao aplicar status automático:', error);
        }
    }

    async aplicarStatus(status) {
        // Esta função agora é usada apenas para aplicação automática de status
        // A seleção manual foi removida em favor da seleção fixa
        console.log(`Função aplicarStatus chamada com status: ${status}`);
    }

    // Funções para exportação Excel
    showExportModal() {
        document.getElementById('export-modal').classList.add('show');
    }

    hideExportModal() {
        document.getElementById('export-modal').classList.remove('show');
        document.getElementById('transportadora-select').value = '';
    }

    async exportarExcel() {
        const transportadora = document.getElementById('transportadora-select').value;
        
        if (!transportadora) {
            this.showNotification('Selecione uma transportadora', 'warning');
            return;
        }
        
        try {
            this.showLoading();
            
            // Primeiro, atualizar todas as mercadorias bipadas com a transportadora selecionada
            await this.atualizarTransportadoraEmLote(transportadora);
            
            // Fazer download do arquivo
            const response = await fetch(`${this.baseURL}/exportar/excel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ transportadora: transportadora })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro || 'Erro ao exportar dados');
            }
            
            // Criar blob e fazer download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `conferencia_nestle_${new Date().toISOString().split('T')[0]}_${transportadora.replace(' ', '_')}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showNotification('Arquivo Excel exportado com sucesso!', 'success');
            this.hideExportModal();
            
            // Forçar atualização do dashboard para mostrar as mudanças de transportadora
            await this.forcarAtualizacaoDashboard();
            
        } catch (error) {
            console.error('Erro ao exportar Excel:', error);
            this.showNotification(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async atualizarTransportadoraEmLote(transportadora) {
        try {
            // Usar a nova rota de atualização em lote
            const response = await this.makeRequest('/transportadora/atualizar-lote', {
                method: 'POST',
                body: JSON.stringify({ transportadora: transportadora })
            });
            
            if (response.atualizadas > 0) {
                this.showNotification(`${response.atualizadas} mercadorias atualizadas com transportadora ${transportadora}`, 'success');
            } else {
                this.showNotification('Todas as mercadorias já têm transportadora definida', 'info');
            }
            
            return response;
            
        } catch (error) {
            console.error('Erro ao atualizar transportadoras em lote:', error);
            throw new Error('Erro ao atualizar transportadoras');
        }
    }

    async atualizarTransportadora(codigo, transportadora) {
        try {
            await this.makeRequest('/transportadora/atualizar', {
                method: 'POST',
                body: JSON.stringify({
                    codigo_rastreio: codigo,
                    transportadora: transportadora
                })
            });
        } catch (error) {
            console.error(`Erro ao atualizar transportadora para ${codigo}:`, error);
        }
    }

    async excluirMercadoria(codigo) {
        try {
            // Confirmar exclusão
            if (!confirm(`Tem certeza que deseja excluir a mercadoria ${codigo}?`)) {
                return;
            }

            // Encontrar o elemento do item e adicionar animação de exclusão
            const itemElement = document.querySelector(`[onclick="sistema.excluirMercadoria('${codigo}')"]`).closest('.item');
            if (itemElement) {
                itemElement.classList.add('deleting');
            }

            await this.makeRequest('/mercadorias/excluir', {
                method: 'DELETE',
                body: JSON.stringify({
                    codigo_rastreio: codigo
                })
            });
            
            this.showNotification(`Mercadoria ${codigo} excluída com sucesso!`, 'success');
            
            // Aguardar um pouco para a animação terminar antes de recarregar
            setTimeout(async () => {
                // Recarregar todas as listas para atualizar os dados
                await Promise.all([
                    this.loadConferidas(),
                    this.loadBipadas(),
                    this.loadEstatisticas(),
                    this.loadDashboard()  // Recarregar dashboard para refletir a exclusão
                ]);
            }, 500);
            
        } catch (error) {
            console.error(`Erro ao excluir mercadoria ${codigo}:`, error);
            this.showNotification(`Erro ao excluir mercadoria: ${error.message}`, 'error');
            
            // Remover classe de animação em caso de erro
            const itemElement = document.querySelector(`[onclick="sistema.excluirMercadoria('${codigo}')"]`)?.closest('.item');
            if (itemElement) {
                itemElement.classList.remove('deleting');
            }
        }
    }

    switchTab(tabName) {
        // Remover classe active de todos os botões e painéis
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        
        // Adicionar classe active ao botão e painel selecionados
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        
        // Definir ícones para cada tipo de notificação
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        
        // Definir títulos para cada tipo
        const titles = {
            success: 'Sucesso!',
            error: 'Erro!',
            warning: 'Atenção!',
            info: 'Informação'
        };
        
        // Criar conteúdo da notificação com ícone e título
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 20px;">${icons[type] || icons.info}</div>
                <div>
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 4px;">${titles[type] || titles.info}</div>
                    <div>${message}</div>
                </div>
            </div>
        `;
        
        notification.className = `notification ${type} show`;
        
        // Tempo de exibição baseado no tipo
        const displayTime = type === 'error' ? 6000 : 5000;
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, displayTime);
    }

    showLoading() {
        document.getElementById('loading').classList.add('show');
    }

    hideLoading() {
        document.getElementById('loading').classList.remove('show');
    }
}

// Inicializar sistema quando a página carregar
let sistema;
document.addEventListener('DOMContentLoaded', () => {
    sistema = new SistemaConferencia();
});

// Adicionar suporte para leitura de código de barras via teclado
document.addEventListener('keydown', (e) => {
    // Se não estiver focado em um input e a tecla for alfanumérica
    if (document.activeElement.tagName !== 'INPUT' && 
        document.activeElement.tagName !== 'TEXTAREA' &&
        /^[a-zA-Z0-9]$/.test(e.key)) {
        
        // Focar no campo de código e adicionar a tecla pressionada
        const codigoInput = document.getElementById('codigo-input');
        codigoInput.focus();
        codigoInput.value += e.key.toUpperCase();
    }
});

