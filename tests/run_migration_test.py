import os
from pathlib import Path
import sys
import pandas as pd

# garante que o diretório do projeto esteja no path para importar `db`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import db
DB_PATH = ROOT / 'finance.db'

# Remove DB se existir para forçar migração
if DB_PATH.exists():
    DB_PATH.unlink()

# Executa inicialização (cria DB e migra CSVs)
db.init_db()

mapping = {
    'df_receitas.csv': 'receitas',
    'df_despesas.csv': 'despesas',
    'df_cat_receita.csv': 'cat_receita',
    'df_cat_despesa.csv': 'cat_despesa',
}

ok = True
for csv_name, table in mapping.items():
    csv_path = ROOT / csv_name
    csv_count = 0
    if csv_path.exists():
        df_csv = pd.read_csv(csv_path, index_col=0)
        csv_count = df_csv.shape[0]

    table_count = db.table_to_df(table).shape[0]
    print(f"{csv_name}: csv_rows={csv_count} -> table_rows={table_count}")
    if csv_count != table_count:
        ok = False

if ok:
    print("MIGRATION OK")
else:
    raise SystemExit("MIGRATION FAILED")
