import pandas as pd
from db import init_db, table_to_df, df_to_table

# Inicializa DB e carrega tabelas
init_db()

# Nota: As categorias agora são gerenciadas por usuário via callbacks
# Não carregamos categorias globais aqui para evitar conflitos

# listas vazias - serão preenchidas dinamicamente quando o usuário fizer login
cat_receita = []
cat_despesa = []