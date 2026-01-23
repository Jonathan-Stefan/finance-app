import sqlite3

conn = sqlite3.connect('finance.db')
cur = conn.cursor()

print("Adicionando coluna 'id' às tabelas...")

# Adicionar coluna id para receitas
try:
    cur.execute("ALTER TABLE receitas ADD COLUMN id INTEGER")
    print("✓ Coluna 'id' adicionada em 'receitas'")
except Exception as e:
    print(f"✗ Erro ao adicionar 'id' em 'receitas': {e}")

# Adicionar coluna id para despesas
try:
    cur.execute("ALTER TABLE despesas ADD COLUMN id INTEGER")
    print("✓ Coluna 'id' adicionada em 'despesas'")
except Exception as e:
    print(f"✗ Erro ao adicionar 'id' em 'despesas': {e}")

conn.commit()

# Atualizar IDs sequenciais
print("\nAtualizando IDs...")
cur.execute("UPDATE receitas SET id = rowid WHERE id IS NULL")
cur.execute("UPDATE despesas SET id = rowid WHERE id IS NULL")
conn.commit()

print("✓ IDs atualizados com rowid")

conn.close()
print("\nConcluído!")
