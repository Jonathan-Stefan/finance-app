from db import init_db

# Inicializa DB e carrega tabelas
print('[INIT] Inicializando banco de dados...')
try:
    init_db()
    print('[INIT] Banco de dados inicializado com sucesso!')
except Exception as e:
    print(f'[INIT] ERRO CRÍTICO ao inicializar DB: {e}')
    print('[INIT] A aplicação pode não funcionar corretamente.')

# listas vazias - serão preenchidas dinamicamente quando o usuário fizer login
cat_receita = []
cat_despesa = []
