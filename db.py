import sqlite3
import pandas as pd
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Detectar ambiente e tipo de banco de dados
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL and (DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')):
    # PostgreSQL no Render
    import psycopg2
    from psycopg2.extras import RealDictCursor
    # Fix: Render usa postgres:// mas psycopg2 precisa de postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    DB_TYPE = 'postgresql'
else:
    # SQLite local
    DB_PATH = Path(__file__).resolve().parent / "finance.db"
    DB_TYPE = 'sqlite'


def connect_db():
    """Conecta ao banco de dados (PostgreSQL ou SQLite)"""
    if DB_TYPE == 'postgresql':
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print('[DB] Usando PostgreSQL (Render)')
            return conn
        except Exception as e:
            print(f'[DB] ERRO ao conectar PostgreSQL: {e}')
            raise
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        print(f'[DB] Usando SQLite local: {DB_PATH}')
        return conn


def get_autoincrement_sql():
    """Retorna o SQL correto para auto-incremento dependendo do banco"""
    if DB_TYPE == 'postgresql':
        return 'SERIAL PRIMARY KEY'
    else:
        return 'INTEGER PRIMARY KEY AUTOINCREMENT'


def get_placeholder(index=None):
    """Retorna o placeholder correto para queries parametrizadas"""
    if DB_TYPE == 'postgresql':
        if index is not None:
            return f'${index}'
        return '%s'
    else:
        return '?'


def convert_query_placeholders(query, num_params=None):
    """Converte placeholders ? para o formato correto do banco"""
    if DB_TYPE == 'postgresql':
        if num_params is None:
            # Conta quantos ? existem
            num_params = query.count('?')
        # Substitui ? por $1, $2, $3, etc
        for i in range(num_params, 0, -1):
            query = query.replace('?', f'${i}', 1)
    return query


def init_db():
    conn = connect_db()
    cur = conn.cursor()
    
    autoincrement = get_autoincrement_sql()

    # Users table
    cur.execute(f"""CREATE TABLE IF NOT EXISTS users (
        id {autoincrement},
        username TEXT UNIQUE,
        password_hash TEXT,
        is_admin INTEGER DEFAULT 0,
        profile_photo TEXT
    )""")

    # Escolhemos adicionar user_id nas outras tabelas para associar registros a usuários
    cur.execute(f"""CREATE TABLE IF NOT EXISTS receitas (
        id {autoincrement},
        Valor REAL,
        Efetuado INTEGER,
        Fixo INTEGER,
        Data TEXT,
        Categoria TEXT,
        Descrição TEXT,
        user_id INTEGER,
        plano_id INTEGER
    )""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS despesas (
        id {autoincrement},
        Valor REAL,
        Status TEXT,
        Fixo INTEGER,
        Data TEXT,
        Categoria TEXT,
        Descrição TEXT,
        user_id INTEGER
    )""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS cat_receita (
        id {autoincrement},
        Categoria TEXT,
        user_id INTEGER
    )""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS cat_despesa (
        id {autoincrement},
        Categoria TEXT,
        user_id INTEGER
    )""")

    conn.commit()

    # Garante coluna user_id caso a versão anterior não a tivesse
    add_column_if_missing(conn, 'receitas', 'user_id INTEGER')
    add_column_if_missing(conn, 'despesas', 'user_id INTEGER')
    add_column_if_missing(conn, 'cat_receita', 'user_id INTEGER')
    add_column_if_missing(conn, 'cat_despesa', 'user_id INTEGER')
    
    # Garante coluna plano_id na tabela receitas
    add_column_if_missing(conn, 'receitas', 'plano_id INTEGER')

    # Garante coluna username nas tabelas de transações (manter para exibição)
    add_column_if_missing(conn, 'receitas', 'username TEXT')
    add_column_if_missing(conn, 'despesas', 'username TEXT')
    
    # Garante coluna profile_photo na tabela users
    add_column_if_missing(conn, 'users', 'profile_photo TEXT')
    
    # Garante coluna Status na tabela despesas e migra dados de Efetuado
    add_column_if_missing(conn, 'despesas', 'Status TEXT')
    migrate_efetuado_to_status(conn)

    # Se não houver usuários, cria um admin padrão (troque senha após o primeiro login)
    if get_user_count(conn) == 0:
        admin_id = create_user('admin', 'admin', conn=conn, is_admin=1)
        print(f"[DB] Created default admin user 'admin' (id={admin_id}) with password 'admin'. Change it ASAP.")

    # Atribui registros existentes ao admin se user_id for NULL
    admin = get_user_by_username('admin', conn=conn)
    if admin:
        cur.execute("UPDATE receitas SET user_id = ? WHERE user_id IS NULL", (admin['id'],))
        cur.execute("UPDATE despesas SET user_id = ? WHERE user_id IS NULL", (admin['id'],))
        cur.execute("UPDATE cat_receita SET user_id = ? WHERE user_id IS NULL", (admin['id'],))
        cur.execute("UPDATE cat_despesa SET user_id = ? WHERE user_id IS NULL", (admin['id'],))
        conn.commit()

    # Cria triggers para manter coluna `username` consistente com a tabela `users`
    try:
        create_username_triggers(conn)
    except Exception as e:
        print('[DB] warning: create_username_triggers failed:', e)

    # Cria tabelas de planos e metas
    try:
        init_planos_tables()
    except Exception as e:
        print('[DB] warning: init_planos_tables failed:', e)

    conn.close()

    # Garante que a coluna username nas tabelas de transações esteja preenchida a partir de users
    # (Corrige registros antigos que ficaram sem username)
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
    conn = connect_db()
    
    if user_id is not None:
        # Usar marcador de parâmetro correto para cada banco
        if DB_TYPE == 'postgresql':
            df = pd.read_sql_query(f"SELECT * FROM {table} WHERE user_id = %s", conn, params=(user_id,))
        else:
            df = pd.read_sql_query(f"SELECT * FROM {table} WHERE user_id = ?", conn, params=(user_id,))
    else:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    
    if 'Data' in df.columns:
        # Use ISO date strings for JSON serialization/consistency
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
    if not include_id and 'id' in df.columns:
        df = df.drop(columns=['id'])
    
    return df


def df_to_table(df, table):
    conn = connect_db()
    # Convert dates to ISO strings for storage
    if 'Data' in df.columns:
        df = df.copy()
        df['Data'] = df['Data'].astype(str)
    df.to_sql(table, conn, if_exists='replace', index=False)
    conn.close()

# ---------- Helpers para usuários e operações por usuário ---------- #

def add_column_if_missing(conn, table, column_def):
    """Adiciona coluna se não existir - compatível com SQLite e PostgreSQL"""
    cur = conn.cursor()
    col_name = column_def.split()[0]
    
    if DB_TYPE == 'postgresql':
        # PostgreSQL: verificar se coluna existe
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table, col_name))
        if not cur.fetchone():
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
            conn.commit()
    else:
        # SQLite: usar PRAGMA
        cur.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cur.fetchall()]
        if col_name not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
            conn.commit()


