import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine

# PostgreSQL Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/finance_app')

# Fix: Render usa postgres:// mas psycopg2 precisa de postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# SQLAlchemy engine para uso com pandas
_engine = None

def get_engine():
    """Retorna SQLAlchemy engine (singleton)"""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
        print('[DB] SQLAlchemy engine criado')
    return _engine


def connect_db():
    """Conecta ao banco de dados PostgreSQL usando psycopg2 para operações diretas"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print('[DB] Conectado ao PostgreSQL')
        return conn
    except Exception as e:
        print(f'[DB] ERRO ao conectar PostgreSQL: {e}')
        raise


def init_db():
    conn = connect_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        is_admin INTEGER DEFAULT 0,
        profile_photo TEXT
    )""")

    # Receitas table
    cur.execute("""CREATE TABLE IF NOT EXISTS receitas (
        id SERIAL PRIMARY KEY,
        Valor REAL,
        Efetuado INTEGER,
        Fixo INTEGER,
        Data TEXT,
        Categoria TEXT,
        Descrição TEXT,
        user_id INTEGER,
        plano_id INTEGER,
        username TEXT
    )""")

    # Despesas table
    cur.execute("""CREATE TABLE IF NOT EXISTS despesas (
        id SERIAL PRIMARY KEY,
        Valor REAL,
        Status TEXT,
        Fixo INTEGER,
        Data TEXT,
        Categoria TEXT,
        Descrição TEXT,
        user_id INTEGER,
        username TEXT
    )""")

    # Categorias de receita
    cur.execute("""CREATE TABLE IF NOT EXISTS cat_receita (
        id SERIAL PRIMARY KEY,
        Categoria TEXT,
        user_id INTEGER
    )""")

    # Categorias de despesa
    cur.execute("""CREATE TABLE IF NOT EXISTS cat_despesa (
        id SERIAL PRIMARY KEY,
        Categoria TEXT,
        user_id INTEGER
    )""")

    # Orçamentos por categoria
    cur.execute("""CREATE TABLE IF NOT EXISTS orcamentos (
        id SERIAL PRIMARY KEY,
        categoria TEXT,
        valor_limite REAL,
        mes INTEGER,
        ano INTEGER,
        user_id INTEGER,
        UNIQUE(categoria, mes, ano, user_id)
    )""")

    conn.commit()

    # Se não houver usuários, cria um admin padrão
    if get_user_count(conn) == 0:
        admin_id = create_user('admin', 'admin', conn=conn, is_admin=1)
        print(f"[DB] Created default admin user 'admin' (id={admin_id}) with password 'admin'. Change it ASAP.")

    # Atribui registros existentes ao admin se user_id for NULL
    admin = get_user_by_username('admin', conn=conn)
    if admin:
        cur.execute("UPDATE receitas SET user_id = %s WHERE user_id IS NULL", (admin['id'],))
        cur.execute("UPDATE despesas SET user_id = %s WHERE user_id IS NULL", (admin['id'],))
        cur.execute("UPDATE cat_receita SET user_id = %s WHERE user_id IS NULL", (admin['id'],))
        cur.execute("UPDATE cat_despesa SET user_id = %s WHERE user_id IS NULL", (admin['id'],))
        conn.commit()

    # Cria tabelas de planos e metas
    try:
        init_planos_tables()
    except Exception as e:
        print('[DB] warning: init_planos_tables failed:', e)

    conn.close()

    # Garante que a coluna username nas tabelas de transações esteja preenchida a partir de users
    try:
        backfill_usernames()
    except Exception as e:
        print('[DB] warning: backfill_usernames failed:', e)
    
    # Limpa categorias órfãs (sem user_id) - evita problemas de categorias globais
    try:
        cleanup_orphan_categories()
    except Exception as e:
        print('[DB] warning: cleanup_orphan_categories failed:', e)


