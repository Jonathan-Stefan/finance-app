# Guia de Deploy no Render - Passo a Passo

## 📋 Pré-requisitos

1. Conta no Render (https://render.com)
2. Repositório Git (GitHub, GitLab ou Bitbucket)
3. Código commitado e enviado para o repositório

## 🚀 Passo 1: Preparar o Projeto

### 1.1 Criar arquivo .env local (não commitar!)
```bash
cp .env.example .env
# Edite .env com suas configurações locais
```

### 1.2 Gerar SECRET_KEY forte
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copie o resultado e guarde em local seguro.

### 1.3 Verificar arquivos necessários
- [x] requirements.txt
- [x] .gitignore
- [x] render.yaml (opcional, mas recomendado)
- [x] myindex.py (arquivo principal)
- [x] config.py
- [x] security.py

### 1.4 Commit e Push
```bash
git add .
git commit -m "Preparar para deploy no Render"
git push origin main
```

## 🔧 Passo 2: Criar Web Service no Render

### 2.1 Acessar Dashboard
1. Login em https://dashboard.render.com
2. Clicar em "New +" → "Web Service"

### 2.2 Conectar Repositório
1. Autorizar acesso ao GitHub/GitLab
2. Selecionar o repositório finance-app
3. Clicar em "Connect"

### 2.3 Configurar Serviço

**Name:** finance-app (ou nome de sua escolha)

**Region:** Oregon (US West) - mais próximo do Brasil é Ohio (US East)

**Branch:** main

**Root Directory:** (deixar vazio se o projeto está na raiz)

**Runtime:** Python 3

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn myindex:server
```

**Plan:** Free (para testes) ou Starter ($7/mês para produção)

## 🔐 Passo 3: Configurar Variáveis de Ambiente

Na seção "Environment Variables", adicionar:

### Obrigatórias:
```
SECRET_KEY = <sua-chave-gerada-no-passo-1.2>
ENVIRONMENT = production
ADMIN_USERNAME = <seu-usuario-admin>
ADMIN_PASSWORD = <senha-forte-aqui>
```

### Recomendadas:
```
SESSION_TIMEOUT_MINUTES = 30
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
RATE_LIMIT_ENABLED = True
RATE_LIMIT_LOGIN_ATTEMPTS = 5
RATE_LIMIT_WINDOW_MINUTES = 15
LOG_LEVEL = WARNING
```

## 💾 Passo 4: Criar Banco de Dados PostgreSQL (Opcional mas Recomendado)

### 4.1 Criar Database
1. No Dashboard Render, clicar "New +" → "PostgreSQL"
2. Name: finance-db
3. Database: finance_app
4. User: finance_user
5. Region: Same as web service
6. Plan: Free (para testes)

### 4.2 Conectar ao Web Service
1. Copiar "Internal Database URL"
2. Adicionar nas variáveis de ambiente do Web Service:
```
DATABASE_URL = <internal-database-url>
```

⚠️ **Importante:** O Render fornece URLs externas e internas. Use a **Internal** para melhor performance e segurança.

## 🎯 Passo 5: Deploy

1. Clicar em "Create Web Service"
2. Aguardar o build (primeira vez leva ~5 minutos)
3. Verificar logs para erros
4. Quando status ficar "Live", aplicação está no ar!

## 🔍 Passo 6: Verificação Pós-Deploy

### 6.1 Acessar a aplicação
```
https://finance-app-XXXX.onrender.com
```

### 6.2 Testar funcionalidades
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Adicionar receita/despesa
- [ ] Visualizar extratos
- [ ] Painel admin (se for admin)

### 6.3 Verificar Logs
1. No painel Render, aba "Logs"
2. Procurar por erros ou warnings
3. Verificar mensagens de segurança

### 6.4 Alterar senha admin
1. Fazer login com credenciais do .env
2. Ir em Admin → Usuários
3. Alterar senha do admin

## ⚙️ Passo 7: Configurações Adicionais (Opcional)

### 7.1 Domínio Customizado
1. Em "Settings" do Web Service
2. Seção "Custom Domain"
3. Adicionar seu domínio
4. Configurar DNS conforme instruções

### 7.2 Auto-Deploy
- Já habilitado por padrão
- Cada push no branch main dispara novo deploy

### 7.3 Health Checks
```
Path: /
```

### 7.4 Configurar Notificações
1. Settings → Notifications
2. Adicionar email ou Slack
3. Notifica sobre deploys e erros

## 🛡️ Passo 8: Segurança Adicional

### 8.1 Backup do Banco
1. PostgreSQL Render faz backup automático
2. Retenção: 7 dias (plano Free), 30 dias (plano pago)

### 8.2 Monitoramento
- Render Dashboard → Métricas
- CPU, Memória, Requisições

### 8.3 Logs
- Retenção: 7 dias
- Para mais, integrar com serviço externo (Papertrail, Datadog)

## ⚡ Comandos Úteis

### Ver logs em tempo real
Dashboard → Logs (atualiza automaticamente)

### Forçar redeploy
Dashboard → Manual Deploy → Deploy latest commit

### Suspender serviço (free tier)
Services ficam suspensos após inatividade
Primeiro acesso pode demorar ~30s para "acordar"

### Rollback
Dashboard → Events → Selecionar deploy anterior → Rollback

## 🐛 Troubleshooting

### Build falha
- Verificar requirements.txt
- Checar Python version
- Ver logs completos

### App não inicia
- Verificar startCommand está correto
- Checar se myindex.py existe
- Verificar variáveis de ambiente

### Erro 500
- Ver logs detalhados
- Verificar conexão com banco
- Checar SECRET_KEY definida

### Performance lenta
- Plano Free tem limitações
- Upgrade para Starter ($7/mês)
- Otimizar queries do banco

## 📞 Suporte

- Documentação: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

## ✅ Checklist Final

- [ ] SECRET_KEY forte e única
- [ ] ADMIN_PASSWORD alterada
- [ ] DATABASE_URL configurada (se usar PostgreSQL)
- [ ] ENVIRONMENT=production
- [ ] HTTPS funcionando (Render fornece automático)
- [ ] Login funciona
- [ ] Dados são salvos corretamente
- [ ] Logs não mostram erros críticos
- [ ] Senha admin foi alterada após primeiro acesso

## 🎉 Pronto!

Sua aplicação está no ar de forma segura no Render!

URL: https://seu-app.onrender.com
