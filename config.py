"""
Configuração da Aplicação por Ambiente
Usa variáveis de ambiente para configurações sensíveis
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Caminho base da aplicação
BASE_DIR = Path(__file__).resolve().parent


class BaseConfig:
    """Configurações base compartilhadas por todos os ambientes"""
    
    # Aplicação
    APP_NAME = "Finance App"
    VERSION = "1.0.0"
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Secret Key (IMPORTANTE: usar variável de ambiente em produção)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Debug
    DEBUG = False
    TESTING = False
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/finance.db')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Sessão
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True') == 'True'
    RATE_LIMIT_LOGIN_ATTEMPTS = int(os.getenv('RATE_LIMIT_LOGIN_ATTEMPTS', 5))
    RATE_LIMIT_WINDOW_MINUTES = int(os.getenv('RATE_LIMIT_WINDOW_MINUTES', 15))


class DevelopmentConfig(BaseConfig):
    """Configurações para ambiente de desenvolvimento"""
    
    DEBUG = True
    
    # Cookie seguro desabilitado para HTTP local
    SESSION_COOKIE_SECURE = False
    
    # Permite hot reload
    HOT_RELOAD = True
    
    # Log mais detalhado
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(BaseConfig):
    """Configurações para ambiente de produção"""
    
    DEBUG = False
    
    # Segurança reforçada
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # HTTPS obrigatório
    FORCE_HTTPS = True
    
    # Database PostgreSQL (Render)
    DATABASE_URL = os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    
    # Logs menos verbosos
    LOG_LEVEL = 'WARNING'
    
    # Admin configurável
    DEFAULT_ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    
    # Validações
    @classmethod
    def validate(cls):
        """Valida configurações obrigatórias para produção"""
        errors = []
        
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY deve ser definida via variável de ambiente")
        
        if not cls.DEFAULT_ADMIN_PASSWORD:
            errors.append("ADMIN_PASSWORD deve ser definida via variável de ambiente")
        
        if cls.DEFAULT_ADMIN_PASSWORD in ['admin', 'admin123', 'password']:
            errors.append("ADMIN_PASSWORD é muito fraca")
        
        if 'sqlite' in cls.DATABASE_URL.lower():
            errors.append("Use PostgreSQL em produção, não SQLite")
        
        return errors


class TestingConfig(BaseConfig):
    """Configurações para testes"""
    
    TESTING = True
    DEBUG = True
    
    # Database em memória para testes
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Desabilita rate limiting em testes
    RATE_LIMIT_ENABLED = False


# Dicionário de configurações
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retorna a configuração baseada na variável de ambiente ENVIRONMENT"""
    env = os.getenv('ENVIRONMENT', 'development')
    return config_by_name.get(env, config_by_name['default'])


# Configuração ativa
Config = get_config()


# Validação de produção
if Config == ProductionConfig:
    validation_errors = ProductionConfig.validate()
    if validation_errors:
        print("⚠️  ERROS DE CONFIGURAÇÃO PARA PRODUÇÃO:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\nConfigure as variáveis de ambiente antes de fazer deploy!")
