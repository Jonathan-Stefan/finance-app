"""
Script de migração: Renomeia coluna Efetuado para Status na tabela despesas
e converte os valores apropriadamente.

Executa as seguintes operações:
1. Cria coluna Status se não existir
2. Migra dados de Efetuado para Status (1 -> "Pago", 0 -> "A vencer")
3. Remove a coluna Efetuado da tabela despesas
4. Atualiza despesas vencidas (Data < hoje e Status = "A vencer" -> "Vencido")
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório pai ao path para importar db
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import connect_db, DB_PATH


def migrate_database():
    """Executa a migração completa."""
    print(f"[MIGRATE] Conectando ao banco de dados: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"[ERRO] Banco de dados não encontrado em: {DB_PATH}")
        return False
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Passo 1: Verificar estrutura atual
    print("\n[STEP 1] Verificando estrutura da tabela despesas...")
    cur.execute("PRAGMA table_info(despesas)")
    columns = {row[1]: row[2] for row in cur.fetchall()}
    print(f"Colunas encontradas: {list(columns.keys())}")
    
    # Passo 2: Criar coluna Status se não existir
    if 'Status' not in columns:
        print("\n[STEP 2] Criando coluna Status...")
        cur.execute("ALTER TABLE despesas ADD COLUMN Status TEXT")
        conn.commit()
        print("✓ Coluna Status criada")
    else:
        print("\n[STEP 2] Coluna Status já existe")
    
    # Passo 3: Migrar dados de Efetuado para Status
    if 'Efetuado' in columns:
        print("\n[STEP 3] Migrando dados de Efetuado para Status...")
        
        # Conta registros antes da migração
        cur.execute("SELECT COUNT(*) FROM despesas WHERE Efetuado = 1")
        count_efetuado_1 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM despesas WHERE Efetuado = 0")
        count_efetuado_0 = cur.fetchone()[0]
        
        print(f"  - Registros com Efetuado=1: {count_efetuado_1}")
        print(f"  - Registros com Efetuado=0: {count_efetuado_0}")
        
        # Migra apenas onde Status está NULL ou vazio
        cur.execute("UPDATE despesas SET Status = 'Pago' WHERE (Status IS NULL OR Status = '') AND Efetuado = 1")
        migrados_pago = cur.rowcount
        
        cur.execute("UPDATE despesas SET Status = 'A vencer' WHERE (Status IS NULL OR Status = '') AND Efetuado = 0")
        migrados_vencer = cur.rowcount
        
        conn.commit()
        
        print(f"  ✓ {migrados_pago} registros migrados para 'Pago'")
        print(f"  ✓ {migrados_vencer} registros migrados para 'A vencer'")
        
        # Passo 4: Atualizar despesas vencidas
        print("\n[STEP 4] Atualizando despesas vencidas...")
        hoje = datetime.now().strftime('%Y-%m-%d')
        cur.execute("UPDATE despesas SET Status = 'Vencido' WHERE Status = 'A vencer' AND Data < ?", (hoje,))
        vencidos = cur.rowcount
        conn.commit()
        print(f"  ✓ {vencidos} despesas marcadas como 'Vencido'")
        
        # Passo 5: Remover coluna Efetuado
        print("\n[STEP 5] Removendo coluna Efetuado...")
        print("  (SQLite não suporta DROP COLUMN diretamente, criando tabela nova...)")
        
        # Primeiro, desabilita foreign keys temporariamente
        cur.execute("PRAGMA foreign_keys=OFF")
        
        # Remove triggers que fazem referência à tabela despesas
        print("  - Removendo triggers temporariamente...")
        cur.execute("DROP TRIGGER IF EXISTS trg_set_username_on_despesas_insert")
        cur.execute("DROP TRIGGER IF EXISTS trg_update_username_on_despesas_userid")
        cur.execute("DROP TRIGGER IF EXISTS trg_update_username_on_users_update")
        cur.execute("DROP TRIGGER IF EXISTS trg_delete_user_set_username_null")
        
        # Cria nova tabela sem a coluna Efetuado
        cur.execute("""
        CREATE TABLE IF NOT EXISTS despesas_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Valor REAL,
            Status TEXT,
            Fixo INTEGER,
            Data TEXT,
            Categoria TEXT,
            Descrição TEXT,
            user_id INTEGER,
            username TEXT
        )
        """)
        
        # Copia dados para nova tabela
        cur.execute("""
        INSERT INTO despesas_new (id, Valor, Status, Fixo, Data, Categoria, Descrição, user_id, username)
        SELECT id, Valor, Status, Fixo, Data, Categoria, Descrição, user_id, username
        FROM despesas
        """)
        
        # Remove tabela antiga e renomeia nova
        cur.execute("DROP TABLE despesas")
        cur.execute("ALTER TABLE despesas_new RENAME TO despesas")
        conn.commit()
        
        # Recria os triggers
        print("  - Recriando triggers...")
        cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_set_username_on_despesas_insert
        AFTER INSERT ON despesas
        BEGIN
            UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
        END;
        """)
        
        cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_update_username_on_despesas_userid
        AFTER UPDATE OF user_id ON despesas
        BEGIN
            UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
        END;
        """)
        
        cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_update_username_on_users_update
        AFTER UPDATE OF username ON users
        BEGIN
            UPDATE receitas SET username = NEW.username WHERE user_id = NEW.id;
            UPDATE despesas SET username = NEW.username WHERE user_id = NEW.id;
        END;
        """)
        
        cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_delete_user_set_username_null
        AFTER DELETE ON users
        BEGIN
            UPDATE receitas SET username = NULL WHERE user_id = OLD.id;
            UPDATE despesas SET username = NULL WHERE user_id = OLD.id;
        END;
        """)
        
        # Reabilita foreign keys
        cur.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        
        print("  ✓ Coluna Efetuado removida com sucesso")
    else:
        print("\n[STEP 3-5] Coluna Efetuado não encontrada, migração já foi executada")
    
    # Passo 6: Verificar resultado final
    print("\n[STEP 6] Verificando resultado final...")
    cur.execute("PRAGMA table_info(despesas)")
    final_columns = {row[1]: row[2] for row in cur.fetchall()}
    print(f"Colunas finais: {list(final_columns.keys())}")
    
    cur.execute("SELECT Status, COUNT(*) FROM despesas GROUP BY Status")
    status_counts = cur.fetchall()
    print("\nDistribuição de Status:")
    for status, count in status_counts:
        print(f"  - {status or '(NULL)'}: {count}")
    
    conn.close()
    
    print("\n[SUCESSO] Migração concluída com sucesso!")
    return True


if __name__ == "__main__":
    print("="*60)
    print("MIGRAÇÃO: Efetuado -> Status na tabela despesas")
    print("="*60)
    
    try:
        success = migrate_database()
        if success:
            print("\n✓ Migração finalizada com sucesso!")
            sys.exit(0)
        else:
            print("\n✗ Migração falhou!")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