def table_to_df(table, user_id=None, include_id=False):
    """Carrega tabela como DataFrame, opcionalmente filtrando por user_id"""
    engine = get_engine()
    
    if user_id is not None:
        query = f"SELECT * FROM {table} WHERE user_id = %(user_id)s"
        print(f"[DB] table_to_df - Executando: {query} com user_id={user_id}")
        df = pd.read_sql_query(query, engine, params={"user_id": user_id})
    else:
        query = f"SELECT * FROM {table}"
        print(f"[DB] table_to_df - Executando: {query}")
        df = pd.read_sql_query(query, engine)
    
    print(f"[DB] table_to_df - Resultado: {len(df)} linhas, colunas={df.columns.tolist()}")
    
    # Capitalizar apenas colunas específicas usadas em transações (receitas/despesas)
    # Mantém o resto em minúsculas como vem do banco
    cols_to_capitalize = ['categoria', 'valor', 'data', 'efetuado', 'fixo', 'descrição', 'status']
    df.columns = [col.title() if col in cols_to_capitalize else col for col in df.columns]
    
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
    if not include_id and 'id' in df.columns:
        df = df.drop(columns=['id'])
    
    return df


def df_to_table(df, table):
    """Substitui tabela inteira com DataFrame"""
    conn = connect_db()
    if 'Data' in df.columns:
        df = df.copy()
        df['Data'] = df['Data'].astype(str)
    df.to_sql(table, conn, if_exists='replace', index=False)
    conn.close()


# ---------- Helpers para usuários ---------- #

def get_user_count(conn=None):
    """Retorna quantidade de usuários cadastrados"""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    cnt = cur.fetchone()[0]
    if close:
        conn.close()
    return cnt


def create_user(username, password, conn=None, is_admin=0):
    """Cria novo usuário e retorna ID"""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    pw_hash = generate_password_hash(password)
    try:
        cur.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (%s,%s,%s) RETURNING id", (username, pw_hash, is_admin))
        uid = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        # possível duplicata - rollback e tenta selecionar usuário existente
        conn.rollback()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        uid = row[0] if row else None
    if close:
        conn.close()
    return uid


def get_user_by_username(username, conn=None):
    """Busca usuário por username"""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    if close:
        conn.close()
    if not row:
        return None
    return {'id': row[0], 'username': row[1], 'password_hash': row[2], 'is_admin': row[3]}


def verify_user(username, password):
    user = get_user_by_username(username)
    if not user:
        return None
    if check_password_hash(user['password_hash'], password):
        return {'id': user['id'], 'username': user['username'], 'is_admin': user['is_admin']}
    return None


def update_user_profile_photo(user_id, photo_data):
    """Atualiza a foto de perfil de um usuário"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET profile_photo = %s WHERE id = %s", (photo_data, user_id))
    conn.commit()
    conn.close()


def get_user_profile_photo(user_id):
    """Retorna a foto de perfil de um usuário"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT profile_photo FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return '/assets/img_hom.png'


# ---------- Funções de transações e categorias ---------- #

def update_status_vencidos(user_id=None):
    """Atualiza despesas com status 'A vencer' para 'Vencido' quando a data já passou"""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    hoje = datetime.now().strftime('%Y-%m-%d')
    
    if user_id:
        cur.execute("UPDATE despesas SET status = 'Vencido' WHERE status = 'A vencer' AND data < %s AND user_id = %s", (hoje, user_id))
    else:
        cur.execute("UPDATE despesas SET status = 'Vencido' WHERE status = 'A vencer' AND data < %s", (hoje,))
    
    conn.commit()
    conn.close()


def insert_cat(table, categoria, user_id):
    """Insere categoria se não existir para o usuário"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE Categoria = %s AND user_id = %s", (categoria, user_id))
    count = cur.fetchone()[0]
    print(f"[DB] insert_cat - Verificando categoria '{categoria}' na tabela '{table}' para user_id={user_id}: count={count}")
    
    if count == 0:
        cur.execute(f"INSERT INTO {table} (Categoria, user_id) VALUES (%s,%s)", (categoria, user_id))
        conn.commit()
        print(f"[DB] insert_cat - Categoria '{categoria}' inserida com sucesso!")
    else:
        print(f"[DB] insert_cat - Categoria '{categoria}' já existe para este usuário")
    
    conn.close()


def delete_cat(table, categoria, user_id):
    """Deleta categoria do usuário"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE Categoria = %s AND user_id = %s", (categoria, user_id))
    conn.commit()
    conn.close()


