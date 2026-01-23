import sqlite3
from pathlib import Path
DB=Path(__file__).resolve().parent.parent / 'finance.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
for table in ['despesas','receitas','cat_receita','cat_despesa','users']:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        cols=cur.fetchall()
        print(table, [c[1] for c in cols])
    except Exception as e:
        print('error', table, e)
conn.close()