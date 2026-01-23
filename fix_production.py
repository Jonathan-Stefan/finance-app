"""
Script para corrigir problemas no banco de dados de produção.
Execute este script uma vez para limpar categorias órfãs.
"""

from db import cleanup_orphan_categories, connect_db

def fix_database():
    """Corrige problemas conhecidos no banco de dados."""
    print("🔧 Iniciando correção do banco de dados...")
    
    # 1. Limpar categorias órfãs (sem user_id)
    print("\n📋 Limpando categorias órfãs (sem user_id)...")
    result = cleanup_orphan_categories()
    print(f"   ✓ Categorias de receita removidas: {result.get('deleted_cat_receita', 0)}")
    print(f"   ✓ Categorias de despesa removidas: {result.get('deleted_cat_despesa', 0)}")
    
    # 2. Verificar categorias por usuário
    print("\n👥 Verificando categorias por usuário...")
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT u.id, u.username, 
               (SELECT COUNT(*) FROM cat_receita WHERE user_id = u.id) as receitas,
               (SELECT COUNT(*) FROM cat_despesa WHERE user_id = u.id) as despesas
        FROM users u
        ORDER BY u.id
    """)
    
    users_info = cur.fetchall()
    for user_id, username, cat_rec, cat_desp in users_info:
        admin_label = " (ADMIN)" if username == "admin" else ""
        print(f"   • {username}{admin_label}: {cat_rec} categorias receita, {cat_desp} categorias despesa")
    
    # 3. Verificar se há categorias sem user_id ainda
    cur.execute("SELECT COUNT(*) FROM cat_receita WHERE user_id IS NULL")
    orphan_receitas = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM cat_despesa WHERE user_id IS NULL")
    orphan_despesas = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n📊 Categorias órfãs restantes:")
    print(f"   • Receitas sem user_id: {orphan_receitas}")
    print(f"   • Despesas sem user_id: {orphan_despesas}")
    
    if orphan_receitas == 0 and orphan_despesas == 0:
        print("\n✅ Banco de dados corrigido com sucesso!")
    else:
        print("\n⚠️  Ainda há categorias órfãs. Execute o script novamente.")
    
    print("\n🎉 Correção concluída!")

if __name__ == "__main__":
    fix_database()
