# 🔧 Correção: Banco de Dados Persistente no Render

## Problema
O Render no plano gratuito usa armazenamento **efêmero**. Quando o serviço hiberna ou reinicia, o banco SQLite é apagado.

## Solução Implementada
✅ Sistema atualizado para usar **PostgreSQL no Render** e **SQLite localmente**

---

## 📋 Passos para Deploy

### 1. Fazer Push do Código Atualizado
```bash
git add .
git commit -m "Fix: Adicionar suporte a PostgreSQL para persistência no Render"
git push origin main
```

### 2. No Painel do Render

#### A. Criar Banco PostgreSQL (se ainda não criou)
1. Acesse: https://dashboard.render.com
2. Clique em **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `finance-db`
   - **Database**: `finance_app`  
   - **User**: `finance_user`
   - **Region**: Mesmo da aplicação (Oregon)
   - **Plan**: **Free**
4. Clique em **"Create Database"**
5. **Aguarde 2-3 minutos** até o banco estar pronto

#### B. Conectar o Banco à Aplicação
1. Vá em **Dashboard** → Seu Web Service `finance-app`
2. Clique na aba **"Environment"**
3. O Render já deve ter criado automaticamente a variável:
   - `DATABASE_URL` = (URL interna do PostgreSQL)
4. **Se não existir**, adicione manualmente:
   - Vá no banco de dados criado
   - Copie a **"Internal Database URL"**
   - Cole em Environment Variables do Web Service

#### C. Configurar Variáveis de Admin (Importante!)
Ainda em **Environment**, adicione as variáveis do admin:

```
ADMIN_USERNAME = seu_usuario_admin
ADMIN_PASSWORD = sua_senha_segura_aqui
```

⚠️ **IMPORTANTE**: Escolha uma senha forte! Esta será a primeira conta criada.

### 3. Fazer Deploy Manual
1. Vá em **"Manual Deploy"** → **"Deploy latest commit"**
2. Aguarde o build completar (2-5 minutos)
3. Verifique os logs em **"Logs"**

### 4. Testar a Aplicação
1. Acesse sua URL do Render
2. Faça login com o usuário admin criado
3. Adicione dados de teste
4. **Aguarde o serviço hibernar** (após 15min de inatividade)
5. Acesse novamente - **os dados devem estar lá!** ✅

---

## 🔍 Verificação Rápida

### Logs Esperados (Sucesso):
```
[DB] Usando PostgreSQL
[DB] Conectado ao banco de dados
```

### Se der erro:
```
# Verifique se DATABASE_URL está configurada:
[DB] Usando SQLite  ← ERRO! Deveria usar PostgreSQL
```

**Solução**: Verifique se a variável `DATABASE_URL` está configurada corretamente

---

## 📊 Comparação: Antes vs Depois

| Aspecto | Antes (SQLite) | Depois (PostgreSQL) |
|---------|----------------|---------------------|
| **Dados após hibernar** | ❌ Perdidos | ✅ Mantidos |
| **Reinício do serviço** | ❌ Dados apagados | ✅ Dados preservados |
| **Deploy novo** | ❌ Banco resetado | ✅ Dados preservados |
| **Ambiente local** | ✅ SQLite | ✅ SQLite |
| **Ambiente Render** | ❌ SQLite efêmero | ✅ PostgreSQL persistente |

---

## 🚀 Desenvolvimento Local

Nada muda! Continue usando normalmente:

```bash
python myindex.py
```

O sistema detecta automaticamente:
- **Local**: Usa `finance.db` (SQLite)
- **Render**: Usa PostgreSQL (DATABASE_URL)

---

## 🔐 Segurança

✅ **Variáveis já configuradas no render.yaml:**
- `SECRET_KEY` (gerado automaticamente)
- `SESSION_TIMEOUT_MINUTES`
- `SESSION_COOKIE_SECURE`
- `RATE_LIMIT_ENABLED`

✅ **Adicione manualmente no painel:**
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

---

## ❓ FAQ

### Q: E se eu já tenho dados no SQLite local?
**R:** Os dados locais continuam no `finance.db`. No Render, será um banco novo PostgreSQL vazio.

### Q: Como migrar dados do SQLite para PostgreSQL?
**R:** Você pode:
1. Exportar dados do SQLite para CSV/JSON
2. Importar no PostgreSQL usando scripts Python
3. Ou começar do zero no Render (recomendado para testes)

### Q: O banco gratuito tem limite?
**R:** Sim, PostgreSQL Free no Render tem:
- 1 GB de armazenamento
- Conexões simultâneas limitadas
- Backup automático limitado

### Q: Posso trocar para MySQL?
**R:** Sim, mas o Render não oferece MySQL gratuito. Recomendamos PostgreSQL.

---

## 📝 Notas Adicionais

- ✅ O código agora é **multi-banco**: funciona com SQLite e PostgreSQL
- ✅ Todas as queries foram adaptadas para serem compatíveis
- ✅ O `render.yaml` já está configurado
- ✅ Ambas as instalações mantêm dados separados (local vs Render)

---

## 🆘 Suporte

Se encontrar problemas:
1. Verifique os **logs do Render** em Dashboard → Logs
2. Confirme que `DATABASE_URL` está configurada
3. Teste localmente primeiro (`python myindex.py`)
