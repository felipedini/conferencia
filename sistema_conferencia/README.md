# Sistema de Conferência Nestlé

Sistema web para conferência de mercadorias da Nestlé com interface moderna e funcionalidades completas.

## 🚀 Instalação Rápida

### Windows (Recomendado)
1. **Baixe o Python 3.9+**: https://www.python.org/downloads/
   - ✅ **IMPORTANTE**: Marque "Add Python to PATH" durante a instalação
2. **Execute o instalador**: Clique duas vezes em `instalar.bat`
3. **Inicie o sistema**: Clique duas vezes em `iniciar.bat`
4. **Acesse**: http://127.0.0.1:5000

### Instalação Manual
```bash
# 1. Instalar Python 3.9+
# 2. Abrir terminal na pasta do projeto
pip install -r requirements.txt
python src/main.py
```

## 📋 Requisitos do Sistema

- **Python**: 3.9 ou superior
- **Sistema Operacional**: Windows, macOS, Linux
- **Navegador**: Chrome, Firefox, Edge, Safari
- **Memória**: Mínimo 512MB RAM
- **Espaço**: 100MB livres

## 🔧 Dependências Instaladas

- **Flask 3.1.1**: Framework web
- **Flask-CORS 6.0.0**: Suporte a CORS
- **Flask-SQLAlchemy 3.1.1**: ORM para banco de dados
- **SQLAlchemy 2.0.41**: ORM principal
- **Outras**: Ver `requirements.txt`

## 🎯 Funcionalidades

### 📊 Dashboard em Tempo Real
- Estatísticas de conferência
- Contadores por transportadora
- Progresso do dia
- Cache automático

### 📦 Gestão de Rastreios
- **Importar Base**: Cole códigos de rastreio
- **Bipar Mercadorias**: Escaneie ou digite códigos
- **Status Automático**: Aplique Coleta/Insucesso
- **Visualização**: Faltantes, Conferidas, Bipadas

### 📈 Relatórios
- **Exportar Excel**: Dados completos com transportadora
- **Copiar Listas**: Códigos por status
- **Estatísticas**: Métricas em tempo real

### 🔄 Controles do Sistema
- **Resetar Sistema**: Limpar todos os dados
- **Resetar Dashboard**: Limpar cache do dia
- **Atualizar Dados**: Refresh automático

## 🌐 Acesso ao Sistema

### Local
- **URL**: http://127.0.0.1:5000
- **URL**: http://localhost:5000

### Rede (Outros Computadores)
- **URL**: http://[IP-DO-COMPUTADOR]:5000
- **Exemplo**: http://192.168.1.100:5000

## 📁 Estrutura do Projeto

```
sistema_conferencia/
├── instalador.bat          # Instalador automático
├── iniciar.bat            # Iniciar servidor
├── requirements.txt       # Dependências Python
├── README.md             # Este arquivo
├── src/
│   ├── main.py           # Aplicação principal
│   ├── models/           # Modelos do banco
│   │   └── rastreio.py   # Modelos de dados
│   ├── routes/           # Rotas da API
│   │   └── conferencia.py # Endpoints principais
│   ├── static/           # Interface web
│   │   ├── index.html    # Página principal
│   │   ├── script.js     # JavaScript
│   │   └── styles.css    # Estilos
│   └── database/         # Banco de dados
│       ├── app.db        # SQLite (criado automaticamente)
│       └── migrate.py    # Migrações
└── venv/                 # Ambiente virtual (criado automaticamente)
```

## 🗄️ Banco de Dados

- **Tipo**: SQLite (local, sem instalação)
- **Arquivo**: `src/database/app.db`
- **Criação**: Automática na primeira execução
- **Migração**: Automática

### Tabelas
- **rastreios_esperados**: Códigos de rastreio importados
- **mercadorias_conferidas**: Mercadorias bipadas
- **dashboard_cache**: Cache do dashboard

## 🔧 Solução de Problemas

### Erro: "Python não encontrado"
- ✅ Instale Python 3.9+ de https://www.python.org/downloads/
- ✅ Marque "Add Python to PATH" durante instalação

### Erro: "Ambiente virtual não encontrado"
- ✅ Execute `instalar.bat` primeiro

### Erro: "Falha na instalação das dependências"
- ✅ Verifique conexão com internet
- ✅ Execute `instalar.bat` novamente

### Erro: "Porta 5000 em uso"
- ✅ Feche outros aplicativos usando a porta 5000
- ✅ Reinicie o computador se necessário

### Sistema não abre no navegador
- ✅ Verifique se o servidor está rodando
- ✅ Tente http://127.0.0.1:5000
- ✅ Verifique firewall/antivírus

## 📞 Suporte

### Logs do Sistema
- Os logs aparecem no terminal onde o servidor foi iniciado
- Erros são exibidos automaticamente

### Backup de Dados
- **Arquivo**: `src/database/app.db`
- **Frequência**: Faça backup regularmente
- **Localização**: Pasta `src/database/`

## 🚀 Comandos Úteis

### Desenvolvimento
```bash
# Ativar ambiente virtual
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python src/main.py

# Verificar estrutura do banco
python check_db.py
```

### Produção
- Use servidor WSGI como Gunicorn ou uWSGI
- Configure proxy reverso (Nginx/Apache)
- Use banco PostgreSQL para múltiplos usuários

## 📝 Changelog

### v1.0.0
- ✅ Sistema completo de conferência
- ✅ Dashboard em tempo real
- ✅ Exportação Excel
- ✅ Interface moderna
- ✅ Instalador automático

## 📄 Licença

Sistema desenvolvido para uso interno da Nestlé.

---

**Desenvolvido com ❤️ para a Nestlé**

