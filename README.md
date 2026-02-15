# Finance App

Aplicação web de controle financeiro pessoal construída com **Dash/Plotly**, com autenticação de usuários, gestão de receitas e despesas, orçamentos, planos/metas e acompanhamento de investimentos.

## Funcionalidades

- Login e cadastro de usuários.
- Dashboard com visão consolidada de saldo, receitas e despesas.
- Extratos com edição em tabela e filtros por período.
- Orçamentos mensais por categoria com acompanhamento de consumo.
- Planos e metas financeiras.
- Investimentos:
  - cadastro de investimento com instituição, tipo, rendimento e nome personalizado;
  - registro de aportes (com ou sem vínculo);
  - atualização de valor com cálculo de rendimento e IOF;
  - busca de cotação por ticker via endpoint interno.
- Área administrativa para gestão de usuários (acesso restrito a admin).

## Stack

- Python 3.11+
- Dash
- Dash Bootstrap Components
- Plotly
- Pandas / NumPy
- PostgreSQL (via `psycopg2` + `SQLAlchemy`)

## Estrutura do projeto

```text
finance-app/
├─ app.py
├─ myindex.py
├─ db.py
├─ config.py
├─ security.py
├─ constants.py
├─ globals.py
├─ requirements.txt
├─ render.yaml
├─ assets/
├─ components/
├─ db/
├─ scripts/
└─ tests/
```

## Pré-requisitos

- Python 3.11+ instalado
- Banco PostgreSQL disponível localmente **ou** via serviço externo

> Observação: o projeto está configurado para usar `DATABASE_URL` com PostgreSQL.

## Instalação local

1. Clone o repositório.
2. Crie e ative um ambiente virtual.
3. Instale as dependências.
4. Configure variáveis de ambiente.
5. Execute a aplicação.

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto (ou exporte no ambiente) com valores como:

```env
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=troque-esta-chave
DATABASE_URL=postgresql://usuario:senha@localhost:5432/finance_app
SESSION_TIMEOUT_MINUTES=30
RATE_LIMIT_ENABLED=True
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_WINDOW_MINUTES=15
```

Para produção, configure também:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=uma-senha-forte
```

## Executando a aplicação

```bash
python myindex.py
```

A aplicação ficará disponível em:

- http://localhost:8050

## Deploy no Render

O projeto já possui blueprint em `render.yaml` com:

- serviço web Python;
- build command: `pip install -r requirements.txt`;
- start command: `gunicorn myindex:server`;
- banco PostgreSQL gerenciado.

### Passos resumidos

1. Conecte o repositório no Render.
2. Crie o serviço via Blueprint.
3. Configure as variáveis obrigatórias no painel (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, etc.).
4. Faça o deploy.

## Scripts úteis

Na pasta `scripts/` existem utilitários para:

- inspeção de schema;
- validações de segurança;
- checagens de callbacks/ids;
- migrações pontuais.

## Testes

Há scripts de teste na pasta `tests/` (execução manual), por exemplo:

```bash
python tests/test_postgresql.py
python tests/test_add_category.py
```

## Segurança

A aplicação aplica cabeçalhos de segurança e validações de prontidão para produção. Revise:

- `security.py`
- `config.py`

