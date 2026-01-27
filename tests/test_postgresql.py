"""
Script de teste para validar todas as funções e tabelas do PostgreSQL
Execute com: python test_postgresql.py
"""
import os
import sys

# Configuração do DATABASE_URL
# Altere para suas credenciais locais do PostgreSQL
#DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/finance_app')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:24862486Js@localhost/finance_app')

print("\n" + "="*60)
print(f"🔧 Conectando ao PostgreSQL")
print(f"   URL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}")
print("="*60)

# Se precisar alterar, edite a linha acima ou exporte:
# export DATABASE_URL=postgresql://usuario:senha@localhost/finance_app

os.environ['DATABASE_URL'] = DATABASE_URL

from db import *
import traceback

def print_test(name, passed):
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"{status} - {name}")

def run_tests():
    print("\n" + "="*60)
    print("🔧 TESTE DE CONEXÃO E ESTRUTURA DO BANCO DE DADOS")
    print("="*60 + "\n")
    
    # 1. Teste de conexão
    try:
        conn = connect_db()
        conn.close()
        print_test("Conexão com PostgreSQL", True)
    except Exception as e:
        print_test("Conexão com PostgreSQL", False)
        print(f"   Erro: {e}\n")
        print("❌ NÃO FOI POSSÍVEL CONECTAR AO POSTGRESQL!\n")
        print("📋 INSTRUÇÕES:")
        print("   1. Instale o PostgreSQL: https://www.postgresql.org/download/")
        print("   2. Crie o banco de dados:")
        print("      psql -U postgres -c 'CREATE DATABASE finance_app;'")
        print("   3. Configure a DATABASE_URL no arquivo test_postgresql.py (linha 9)")
        print("      Exemplo: postgresql://postgres:senha@localhost/finance_app")
        print("\n   📖 Veja INSTALL_POSTGRESQL.md para mais detalhes\n")
        return
    
    # 2. Teste de inicialização do banco
    try:
        init_db()
        print_test("Inicialização do banco (init_db)", True)
    except Exception as e:
        print_test("Inicialização do banco (init_db)", False)
        print(f"   Erro: {e}\n{traceback.format_exc()}")
        return
    
    # 3. Verificar tabelas criadas
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        tabelas = ['users', 'receitas', 'despesas', 'cat_receita', 'cat_despesa', 'planos', 'montantes', 'anotacoes_planos']
        
        for tabela in tabelas:
            cur.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cur.fetchone()[0]
            print_test(f"Tabela '{tabela}' existe (count={count})", True)
        
        conn.close()
    except Exception as e:
        print_test("Verificação de tabelas", False)
        print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    print("\n" + "="*60)
    print("👤 TESTE DE FUNÇÕES DE USUÁRIOS")
    print("="*60 + "\n")
    
    # 4. Teste de criação de usuário
    test_user_id = None
    try:
        test_user_id = create_user('test_user', 'test_password', is_admin=0)
        print_test(f"Criar usuário (ID={test_user_id})", test_user_id is not None)
    except Exception as e:
        print_test("Criar usuário", False)
        print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    # 5. Teste de busca de usuário
    try:
        user = get_user_by_username('test_user')
        print_test(f"Buscar usuário por username", user is not None and user['username'] == 'test_user')
    except Exception as e:
        print_test("Buscar usuário por username", False)
        print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    # 6. Teste de verificação de senha
    try:
        verified_user = verify_user('test_user', 'test_password')
        print_test("Verificar senha correta", verified_user is not None)
        
        wrong_user = verify_user('test_user', 'wrong_password')
        print_test("Rejeitar senha incorreta", wrong_user is None)
    except Exception as e:
        print_test("Verificar senha", False)
        print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    # 7. Teste de contagem de usuários
    try:
        count = get_user_count()
        print_test(f"Contar usuários (count={count})", count >= 2)  # admin + test_user
    except Exception as e:
        print_test("Contar usuários", False)
        print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    print("\n" + "="*60)
    print("💰 TESTE DE FUNÇÕES DE CATEGORIAS")
    print("="*60 + "\n")
    
    if test_user_id:
        # 8. Teste de inserção de categoria
        try:
            insert_cat('cat_receita', 'Salário', test_user_id)
            insert_cat('cat_despesa', 'Alimentação', test_user_id)
            print_test("Inserir categorias", True)
        except Exception as e:
            print_test("Inserir categorias", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
        
        # 9. Teste de leitura de categorias
        try:
            df_cat_rec = table_to_df('cat_receita', user_id=test_user_id)
            df_cat_desp = table_to_df('cat_despesa', user_id=test_user_id)
            print_test(f"Ler categorias (receita={len(df_cat_rec)}, despesa={len(df_cat_desp)})", 
                       len(df_cat_rec) > 0 and len(df_cat_desp) > 0)
        except Exception as e:
            print_test("Ler categorias", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    print("\n" + "="*60)
    print("📊 TESTE DE FUNÇÕES DE TRANSAÇÕES")
    print("="*60 + "\n")
    
    if test_user_id:
        # 10. Teste de inserção de receita
        try:
            insert_transacao('receitas', 1000.00, 1, 0, '2026-01-27', 'Salário', 'Teste receita', test_user_id)
            print_test("Inserir receita", True)
        except Exception as e:
            print_test("Inserir receita", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
        
        # 11. Teste de inserção de despesa
        try:
            insert_transacao('despesas', 50.00, 'Pago', 0, '2026-01-27', 'Alimentação', 'Teste despesa', test_user_id)
            print_test("Inserir despesa", True)
        except Exception as e:
            print_test("Inserir despesa", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
        
        # 12. Teste de leitura de transações
        try:
            df_receitas = table_to_df('receitas', user_id=test_user_id)
            df_despesas = table_to_df('despesas', user_id=test_user_id)
            print_test(f"Ler transações (receitas={len(df_receitas)}, despesas={len(df_despesas)})", 
                       len(df_receitas) > 0 and len(df_despesas) > 0)
        except Exception as e:
            print_test("Ler transações", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
        
        # 13. Teste de atualização de status vencidos
        try:
            update_status_vencidos(test_user_id)
            print_test("Atualizar status vencidos", True)
        except Exception as e:
            print_test("Atualizar status vencidos", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    print("\n" + "="*60)
    print("🎯 TESTE DE FUNÇÕES DE PLANOS")
    print("="*60 + "\n")
    
    if test_user_id:
        # 14. Teste de inserção de plano
        plano_id = None
        try:
            plano_id = insert_plano('Viagem', 5000.00, 0, 'Lazer', test_user_id)
            print_test(f"Inserir plano (ID={plano_id})", plano_id is not None)
        except Exception as e:
            print_test("Inserir plano", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
        
        # 15. Teste de leitura de planos
        try:
            planos = get_planos_by_user(test_user_id)
            print_test(f"Ler planos (count={len(planos)})", len(planos) > 0)
        except Exception as e:
            print_test("Ler planos", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
        
        # 16. Teste de atualização de plano
        if plano_id:
            try:
                update_plano(plano_id, 'Viagem Atualizada', 6000.00, 100.00, 'Lazer')
                print_test("Atualizar plano", True)
            except Exception as e:
                print_test("Atualizar plano", False)
                print(f"   Erro: {e}\n{traceback.format_exc()}")
        
        # 17. Teste de cálculo de valor acumulado
        try:
            valor = calculate_plano_valor_acumulado(plano_id, test_user_id) if plano_id else 0
            print_test(f"Calcular valor acumulado (valor={valor})", True)
        except Exception as e:
            print_test("Calcular valor acumulado", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    print("\n" + "="*60)
    print("🧹 LIMPEZA E FINALIZAÇÃO")
    print("="*60 + "\n")
    
    # 18. Teste de deleção de usuário (limpa dados de teste)
    if test_user_id:
        try:
            delete_user(test_user_id)
            print_test("Deletar usuário de teste", True)
        except Exception as e:
            print_test("Deletar usuário de teste", False)
            print(f"   Erro: {e}\n{traceback.format_exc()}")
    
    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS!")
    print("="*60 + "\n")
    print("⚠️  IMPORTANTE: Configure DATABASE_URL antes de usar em produção:")
    print("   export DATABASE_URL=postgresql://usuario:senha@host/database")
    print()

if __name__ == '__main__':
    run_tests()
