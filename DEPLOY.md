# 🚀 Guia de Deploy - Finance App

## Opção 1: Render (RECOMENDADO - 100% Gratuito)

### ✨ Vantagens:
- ✅ Totalmente gratuito
- ✅ HTTPS automático
- ✅ Deploy automático via GitHub
- ✅ Domínio grátis (.onrender.com)
- ✅ Zero configuração de servidor

### 📝 Passo a Passo:

#### 1. Preparar o Repositório GitHub

```bash
# Adicionar e commitar os arquivos de deploy
git add .
git commit -m "Adicionar configuração de deploy"
git push origin main
```

#### 2. Criar Conta no Render

1. Acesse: https://render.com
2. Clique em **"Get Started for Free"**
3. Faça login com GitHub

#### 3. Criar Web Service

1. No dashboard, clique em **"New +"** → **"Web Service"**
2. Conecte seu repositório: `Jonathan-Stefan/finance-app`
3. Configure:
   - **Name**: `finance-app` (ou qualquer nome)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn myindex:server`
   - **Plan**: `Free`

4. Clique em **"Create Web Service"**

#### 4. Aguardar Deploy

- O Render irá fazer build automaticamente
- Leva ~2-5 minutos
- Você verá os logs em tempo real
- Quando aparecer "Your service is live 🎉", está pronto!

#### 5. Acessar sua Aplicação

Sua URL será algo como:
```
https://finance-app-xxxx.onrender.com
```

---

## Opção 2: Railway (Gratuito com Limites)

### 📝 Passo a Passo:

1. Acesse: https://railway.app
2. Login com GitHub
3. **"New Project"** → **"Deploy from GitHub repo"**
4. Selecione `finance-app`
5. Railway detecta automaticamente Python
6. Deploy automático!

**Limites gratuitos**: 500 horas/mês, $5 de crédito

---

## Opção 3: PythonAnywhere (Gratuito com Limitações)

### 📝 Passo a Passo:

1. Criar conta: https://www.pythonanywhere.com
2. **"Web"** → **"Add a new web app"**
3. Escolha **"Manual configuration"** → **"Python 3.9"**
4. Configure WSGI:

```python
# /var/www/seu_usuario_pythonanywhere_com_wsgi.py
import sys
path = '/home/seu_usuario/finance-app'
if path not in sys.path:
    sys.path.insert(0, path)

from myindex import server as application
```

5. Upload dos arquivos via **"Files"**
6. Console Bash:
```bash
pip install -r requirements.txt
```

**Limitações**: Sem sempre-online, precisa "wake up" diário

---

## Opção 4: Fly.io (Gratuito Generoso)

### 📝 Passo a Passo:

1. Instalar CLI:
```bash
# Windows PowerShell
iwr https://fly.io/install.ps1 -useb | iex
```

2. Login e deploy:
```bash
fly auth login
fly launch
fly deploy
```

**Limites**: 3 VMs gratuitas, sempre online

---

## ⚙️ Configurações Importantes

### Variáveis de Ambiente (Produção)

Se precisar adicionar secrets:

**No Render**:
1. Dashboard → Service → **"Environment"**
2. Adicione variáveis:
   - `SECRET_KEY`: sua-chave-secreta
   - `DATABASE_URL`: se usar DB externo

### Banco de Dados

O SQLite funciona, mas para produção considere:
- **Render**: PostgreSQL gratuito
- **Railway**: PostgreSQL incluído
- **Supabase**: PostgreSQL gratuito separado

---

## 🔒 Checklist de Segurança

Antes de ir para produção:

- [ ] Remover `debug=True` em produção
- [ ] Adicionar autenticação robusta
- [ ] Usar variáveis de ambiente para secrets
- [ ] Configurar CORS se necessário
- [ ] Adicionar rate limiting
- [ ] Fazer backup do banco de dados

---

## 📊 Monitoramento

### Render
- Logs em tempo real no dashboard
- Métricas de CPU/RAM
- Alertas de erro

### Verificar se está online:
```bash
curl https://seu-app.onrender.com
```

---

## 🐛 Troubleshooting

### App não inicia no Render?

1. Verifique os logs
2. Confirme que `gunicorn` está em `requirements.txt`
3. Teste localmente:
   ```bash
   gunicorn myindex:server
   ```

### Erro 503/502?

- Render apps gratuitos "dormem" após 15min de inatividade
- Primeiro acesso demora ~30s para acordar
- Use um serviço de ping (ex: UptimeRobot) para manter ativo

### Banco de dados não persiste?

- Render pode resetar sistema de arquivos
- Use PostgreSQL ou Volume persistente

---

## 🎯 Recomendação Final

Para este projeto, **Render** é a melhor opção porque:
- ✅ 100% gratuito para sempre
- ✅ Setup mais simples (1 clique)
- ✅ HTTPS grátis
- ✅ Deploy automático do GitHub
- ✅ Logs e métricas inclusos

**Tempo total de deploy: ~5 minutos** ⚡

---

## 📞 Suporte

Se tiver problemas:
1. Confira os logs do Render
2. Teste localmente primeiro: `gunicorn myindex:server`
3. Verifique se todos os arquivos foram commitados no Git

**Boa sorte com o deploy! 🚀**