def get_user_count(conn=None):
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
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    pw_hash = generate_password_hash(password)
    try:
        cur.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?,?,?)", (username, pw_hash, is_admin))
        conn.commit()
        uid = cur.lastrowid
    except Exception as e:
        # possível duplicata - tenta selecionar usuário existente
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        uid = row[0] if row else None
    if close:
        conn.close()
    return uid


def get_user_by_username(username, conn=None):
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = ?", (username,))
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
    """Atualiza a foto de perfil de um usuário."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET profile_photo = ? WHERE id = ?", (photo_data, user_id))
    conn.commit()
    conn.close()


def get_user_profile_photo(user_id):
    """Retorna a foto de perfil de um usuário."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT profile_photo FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return '/assets/img_hom.png'  # foto padrão


def migrate_efetuado_to_status(conn=None):
    """Migra dados da coluna Efetuado para Status na tabela despesas (se a coluna Efetuado ainda existir)."""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    
    # Verifica se a coluna Efetuado existe
    cur.execute("PRAGMA table_info(despesas)")
    columns = [row[1] for row in cur.fetchall()]
    
    if 'Efetuado' in columns:
        # Migra apenas registros onde Status está NULL ou vazio
        # Efetuado = 1 -> "Pago"
        # Efetuado = 0 -> "A vencer"
        cur.execute("UPDATE despesas SET Status = 'Pago' WHERE (Status IS NULL OR Status = '') AND Efetuado = 1")
        cur.execute("UPDATE despesas SET Status = 'A vencer' WHERE (Status IS NULL OR Status = '') AND Efetuado = 0")
        conn.commit()
    
    if close:
        conn.close()


