"""
Migração: Adiciona suporte a cartões de crédito e forma de pagamento
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import connect_db

def migrate():
    conn = connect_db()
    cur = conn.cursor()
    
    print("[MIGRATE] Adicionando suporte a cartões de crédito...")
    
    # 1. Criar tabela de cartões
    print("[MIGRATE] Criando tabela de cartões...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cartoes (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            ativo INTEGER DEFAULT 1,
            limite REAL DEFAULT 0,
            dia_vencimento INTEGER DEFAULT 10,
            dia_fechamento INTEGER DEFAULT 5,
            UNIQUE(nome, user_id)
        )
    """)
    
    # 2. Adicionar campos nas despesas
    print("[MIGRATE] Adicionando campos forma_pagamento e cartao_id em despesas...")
    cur.execute("""
        ALTER TABLE despesas 
        ADD COLUMN IF NOT EXISTS forma_pagamento TEXT DEFAULT 'dinheiro'
    """)
    
    cur.execute("""
        ALTER TABLE despesas 
        ADD COLUMN IF NOT EXISTS cartao_id INTEGER
    """)
    
    cur.execute("""
        ALTER TABLE despesas 
        ADD COLUMN IF NOT EXISTS fatura_mes INTEGER
    """)
    
    cur.execute("""
        ALTER TABLE despesas 
        ADD COLUMN IF NOT EXISTS fatura_ano INTEGER
    """)
    
    cur.execute("""
        ALTER TABLE despesas 
        ADD COLUMN IF NOT EXISTS eh_fatura INTEGER DEFAULT 0
    """)
    
    # 3. Adicionar campo saldo_inicial nos users
    print("[MIGRATE] Adicionando campo saldo_inicial em users...")
    cur.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS saldo_inicial REAL DEFAULT 0
    """)
    
    conn.commit()
    
    print("[MIGRATE] ✅ Migração concluída com sucesso!")
    print("[MIGRATE] Novos recursos:")
    print("  - Tabela 'cartoes' para gerenciar cartões de crédito")
    print("  - Campo 'forma_pagamento' em despesas (dinheiro/debito/cartao)")
    print("  - Campo 'cartao_id' para vincular despesa ao cartão")
    print("  - Campos 'fatura_mes' e 'fatura_ano' para rastreamento de faturas")
    print("  - Campo 'eh_fatura' para identificar despesas geradas automaticamente")
    print("  - Campo 'saldo_inicial' em users para definir saldo base")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    migrate()
