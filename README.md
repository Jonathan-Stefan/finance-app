# Finance App 💰

Aplicação web de gestão financeira construída com Dash (Python) e Bootstrap.

## 🚀 Como Executar

### 1. Instalação de Dependências

```bash
# Ativar o ambiente virtual (Windows)
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar a Aplicação

```bash
python myindex.py
```

A aplicação estará disponível em:
- **Local**: http://127.0.0.1:8050
- **Rede**: http://192.168.0.103:8050 (use seu IP local)

## 📱 Acesso via Celular

### Passo a Passo:

1. **Conecte o celular na mesma rede Wi-Fi** que o computador
2. **Descubra o IP do computador** (já configurado: `192.168.0.103`)
3. **Abra o navegador do celular** e acesse:
   ```
   http://192.168.0.103:8050
   ```

### Descobrir seu IP Local

No PowerShell:
```powershell
ipconfig | Select-String -Pattern "IPv4"
```

Use o IP que começa com `192.168.x.x` ou `10.x.x.x`

### Liberar Firewall (se necessário)

Se não conseguir acessar do celular, execute como Administrador:

```powershell
New-NetFirewallRule -DisplayName "Finance App" -Direction Inbound -Protocol TCP -LocalPort 8050 -Action Allow
```

### Breakpoints

- **Mobile**: < 576px (smartphones)
- **Tablet**: 576px - 768px
- **Desktop**: > 768px

## 🛠️ Tecnologias

- **Python 3.9+**
- **Dash 3.4.0** - Framework web
- **Plotly** - Gráficos interativos
- **Dash Bootstrap Components** - UI responsiva
- **Pandas** - Manipulação de dados
- **SQLite** - Banco de dados


## 📝 Estrutura do Projeto

```
finance-app/
├── app.py                 # Configuração do Dash
├── myindex.py            # Arquivo principal
├── db.py                 # Funções do banco de dados
├── globals.py            # Variáveis globais
├── requirements.txt      # Dependências
├── assets/
│   └── styles.css        # Estilos personalizados + responsividade
├── components/
│   ├── dashboards.py     # Dashboard principal
│   ├── extratos.py       # Página de extratos
│   ├── login.py          # Sistema de login
│   └── sidebar.py        # Menu lateral
└── venv/                 # Ambiente virtual (não versionado)
```

## 🔒 Segurança

⚠️ **Importante**: 
- Não exponha a aplicação diretamente na internet sem autenticação adequada
- Use HTTPS em produção
- Configure variáveis de ambiente para senhas
- Implemente rate limiting para APIs

## 📄 Licença

Desenvolvido por Jônathan