def update_status_vencidos(user_id=None):
    """Atualiza despesas com status 'A vencer' para 'Vencido' quando a data já passou."""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    hoje = datetime.now().strftime('%Y-%m-%d')
    
    if user_id:
        cur.execute("UPDATE despesas SET Status = 'Vencido' WHERE Status = 'A vencer' AND Data < ? AND user_id = ?", (hoje, user_id))
    else:
        cur.execute("UPDATE despesas SET Status = 'Vencido' WHERE Status = 'A vencer' AND Data < ?", (hoje,))
    
    conn.commit()
    conn.close()


def insert_cat(table, categoria, user_id):
    conn = connect_db()
    cur = conn.cursor()
    # evita duplicata para o mesmo usuário (pela combinação Categoria+user_id)
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE Categoria = ? AND user_id = ?", (categoria, user_id))
    if cur.fetchone()[0] == 0:
        cur.execute(f"INSERT INTO {table} (Categoria, user_id) VALUES (?,?)", (categoria, user_id))
        conn.commit()
    conn.close()


def delete_cat(table, categoria, user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE Categoria = ? AND user_id = ?", (categoria, user_id))
    conn.commit()
    conn.close()


def insert_transacao(table, valor, status, fixo, data, categoria, descricao, user_id, plano_id=None):
    conn = connect_db()
    cur = conn.cursor()
    if table == 'despesas':
        # Para despesas, recebido_ou_status é o Status ("Pago", "A vencer", "Vencido")
        cur.execute(f"INSERT INTO {table} (Valor, Status, Fixo, Data, Categoria, Descrição, user_id) VALUES (?,?,?,?,?,?,?)",
                    (valor, status, fixo, data, categoria, descricao, user_id))
    else:
        # Para receitas, mantém Efetuado e adiciona plano_id
        cur.execute(f"INSERT INTO {table} (Valor, Efetuado, Fixo, Data, Categoria, Descrição, user_id, plano_id) VALUES (?,?,?,?,?,?,?,?)",
                    (valor, status, fixo, data, categoria, descricao, user_id, plano_id))
    conn.commit()
    conn.close()


def update_transacao(table, row_id, fields, user_id):
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
    set_clause = ", ".join([f"{col} = ?" for col in payload.keys()])
    values = list(payload.values()) + [row_id, user_id]
    cur.execute(f"UPDATE {table} SET {set_clause} WHERE id = ? AND user_id = ?", values)
    conn.commit()
    conn.close()


def delete_transacao(table, row_id, user_id):
    try:
        row_id = int(row_id)
    except Exception:
        return
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ? AND user_id = ?", (row_id, user_id))
    conn.commit()
    conn.close()


def backfill_usernames(conn=None):
    """Preenche a coluna `username` nas tabelas `receitas` e `despesas` a partir da tabela `users` quando estiverem NULL ou vazias.
    Retorna um dicionário com contagens de linhas afetadas."""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()
    # Primeira passagem: apenas linhas sem username
    cur.execute("UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = despesas.user_id) WHERE username IS NULL OR username = ''")
    cur.execute("UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = receitas.user_id) WHERE username IS NULL OR username = ''")
    conn.commit()

    # Segunda passagem: garante que linhas com user_id preenchido possuam username (cobre casos inconsistentes)
    cur.execute("UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = despesas.user_id) WHERE user_id IS NOT NULL")
    cur.execute("UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = receitas.user_id) WHERE user_id IS NOT NULL")
    conn.commit()

    # Relatório de contagens
    cur.execute("SELECT COUNT(*) FROM despesas WHERE username IS NULL OR username = ''")
    rem_desp = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM receitas WHERE username IS NULL OR username = ''")
    rem_rec = cur.fetchone()[0]

    if close:
        conn.close()

    return {'remaining_despesas_without_username': rem_desp, 'remaining_receitas_without_username': rem_rec}


def create_username_triggers(conn=None):
    """Cria triggers para manter a coluna `username` consistente:
     - após INSERT/UPDATE em receitas/despesas (ajusta username a partir de users)
     - após UPDATE/DELETE em users (propaga mudanças ou limpa)
    """
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    cur = conn.cursor()

    # Ao inserir uma transação, preenche username a partir do user_id
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_set_username_on_receitas_insert
    AFTER INSERT ON receitas
    BEGIN
        UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """)

    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_set_username_on_despesas_insert
    AFTER INSERT ON despesas
    BEGIN
        UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """)

    # Ao atualizar user_id em uma transação, atualiza username também
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_update_username_on_receitas_userid
    AFTER UPDATE OF user_id ON receitas
    BEGIN
        UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """)

    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_update_username_on_despesas_userid
    AFTER UPDATE OF user_id ON despesas
    BEGIN
        UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """)

    # Ao atualizar username em users, propaga a mudança
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_update_username_on_users_update
    AFTER UPDATE OF username ON users
    BEGIN
        UPDATE receitas SET username = NEW.username WHERE user_id = NEW.id;
        UPDATE despesas SET username = NEW.username WHERE user_id = NEW.id;
    END;
    """)

    # Ao remover usuário, limpa o username nas transações
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_delete_user_set_username_null
    AFTER DELETE ON users
    BEGIN
        UPDATE receitas SET username = NULL WHERE user_id = OLD.id;
        UPDATE despesas SET username = NULL WHERE user_id = OLD.id;
    END;
    """)

    conn.commit()
    if close:
        conn.close()


