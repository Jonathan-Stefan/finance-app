"""
Queries SQL centralizadas
Mantém todas as queries SQL em um único lugar para facilitar manutenção
"""


# ========= Users Queries ========= #
class UserQueries:
    """Queries relacionadas à tabela de usuários"""
    
    CREATE_TABLE = """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        is_admin INTEGER DEFAULT 0,
        profile_photo TEXT
    )"""
    
    INSERT = "INSERT INTO users (username, password_hash, is_admin) VALUES (?,?,?)"
    
    GET_BY_USERNAME = "SELECT id, username, password_hash, is_admin FROM users WHERE username = ?"
    
    GET_BY_ID = "SELECT id, username, password_hash, is_admin FROM users WHERE id = ?"
    
    GET_ALL = "SELECT id, username, is_admin FROM users ORDER BY id"
    
    COUNT = "SELECT COUNT(*) FROM users"
    
    UPDATE_PHOTO = "UPDATE users SET profile_photo = ? WHERE id = ?"
    
    GET_PHOTO = "SELECT profile_photo FROM users WHERE id = ?"
    
    UPDATE_ADMIN_STATUS = "UPDATE users SET is_admin = ? WHERE id = ?"
    
    DELETE = "DELETE FROM users WHERE id = ?"


# ========= Receitas Queries ========= #
class ReceitasQueries:
    """Queries relacionadas à tabela de receitas"""
    
    CREATE_TABLE = """CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Valor REAL,
        Efetuado INTEGER,
        Fixo INTEGER,
        Data TEXT,
        Categoria TEXT,
        Descrição TEXT,
        user_id INTEGER,
        username TEXT
    )"""
    
    INSERT = """INSERT INTO receitas 
        (Valor, Efetuado, Fixo, Data, Categoria, Descrição, user_id) 
        VALUES (?,?,?,?,?,?,?)"""
    
    SELECT_BY_USER = "SELECT * FROM receitas WHERE user_id = ?"
    
    SELECT_ALL = "SELECT * FROM receitas"
    
    DELETE = "DELETE FROM receitas WHERE id = ? AND user_id = ?"
    
    UPDATE_USERNAME_NULL = "UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = receitas.user_id) WHERE username IS NULL OR username = ''"
    
    UPDATE_USERNAME_ALL = "UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = receitas.user_id) WHERE user_id IS NOT NULL"
    
    UPDATE_USER_ID = "UPDATE receitas SET user_id = ? WHERE user_id IS NULL"
    
    DELETE_BY_USER = "DELETE FROM receitas WHERE user_id = ?"


# ========= Despesas Queries ========= #
class DespesasQueries:
    """Queries relacionadas à tabela de despesas"""
    
    CREATE_TABLE = """CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Valor REAL,
        Status TEXT,
        Fixo INTEGER,
        Data TEXT,
        Categoria TEXT,
        Descrição TEXT,
        user_id INTEGER,
        username TEXT
    )"""
    
    INSERT = """INSERT INTO despesas 
        (Valor, Status, Fixo, Data, Categoria, Descrição, user_id) 
        VALUES (?,?,?,?,?,?,?)"""
    
    SELECT_BY_USER = "SELECT * FROM despesas WHERE user_id = ?"
    
    SELECT_ALL = "SELECT * FROM despesas"
    
    DELETE = "DELETE FROM despesas WHERE id = ? AND user_id = ?"
    
    UPDATE_STATUS_VENCIDOS = "UPDATE despesas SET Status = 'Vencido' WHERE Status = 'A vencer' AND Data < ?"
    
    UPDATE_STATUS_VENCIDOS_BY_USER = "UPDATE despesas SET Status = 'Vencido' WHERE Status = 'A vencer' AND Data < ? AND user_id = ?"
    
    UPDATE_USERNAME_NULL = "UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = despesas.user_id) WHERE username IS NULL OR username = ''"
    
    UPDATE_USERNAME_ALL = "UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = despesas.user_id) WHERE user_id IS NOT NULL"
    
    UPDATE_USER_ID = "UPDATE despesas SET user_id = ? WHERE user_id IS NULL"
    
    DELETE_BY_USER = "DELETE FROM despesas WHERE user_id = ?"