def insert_transacao(table, valor, status, fixo, data, categoria, descricao, user_id, plano_id=None):
    """Insere transação (receita ou despesa)"""
    conn = connect_db()
    cur = conn.cursor()
    if table == 'despesas':
        cur.execute(f"INSERT INTO {table} (Valor, Status, Fixo, Data, Categoria, Descrição, user_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (valor, status, fixo, data, categoria, descricao, user_id))
    else:
        cur.execute(f"INSERT INTO {table} (Valor, Efetuado, Fixo, Data, Categoria, Descrição, user_id, plano_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (valor, status, fixo, data, categoria, descricao, user_id, plano_id))
    conn.commit()
    conn.close()


def update_transacao(table, row_id, fields, user_id):
    """Atualiza transação existente"""
    if not fields:
        return
    allowed = {"Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "Status"}
    payload = {k: v for k, v in fields.items() if k in allowed}
    if not payload:
        return
    try:
        row_id = int(row_id)
    except Exception:
        return
    conn = connect_db()
    cur = conn.cursor()
    set_clause = ", ".join([f"{col} = %s" for col in payload.keys()])
    values = list(payload.values()) + [row_id, user_id]
    cur.execute(f"UPDATE {table} SET {set_clause} WHERE id = %s AND user_id = %s", values)
    conn.commit()
    conn.close()


def delete_transacao(table, row_id, user_id):
    """Deleta transação"""
    try:
        row_id = int(row_id)
    except Exception:
        return
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = %s AND user_id = %s", (row_id, user_id))
    conn.commit()
    conn.close()



def delete_cat(table, categoria, user_id):
    """Deleta categoria do usuário"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE Categoria = %s AND user_id = %s", (categoria, user_id))
    conn.commit()
    conn.close()


def insert_transacao(table, valor, status, fixo, data, categoria, descricao, user_id, plano_id=None):
    """Insere transação (receita ou despesa)"""
    conn = connect_db()
    cur = conn.cursor()
    if table == 'despesas':
        cur.execute(f"INSERT INTO {table} (Valor, Status, Fixo, Data, Categoria, Descrição, user_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (valor, status, fixo, data, categoria, descricao, user_id))
    else:
        cur.execute(f"INSERT INTO {table} (Valor, Efetuado, Fixo, Data, Categoria, Descrição, user_id, plano_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (valor, status, fixo, data, categoria, descricao, user_id, plano_id))
    conn.commit()
    conn.close()


def update_transacao(table, row_id, fields, user_id):
    """Atualiza transação existente"""
    if not fields:
        return
    allowed = {"Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "Status"}
    payload = {k: v for k, v in fields.items() if k in allowed}
    if not payload:
        return
    try:
        row_id = int(row_id)
    except Exception:
        return
    conn = connect_db()
    cur = conn.cursor()
    set_clause = ", ".join([f"{col} = %s" for col in payload.keys()])
    values = list(payload.values()) + [row_id, user_id]
    cur.execute(f"UPDATE {table} SET {set_clause} WHERE id = %s AND user_id = %s", values)
    conn.commit()
    conn.close()


def delete_transacao(table, row_id, user_id):
    """Deleta transação"""
    try:
        row_id = int(row_id)
    except Exception:
        return
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = %s AND user_id = %s", (row_id, user_id))
    conn.commit()
    conn.close()


def insert_despesa_parcelada(valor, status, fixo, data, categoria, descricao, user_id, num_parcelas):
    """Insere despesas parceladas nos meses subsequentes"""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Converte a data string para datetime
    data_inicial = datetime.strptime(data, '%Y-%m-%d')
    
    # Insere cada parcela
    for i in range(num_parcelas):
        # Calcula a data da parcela (adiciona i meses à data inicial)
        data_parcela = data_inicial + relativedelta(months=i)
        data_parcela_str = data_parcela.strftime('%Y-%m-%d')
        
        # Atualiza a descrição para incluir o número da parcela
        if num_parcelas > 1:
            descricao_parcela = f"{descricao} - Parcela {i+1}/{num_parcelas}"
        else:
            descricao_parcela = descricao
        
        # Insere a parcela
        cur.execute(
            "INSERT INTO despesas (Valor, Status, Fixo, Data, Categoria, Descrição, user_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (valor, status, fixo, data_parcela_str, categoria, descricao_parcela, user_id)
        )
    
    conn.commit()
    conn.close()
    print(f"[DB] Inseridas {num_parcelas} parcelas de despesa para o usuário {user_id}")


# ---------- Funções de Orçamento ---------- #

def set_orcamento(categoria, valor_limite, mes, ano, user_id):
    """Define ou atualiza orçamento para uma categoria em um mês/ano específico"""
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO orcamentos (categoria, valor_limite, mes, ano, user_id) 
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (categoria, mes, ano, user_id) 
               DO UPDATE SET valor_limite = EXCLUDED.valor_limite""",
            (categoria, valor_limite, mes, ano, user_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[DB] Erro ao definir orçamento: {e}")
        raise
    finally:
        conn.close()


def get_orcamentos(user_id, mes=None, ano=None):
    """Retorna orçamentos do usuário, opcionalmente filtrados por mês/ano"""
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if mes and ano:
        cur.execute(
            "SELECT * FROM orcamentos WHERE user_id = %s AND mes = %s AND ano = %s ORDER BY categoria",
            (user_id, mes, ano)
        )
    else:
        cur.execute(
            "SELECT * FROM orcamentos WHERE user_id = %s ORDER BY ano DESC, mes DESC, categoria",
            (user_id,)
        )
    
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_orcamento(orcamento_id, user_id):
    """Deleta orçamento específico"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM orcamentos WHERE id = %s AND user_id = %s", (orcamento_id, user_id))
    conn.commit()
    conn.close()


def get_gastos_por_categoria(user_id, mes, ano):
    """Retorna total gasto por categoria em um mês/ano específico"""
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Calcula primeiro e último dia do mês
    from datetime import date
    primeiro_dia = date(ano, mes, 1).strftime('%Y-%m-%d')
    if mes == 12:
        ultimo_dia = date(ano, 12, 31).strftime('%Y-%m-%d')
    else:
        from datetime import timedelta
        ultimo_dia = (date(ano, mes + 1, 1) - timedelta(days=1)).strftime('%Y-%m-%d')
    
    cur.execute(
        """SELECT categoria, SUM(valor) as total_gasto
           FROM despesas
           WHERE user_id = %s AND data >= %s AND data <= %s
           GROUP BY categoria""",
        (user_id, primeiro_dia, ultimo_dia)
    )
    
    rows = cur.fetchall()
    conn.close()
    return {row['categoria']: row['total_gasto'] for row in rows}


def backfill_usernames(conn=None):
    """Preenche a coluna username nas tabelas receitas e despesas"""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    cur.execute("UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = despesas.user_id) WHERE username IS NULL OR username = ''")
    cur.execute("UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = receitas.user_id) WHERE username IS NULL OR username = ''")
    conn.commit()
    cur.execute("UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = despesas.user_id) WHERE user_id IS NOT NULL")
    cur.execute("UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = receitas.user_id) WHERE user_id IS NOT NULL")
    conn.commit()
    
    if close:
        conn.close()


# ---------- Funções de administração ---------- #

def get_all_users(conn=None):
    """Retorna lista de todos os usuários com informações básicas"""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    cur.execute("SELECT id, username, is_admin FROM users ORDER BY id")
    rows = cur.fetchall()
    if close:
        conn.close()
    return [{'id': row[0], 'username': row[1], 'is_admin': row[2]} for row in rows]


def delete_user(user_id, conn=None):
    """Deleta um usuário e todos os seus dados relacionados"""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    
    cur = conn.cursor()
    # Deletar na ordem correta (tabelas dependentes primeiro)
    cur.execute("DELETE FROM planos WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM montantes WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM anotacoes_planos WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM receitas WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM despesas WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM cat_receita WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM cat_despesa WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    
    if close:
        conn.close()
    
    return True


def change_user_admin_status(user_id, is_admin, conn=None):
    """Altera o status de admin de um usuário."""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin = %s WHERE id = %s", (is_admin, user_id))
    conn.commit()
    
    if close:
        conn.close()
    
    return True


def cleanup_orphan_categories(conn=None):
    """Remove categorias sem user_id (órfãs/globais)"""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    
    cur = conn.cursor()
    cur.execute("DELETE FROM cat_receita WHERE user_id IS NULL")
    deleted_receitas = cur.rowcount
    cur.execute("DELETE FROM cat_despesa WHERE user_id IS NULL")
    deleted_despesas = cur.rowcount
    conn.commit()
    
    if close:
        conn.close()
    
    return {'deleted_cat_receita': deleted_receitas, 'deleted_cat_despesa': deleted_despesas}


# ---------- Funções para Planos e Metas ---------- #

def init_planos_tables():
    """Cria as tabelas de planos e montantes se não existirem"""
    conn = connect_db()
    cur = conn.cursor()
    
    # Tabela de planos/metas
    cur.execute("""CREATE TABLE IF NOT EXISTS planos (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        valor_total REAL,
        valor_acumulado REAL DEFAULT 0,
        categoria_despesa TEXT,
        user_id INTEGER,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )""")
    
    # Tabela de montantes acumulados (investimentos)
    cur.execute("""CREATE TABLE IF NOT EXISTS montantes (
        id SERIAL PRIMARY KEY,
        instituicao TEXT,
        tipo TEXT,
        valor REAL,
        tipo_rendimento TEXT DEFAULT 'Sem rendimento',
        taxa_percentual REAL DEFAULT 0,
        data_inicio TEXT,
        valor_inicial REAL,
        user_id INTEGER,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )""")
    
    # Adicionar colunas novas se não existirem (migração)
    try:
        cur.execute("ALTER TABLE montantes ADD COLUMN IF NOT EXISTS tipo_rendimento TEXT DEFAULT 'Sem rendimento'")
        cur.execute("ALTER TABLE montantes ADD COLUMN IF NOT EXISTS taxa_percentual REAL DEFAULT 0")
        cur.execute("ALTER TABLE montantes ADD COLUMN IF NOT EXISTS data_inicio TEXT")
        cur.execute("ALTER TABLE montantes ADD COLUMN IF NOT EXISTS valor_inicial REAL")
    except:
        pass
    
    # Tabela de anotações
    cur.execute("""CREATE TABLE IF NOT EXISTS anotacoes_planos (
        id SERIAL PRIMARY KEY,
        conteudo TEXT,
        user_id INTEGER UNIQUE,
        updated_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )""")
    
    conn.commit()
    conn.close()


def get_planos_by_user(user_id):
    """Retorna todos os planos de um usuário"""
    engine = get_engine()
    df = pd.read_sql_query(
        "SELECT id, nome, valor_total, valor_acumulado, categoria_despesa FROM planos WHERE user_id = %(user_id)s",
        engine, params={"user_id": user_id}
    )
    # Mantém nomes de colunas como vêm do banco (minúsculas)
    return df.to_dict('records')


def insert_plano(nome, valor_total, valor_acumulado, categoria_despesa, user_id):
    """Insere um novo plano"""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(
        "INSERT INTO planos (nome, valor_total, valor_acumulado, categoria_despesa, user_id, created_at) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
        (nome, valor_total, valor_acumulado, categoria_despesa, user_id, created_at)
    )
    plano_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return plano_id


def update_plano(plano_id, nome, valor_total, valor_acumulado, categoria_despesa):
    """Atualiza um plano existente"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE planos SET nome = %s, valor_total = %s, valor_acumulado = %s, categoria_despesa = %s WHERE id = %s",
        (nome, valor_total, valor_acumulado, categoria_despesa, plano_id)
    )
    conn.commit()
    conn.close()


def delete_plano(plano_id, user_id):
    """Deleta um plano"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM planos WHERE id = %s AND user_id = %s", (plano_id, user_id))
    conn.commit()
    conn.close()


def calculate_plano_valor_acumulado(plano_id, user_id):
    """Calcula o valor acumulado de um plano baseado nas receitas destinadas a esse plano"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT SUM(Valor) FROM receitas WHERE plano_id = %s AND Efetuado = 1 AND user_id = %s",
        (plano_id, user_id)
    )
    result = cur.fetchone()[0]
    conn.close()
    return result if result else 0


def get_montantes_by_user(user_id):
    """Retorna todos os montantes/investimentos de um usuário"""
    engine = get_engine()
    df = pd.read_sql_query(
        """SELECT id, instituicao, tipo, valor, tipo_rendimento, taxa_percentual, 
                  data_inicio, valor_inicial 
           FROM montantes WHERE user_id = %(user_id)s""",
        engine, params={"user_id": user_id}
    )
    # Mantém nomes de colunas como vêm do banco (minúsculas)
    return df.to_dict('records')


def insert_montante(instituicao, tipo, valor, tipo_rendimento, taxa_percentual, data_inicio, valor_inicial, user_id):
    """Insere um novo investimento/montante"""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(
        """INSERT INTO montantes (instituicao, tipo, valor, tipo_rendimento, taxa_percentual, 
                                   data_inicio, valor_inicial, user_id, created_at) 
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (instituicao, tipo, valor, tipo_rendimento, taxa_percentual, data_inicio, valor_inicial, user_id, created_at)
    )
    montante_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return montante_id


def update_montante(montante_id, instituicao, tipo, valor, tipo_rendimento, taxa_percentual, data_inicio, valor_inicial):
    """Atualiza um investimento/montante existente"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """UPDATE montantes SET instituicao = %s, tipo = %s, valor = %s, tipo_rendimento = %s, 
                                taxa_percentual = %s, data_inicio = %s, valor_inicial = %s 
           WHERE id = %s""",
        (instituicao, tipo, valor, tipo_rendimento, taxa_percentual, data_inicio, valor_inicial, montante_id)
    )
    conn.commit()
    conn.close()


def delete_montante(montante_id, user_id):
    """Deleta um montante"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM montantes WHERE id = %s AND user_id = %s", (montante_id, user_id))
    conn.commit()
    conn.close()


def get_anotacoes_planos(user_id):
    """Retorna as anotações de planos de um usuário"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT conteudo FROM anotacoes_planos WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""


def save_anotacoes_planos(user_id, conteudo):
    """Salva as anotações de planos de um usuário"""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Verifica se já existe
    cur.execute("SELECT id FROM anotacoes_planos WHERE user_id = %s", (user_id,))
    exists = cur.fetchone()
    
    if exists:
        cur.execute("UPDATE anotacoes_planos SET conteudo = %s, updated_at = %s WHERE user_id = %s",
                   (conteudo, updated_at, user_id))
    else:
        cur.execute("INSERT INTO anotacoes_planos (conteudo, user_id, updated_at) VALUES (%s,%s,%s)",
                   (conteudo, user_id, updated_at))
    
    conn.commit()
    conn.close()


# ========= Funções de Cálculo de Rendimento ========= #

def calcular_rendimento_investimento(valor_inicial, tipo_rendimento, taxa_percentual, dias_decorridos):
    """
    Calcula o rendimento de um investimento
    
    Args:
        valor_inicial: Valor inicial investido
        tipo_rendimento: Tipo de rendimento (% do CDI, Taxa fixa, etc.)
        taxa_percentual: Taxa/percentual do rendimento
        dias_decorridos: Número de dias desde o início do investimento
    
    Returns:
        dict com valor_atual, rendimento_total, rendimento_diario, rendimento_mensal, rendimento_anual
    """
    from constants import TAXA_CDI_ANUAL, TAXA_SELIC_ANUAL, TAXA_IPCA_ANUAL
    
    if not valor_inicial or valor_inicial <= 0:
        return {
            'valor_atual': 0,
            'rendimento_total': 0,
            'rendimento_diario': 0,
            'rendimento_mensal': 0,
            'rendimento_anual': 0
        }
    
    taxa_anual = 0
    
    # Determina a taxa anual baseada no tipo de rendimento
    if tipo_rendimento == "Sem rendimento":
        taxa_anual = 0
    
    elif tipo_rendimento == "% do CDI":
        # Ex: 100% do CDI com CDI a 10.65% a.a.
        taxa_anual = (taxa_percentual / 100) * TAXA_CDI_ANUAL
    
    elif tipo_rendimento == "Taxa fixa (% a.a.)":
        taxa_anual = taxa_percentual
    
    elif tipo_rendimento == "IPCA + (% a.a.)":
        taxa_anual = TAXA_IPCA_ANUAL + taxa_percentual
    
    elif tipo_rendimento == "100% da Selic":
        taxa_anual = TAXA_SELIC_ANUAL
    
    elif tipo_rendimento == "Poupança (0.5% a.m.)":
        taxa_anual = 0.5 * 12  # 6% a.a.
    
    # Conversão para taxa diária (juros compostos)
    taxa_diaria = (1 + taxa_anual/100) ** (1/252) - 1  # 252 dias úteis no ano
    
    # Cálculo do montante com juros compostos
    valor_atual = valor_inicial * ((1 + taxa_diaria) ** dias_decorridos)
    rendimento_total = valor_atual - valor_inicial
    
    # Estimativas de rendimento
    rendimento_diario = valor_atual * taxa_diaria
    rendimento_mensal = valor_atual * ((1 + taxa_diaria) ** 21 - 1)  # 21 dias úteis no mês
    rendimento_anual = valor_atual * ((1 + taxa_diaria) ** 252 - 1)  # 252 dias úteis no ano
    
    return {
        'valor_atual': round(valor_atual, 2),
        'rendimento_total': round(rendimento_total, 2),
        'rendimento_diario': round(rendimento_diario, 2),
        'rendimento_mensal': round(rendimento_mensal, 2),
        'rendimento_anual': round(rendimento_anual, 2)
    }


def atualizar_valores_investimentos(user_id):
    """Atualiza os valores de todos os investimentos de um usuário com base nos rendimentos"""
    from datetime import datetime, date
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Busca todos os investimentos do usuário
    cur.execute(
        """SELECT id, valor_inicial, tipo_rendimento, taxa_percentual, data_inicio 
           FROM montantes WHERE user_id = %s AND data_inicio IS NOT NULL""",
        (user_id,)
    )
    
    investimentos = cur.fetchall()
    
    hoje = date.today()
    
    for inv in investimentos:
        inv_id, valor_inicial, tipo_rendimento, taxa_percentual, data_inicio_str = inv
        
        if not valor_inicial or not data_inicio_str:
            continue
        
        # Calcula dias decorridos
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        dias_decorridos = (hoje - data_inicio).days
        
        if dias_decorridos < 0:
            dias_decorridos = 0
        
        # Calcula novo valor
        resultado = calcular_rendimento_investimento(
            valor_inicial, 
            tipo_rendimento or "Sem rendimento", 
            taxa_percentual or 0, 
            dias_decorridos
        )
        
        # Atualiza valor no banco
        cur.execute(
            "UPDATE montantes SET valor = %s WHERE id = %s",
            (resultado['valor_atual'], inv_id)
        )
    
    conn.commit()
    conn.close()
