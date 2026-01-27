"""
Configurações de Segurança para a Aplicação
Implementa proteções essenciais para deploy em produção
"""

import os
import secrets
from datetime import timedelta
from functools import wraps
from flask import request, jsonify
import time


# ========= Configurações de Ambiente ========= #
class Config:
    """Configurações base"""
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Sessão
    SESSION_TIMEOUT = timedelta(minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', 30)))
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True') == 'True'
    RATE_LIMIT_LOGIN_ATTEMPTS = int(os.getenv('RATE_LIMIT_LOGIN_ATTEMPTS', 5))
    RATE_LIMIT_WINDOW_MINUTES = int(os.getenv('RATE_LIMIT_WINDOW_MINUTES', 15))
    
    # Admin padrão
    DEFAULT_ADMIN_USERNAME = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def is_production(cls):
        return cls.ENVIRONMENT == 'production'


# ========= Rate Limiting ========= #
class RateLimiter:
    """Implementação simples de rate limiting por IP"""
    
    def __init__(self):
        self.attempts = {}  # {ip: [(timestamp, endpoint), ...]}
    
    def is_allowed(self, ip_address, endpoint, max_attempts=5, window_minutes=15):
        """Verifica se o IP pode fazer a requisição"""
        if not Config.RATE_LIMIT_ENABLED:
            return True
        
        current_time = time.time()
        window_seconds = window_minutes * 60
        
        # Limpa tentativas antigas
        if ip_address in self.attempts:
            self.attempts[ip_address] = [
                (ts, ep) for ts, ep in self.attempts[ip_address]
                if current_time - ts < window_seconds and ep == endpoint
            ]
        else:
            self.attempts[ip_address] = []
        
        # Verifica se excedeu o limite
        endpoint_attempts = [
            ts for ts, ep in self.attempts[ip_address]
            if ep == endpoint
        ]
        
        if len(endpoint_attempts) >= max_attempts:
            return False
        
        # Registra nova tentativa
        self.attempts[ip_address].append((current_time, endpoint))
        return True
    
    def reset(self, ip_address, endpoint=None):
        """Reseta contador para um IP (após login bem-sucedido, por exemplo)"""
        if ip_address in self.attempts:
            if endpoint:
                self.attempts[ip_address] = [
                    (ts, ep) for ts, ep in self.attempts[ip_address]
                    if ep != endpoint
                ]
            else:
                del self.attempts[ip_address]


# Instância global do rate limiter
rate_limiter = RateLimiter()


def rate_limit(max_attempts=5, window_minutes=15):
    """
    Decorator para aplicar rate limiting em endpoints
    
    Uso:
        @rate_limit(max_attempts=5, window_minutes=15)
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr
            endpoint = request.endpoint or 'unknown'
            
            if not rate_limiter.is_allowed(ip, endpoint, max_attempts, window_minutes):
                return jsonify({
                    'error': 'Too many requests',
                    'message': f'Limite de {max_attempts} tentativas excedido. Tente novamente em {window_minutes} minutos.'
                }), 429
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ========= Cabeçalhos de Segurança ========= #
def add_security_headers(response):
    """Adiciona cabeçalhos de segurança HTTP às respostas"""
    
    # Previne MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Proteção contra clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # XSS Protection (navegadores antigos)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy
    if Config.is_production():
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
    
    # Força HTTPS em produção
    if Config.is_production():
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Política de Referrer
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissões
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response


# ========= Validação de Senha ========= #
def validate_password_strength(password):
    """
    Valida força da senha
    
    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial (recomendado)
    
    Returns:
        tuple: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if not any(c.isupper() for c in password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not any(c.islower() for c in password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not any(c.isdigit() for c in password):
        return False, "Senha deve conter pelo menos um número"
    
    # Recomendado mas não obrigatório
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return True, "Senha válida (recomenda-se adicionar caractere especial)"
    
    return True, "Senha forte"


# ========= Sanitização de Inputs ========= #
def sanitize_string(value, max_length=None):
    """Remove caracteres potencialmente perigosos de strings"""
    if not isinstance(value, str):
        return value
    
    # Remove tags HTML básicas
    value = value.replace('<', '&lt;').replace('>', '&gt;')
    
    # Remove caracteres de controle
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    # Limita tamanho se especificado
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


def sanitize_sql_string(value):
    """Sanitiza string para uso em queries SQL (complementar a prepared statements)"""
    if not isinstance(value, str):
        return value
    
    # Remove caracteres perigosos
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_', 'EXEC', 'EXECUTE']
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    return value


# ========= Logging Seguro ========= #
def safe_log(message, sensitive_fields=None):
    """
    Log seguro que remove dados sensíveis
    
    Args:
        message: Mensagem ou dict a logar
        sensitive_fields: Lista de campos a mascarar
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'senha', 'token', 'secret', 'key']
    
    if isinstance(message, dict):
        safe_message = message.copy()
        for field in sensitive_fields:
            if field in safe_message:
                safe_message[field] = '***REDACTED***'
        return safe_message
    
    return message


# ========= Verificação de Ambiente ========= #
def check_production_readiness():
    """Verifica se a aplicação está pronta para produção"""
    issues = []
    
    # Verifica SECRET_KEY
    if Config.SECRET_KEY == 'dev':
        issues.append("SECRET_KEY não deve ser 'dev' em produção")
    
    if len(Config.SECRET_KEY) < 32:
        issues.append("SECRET_KEY deve ter pelo menos 32 caracteres")
    
    # Verifica senha admin padrão
    if Config.is_production():
        if Config.DEFAULT_ADMIN_PASSWORD in ['admin', 'admin123', 'password']:
            issues.append("Altere DEFAULT_ADMIN_PASSWORD antes de ir para produção")
    
    # Verifica HTTPS
    if Config.is_production() and not Config.SESSION_COOKIE_SECURE:
        issues.append("SESSION_COOKIE_SECURE deve ser True em produção")
    
    return len(issues) == 0, issues


# ========= Exportar Configurações ========= #
__all__ = [
    'Config',
    'RateLimiter',
    'rate_limiter',
    'rate_limit',
    'add_security_headers',
    'validate_password_strength',
    'sanitize_string',
    'sanitize_sql_string',
    'safe_log',
    'check_production_readiness'
]