# ---------- Funções de administração de usuários ---------- #

def get_all_users(conn=None):
    """Retorna lista de todos os usuários com informações básicas."""
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
    """Deleta um usuário e todos os seus dados relacionados."""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    
    cur = conn.cursor()
    
    # Deleta todos os dados relacionados ao usuário
    cur.execute("DELETE FROM receitas WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM despesas WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM cat_receita WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM cat_despesa WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
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
    cur.execute("UPDATE users SET is_admin = ? WHERE id = ?", (is_admin, user_id))
    conn.commit()
    
    if close:
        conn.close()
    
    return True


def cleanup_orphan_categories(conn=None):
    """Remove categorias sem user_id (órfãs/globais)."""
    close = False
    if conn is None:
        conn = connect_db()
        close = True
    
    cur = conn.cursor()
    
    # Remove categorias sem usuário
    cur.execute("DELETE FROM cat_receita WHERE user_id IS NULL")
    cur.execute("DELETE FROM cat_despesa WHERE user_id IS NULL")
    
    deleted_receitas = cur.rowcount
    conn.commit()
    
    cur.execute("SELECT changes()")
    deleted_despesas = cur.fetchone()[0]
    
    if close:
        conn.close()
    
    return {'deleted_cat_receita': deleted_receitas, 'deleted_cat_despesa': deleted_despesas}


# ---------- Funções para Planos e Metas ---------- #

def init_planos_tables():
    """Cria as tabelas de planos e montantes se não existirem."""
    conn = connect_db()
    cur = conn.cursor()
    
    # Tabela de planos/metas
    cur.execute("""CREATE TABLE IF NOT EXISTS planos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        valor_total REAL,
        valor_acumulado REAL DEFAULT 0,
        categoria_despesa TEXT,
        user_id INTEGER,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )""")
    
    # Tabela de montantes acumulados
    cur.execute("""CREATE TABLE IF NOT EXISTS montantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instituicao TEXT,
        tipo TEXT,
        valor REAL,
        user_id INTEGER,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )""")
    
    # Tabela de anotações
    cur.execute("""CREATE TABLE IF NOT EXISTS anotacoes_planos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conteudo TEXT,
        user_id INTEGER UNIQUE,
        updated_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )""")
    
    conn.commit()
    conn.close()


def get_planos_by_user(user_id):
    """Retorna todos os planos de um usuário."""
    conn = connect_db()
    df = pd.read_sql_query(
        "SELECT id, nome, valor_total, valor_acumulado, categoria_despesa FROM planos WHERE user_id = ?",
        conn, params=(user_id,)
    )
    conn.close()
    return df.to_dict('records')


def insert_plano(nome, valor_total, valor_acumulado, categoria_despesa, user_id):
    """Insere um novo plano."""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(
        "INSERT INTO planos (nome, valor_total, valor_acumulado, categoria_despesa, user_id, created_at) VALUES (?,?,?,?,?,?)",
        (nome, valor_total, valor_acumulado, categoria_despesa, user_id, created_at)
    )
    conn.commit()
    plano_id = cur.lastrowid
    conn.close()
    return plano_id


def update_plano(plano_id, nome, valor_total, valor_acumulado, categoria_despesa):
    """Atualiza um plano existente."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE planos SET nome = ?, valor_total = ?, valor_acumulado = ?, categoria_despesa = ? WHERE id = ?",
        (nome, valor_total, valor_acumulado, categoria_despesa, plano_id)
    )
    conn.commit()
    conn.close()


def delete_plano(plano_id, user_id):
    """Deleta um plano."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM planos WHERE id = ? AND user_id = ?", (plano_id, user_id))
    conn.commit()
    conn.close()


