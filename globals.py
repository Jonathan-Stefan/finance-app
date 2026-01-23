import pandas as pd
from db import init_db, table_to_df, df_to_table

# Inicializa DB e carrega tabelas
init_db()

# Transações
df_despesas = table_to_df('despesas')
df_receitas = table_to_df('receitas')

if df_despesas.empty and df_receitas.empty:
    data_structure = {'Valor':[],
        'Efetuado':[],
        'Fixo':[],
        'Data':[],
        'Categoria':[],
        'Descrição':[],}

    df_receitas = pd.DataFrame(data_structure)
    df_despesas = pd.DataFrame(data_structure)
    df_to_table(df_despesas, 'despesas')
    df_to_table(df_receitas, 'receitas')
else:
    if 'Data' in df_despesas.columns:
        df_despesas['Data'] = pd.to_datetime(df_despesas['Data']).dt.date
    if 'Data' in df_receitas.columns:
        df_receitas['Data'] = pd.to_datetime(df_receitas['Data']).dt.date

# Categorias
df_cat_receita = table_to_df('cat_receita')
df_cat_despesa = table_to_df('cat_despesa')

if df_cat_receita.empty and df_cat_despesa.empty:
    cat_receita = {'Categoria': ["Salário", "Investimentos", "Comissão"]}
    cat_despesa = {'Categoria': ["Alimentação", "Aluguel", "Gasolina", "Saúde", "Lazer"]}
    df_cat_receita = pd.DataFrame(cat_receita)
    df_cat_despesa = pd.DataFrame(cat_despesa)
    df_to_table(df_cat_receita, 'cat_receita')
    df_to_table(df_cat_despesa, 'cat_despesa')

# listas de categorias como lista simples
cat_receita = df_cat_receita['Categoria'].tolist()
cat_despesa = df_cat_despesa['Categoria'].tolist()