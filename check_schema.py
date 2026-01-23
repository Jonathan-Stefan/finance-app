import sqlite3

conn = sqlite3.connect('finance.db')
cur = conn.cursor()

# Listar tabelas
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tabelas no banco:", [t[0] for t in tables])

# Ver schema da tabela receitas
schema = cur.execute("PRAGMA table_info(receitas)").fetchall()
print("\nSchema da tabela receitas:")
for col in schema:
    print(f"  cid={col[0]}, name={col[1]}, type={col[2]}, notnull={col[3]}, default={col[4]}, pk={col[5]}")

conn.close()