# ========= Categorias Queries ========= #
class CategoriaQueries:
    """Queries relacionadas às tabelas de categorias"""
    
    CREATE_CAT_RECEITA = """CREATE TABLE IF NOT EXISTS cat_receita (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Categoria TEXT,
        user_id INTEGER
    )"""
    
    CREATE_CAT_DESPESA = """CREATE TABLE IF NOT EXISTS cat_despesa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Categoria TEXT,
        user_id INTEGER
    )"""
    
    COUNT_DUPLICATE = "SELECT COUNT(*) FROM {table} WHERE Categoria = ? AND user_id = ?"
    
    INSERT = "INSERT INTO {table} (Categoria, user_id) VALUES (?,?)"
    
    DELETE = "DELETE FROM {table} WHERE Categoria = ? AND user_id = ?"
    
    DELETE_ORPHAN = "DELETE FROM {table} WHERE user_id IS NULL"
    
    UPDATE_USER_ID = "UPDATE {table} SET user_id = ? WHERE user_id IS NULL"
    
    DELETE_BY_USER_RECEITA = "DELETE FROM cat_receita WHERE user_id = ?"
    
    DELETE_BY_USER_DESPESA = "DELETE FROM cat_despesa WHERE user_id = ?"


# ========= Triggers Queries ========= #
class TriggerQueries:
    """Queries para criação de triggers"""
    
    DROP_SET_USERNAME_RECEITAS = "DROP TRIGGER IF EXISTS trg_set_username_on_receitas_insert"
    DROP_SET_USERNAME_DESPESAS = "DROP TRIGGER IF EXISTS trg_set_username_on_despesas_insert"
    DROP_UPDATE_USERNAME_RECEITAS = "DROP TRIGGER IF EXISTS trg_update_username_on_receitas_userid"
    DROP_UPDATE_USERNAME_DESPESAS = "DROP TRIGGER IF EXISTS trg_update_username_on_despesas_userid"
    DROP_UPDATE_USERNAME_USERS = "DROP TRIGGER IF EXISTS trg_update_username_on_users_update"
    DROP_DELETE_USER = "DROP TRIGGER IF EXISTS trg_delete_user_set_username_null"
    
    CREATE_SET_USERNAME_RECEITAS = """
    CREATE TRIGGER IF NOT EXISTS trg_set_username_on_receitas_insert
    AFTER INSERT ON receitas
    BEGIN
        UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """
    
    CREATE_SET_USERNAME_DESPESAS = """
    CREATE TRIGGER IF NOT EXISTS trg_set_username_on_despesas_insert
    AFTER INSERT ON despesas
    BEGIN
        UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """
    
    CREATE_UPDATE_USERNAME_RECEITAS = """
    CREATE TRIGGER IF NOT EXISTS trg_update_username_on_receitas_userid
    AFTER UPDATE OF user_id ON receitas
    BEGIN
        UPDATE receitas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """
    
    CREATE_UPDATE_USERNAME_DESPESAS = """
    CREATE TRIGGER IF NOT EXISTS trg_update_username_on_despesas_userid
    AFTER UPDATE OF user_id ON despesas
    BEGIN
        UPDATE despesas SET username = (SELECT username FROM users WHERE users.id = NEW.user_id) WHERE rowid = NEW.rowid;
    END;
    """
    
    CREATE_UPDATE_USERNAME_USERS = """
    CREATE TRIGGER IF NOT EXISTS trg_update_username_on_users_update
    AFTER UPDATE OF username ON users
    BEGIN
        UPDATE receitas SET username = NEW.username WHERE user_id = NEW.id;
        UPDATE despesas SET username = NEW.username WHERE user_id = NEW.id;
    END;
    """
    
    CREATE_DELETE_USER = """
    CREATE TRIGGER IF NOT EXISTS trg_delete_user_set_username_null
    AFTER DELETE ON users
    BEGIN
        UPDATE receitas SET username = NULL WHERE user_id = OLD.id;
        UPDATE despesas SET username = NULL WHERE user_id = OLD.id;
    END;
    """


# ========= Utility Queries ========= #
class UtilityQueries:
    """Queries utilitárias"""
    
    PRAGMA_TABLE_INFO = "PRAGMA table_info({table})"
    
    PRAGMA_FOREIGN_KEYS_OFF = "PRAGMA foreign_keys=OFF"
    
    PRAGMA_FOREIGN_KEYS_ON = "PRAGMA foreign_keys=ON"
    
    ALTER_TABLE_ADD_COLUMN = "ALTER TABLE {table} ADD COLUMN {column_def}"
    
    COUNT_ORPHAN_RECEITAS = "SELECT COUNT(*) FROM receitas WHERE username IS NULL OR username = ''"
    
    COUNT_ORPHAN_DESPESAS = "SELECT COUNT(*) FROM despesas WHERE username IS NULL OR username = ''"