def calculate_plano_valor_acumulado(plano_id, user_id):
    """Calcula o valor acumulado de um plano baseado nas receitas destinadas a esse plano."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT SUM(Valor) FROM receitas WHERE plano_id = ? AND Efetuado = 1 AND user_id = ?",
        (plano_id, user_id)
    )
    result = cur.fetchone()[0]
    conn.close()
    return result if result else 0


def get_montantes_by_user(user_id):
    """Retorna todos os montantes de um usuário."""
    conn = connect_db()
    df = pd.read_sql_query(
        "SELECT id, instituicao, tipo, valor FROM montantes WHERE user_id = ?",
        conn, params=(user_id,)
    )
    conn.close()
    return df.to_dict('records')


def insert_montante(instituicao, tipo, valor, user_id):
    """Insere um novo montante."""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(
        "INSERT INTO montantes (instituicao, tipo, valor, user_id, created_at) VALUES (?,?,?,?,?)",
        (instituicao, tipo, valor, user_id, created_at)
    )
    conn.commit()
    montante_id = cur.lastrowid
    conn.close()
    return montante_id


def update_montante(montante_id, instituicao, tipo, valor):
    """Atualiza um montante existente."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE montantes SET instituicao = ?, tipo = ?, valor = ? WHERE id = ?",
        (instituicao, tipo, valor, montante_id)
    )
    conn.commit()
    conn.close()


def delete_montante(montante_id, user_id):
    """Deleta um montante."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM montantes WHERE id = ? AND user_id = ?", (montante_id, user_id))
    conn.commit()
    conn.close()


def get_anotacoes_planos(user_id):
    """Retorna as anotações de planos de um usuário."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT conteudo FROM anotacoes_planos WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""


def save_anotacoes_planos(user_id, conteudo):
    """Salva as anotações de planos de um usuário."""
    from datetime import datetime
    conn = connect_db()
    cur = conn.cursor()
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Verifica se já existe
    cur.execute("SELECT id FROM anotacoes_planos WHERE user_id = ?", (user_id,))
    exists = cur.fetchone()
    
    if exists:
        cur.execute("UPDATE anotacoes_planos SET conteudo = ?, updated_at = ? WHERE user_id = ?",
                   (conteudo, updated_at, user_id))
    else:
        cur.execute("INSERT INTO anotacoes_planos (conteudo, user_id, updated_at) VALUES (?,?,?)",
                   (conteudo, user_id, updated_at))
    
    conn.commit()
    conn.close()
