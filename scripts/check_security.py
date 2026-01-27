#!/usr/bin/env python
"""
Script de Verificação de Segurança
Executa checagem de segurança antes do deploy
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from config import Config, ProductionConfig
    from security import check_production_readiness
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)


def check_files():
    """Verifica se arquivos necessários existem"""
    required_files = [
        'requirements.txt',
        '.gitignore',
        'myindex.py',
        'config.py',
        'security.py',
        'db.py',
        'constants.py'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    return missing


def check_env_vars():
    """Verifica variáveis de ambiente críticas"""
    if Config.ENVIRONMENT != 'production':
        return []
    
    critical_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'ADMIN_PASSWORD': os.getenv('ADMIN_PASSWORD'),
    }
    
    missing = []
    weak = []
    
    for var, value in critical_vars.items():
        if not value:
            missing.append(var)
        elif var == 'SECRET_KEY' and len(value) < 32:
            weak.append(f"{var} (muito curta, use pelo menos 32 caracteres)")
        elif var == 'ADMIN_PASSWORD' and value in ['admin', 'admin123', 'password', '123456']:
            weak.append(f"{var} (senha muito fraca)")
    
    return missing, weak


def check_database():
    """Verifica configuração do banco de dados"""
    issues = []
    
    if Config.ENVIRONMENT == 'production':
        if 'sqlite' in Config.DATABASE_URL.lower():
            issues.append("SQLite não é recomendado para produção - use PostgreSQL")
        
        if not Config.DATABASE_URL.startswith(('postgresql://', 'postgres://')):
            issues.append("DATABASE_URL deve apontar para PostgreSQL em produção")
    
    return issues


def check_gitignore():
    """Verifica se .gitignore está protegendo arquivos sensíveis"""
    gitignore_path = Path('.gitignore')
    
    if not gitignore_path.exists():
        return ["Arquivo .gitignore não encontrado"]
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    required_patterns = ['.env', '*.db', '*.log', '__pycache__']
    missing = []
    
    for pattern in required_patterns:
        if pattern not in content:
            missing.append(pattern)
    
    if missing:
        return [f"Padrões faltando no .gitignore: {', '.join(missing)}"]
    
    return []


def check_dependencies():
    """Verifica se dependências críticas estão instaladas"""
    try:
        import dash
        import pandas
        import werkzeug
        import dotenv
    except ImportError as e:
        return [f"Dependência faltando: {e.name}"]
    
    return []


def run_security_check():
    """Executa todas as verificações de segurança"""
    print("🔍 Executando Verificação de Segurança...")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Verificar arquivos
    print("\n📁 Verificando arquivos necessários...")
    missing_files = check_files()
    if missing_files:
        print(f"❌ Arquivos faltando: {', '.join(missing_files)}")
        all_passed = False
    else:
        print("✅ Todos os arquivos necessários presentes")
    
    # 2. Verificar variáveis de ambiente
    print("\n🔐 Verificando variáveis de ambiente...")
    if Config.ENVIRONMENT == 'production':
        missing_vars, weak_vars = check_env_vars()
        if missing_vars:
            print(f"❌ Variáveis faltando: {', '.join(missing_vars)}")
            all_passed = False
        if weak_vars:
            print(f"⚠️  Variáveis fracas: {', '.join(weak_vars)}")
            all_passed = False
        if not missing_vars and not weak_vars:
            print("✅ Variáveis de ambiente configuradas")
    else:
        print(f"ℹ️  Ambiente: {Config.ENVIRONMENT} (pular verificação de produção)")
    
    # 3. Verificar banco de dados
    print("\n💾 Verificando configuração do banco...")
    db_issues = check_database()
    if db_issues:
        for issue in db_issues:
            print(f"⚠️  {issue}")
        if Config.ENVIRONMENT == 'production':
            all_passed = False
    else:
        print("✅ Configuração do banco OK")
    
    # 4. Verificar .gitignore
    print("\n🚫 Verificando .gitignore...")
    gitignore_issues = check_gitignore()
    if gitignore_issues:
        for issue in gitignore_issues:
            print(f"⚠️  {issue}")
    else:
        print("✅ .gitignore protegendo arquivos sensíveis")
    
    # 5. Verificar dependências
    print("\n📦 Verificando dependências...")
    dep_issues = check_dependencies()
    if dep_issues:
        for issue in dep_issues:
            print(f"❌ {issue}")
        all_passed = False
    else:
        print("✅ Dependências instaladas")
    
    # 6. Verificar segurança da aplicação
    print("\n🛡️  Verificando configurações de segurança...")
    is_ready, issues = check_production_readiness()
    if not is_ready:
        for issue in issues:
            print(f"⚠️  {issue}")
        if Config.ENVIRONMENT == 'production':
            all_passed = False
    else:
        print("✅ Configurações de segurança OK")
    
    # Resumo
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODAS AS VERIFICAÇÕES PASSARAM!")
        print("   A aplicação está pronta para deploy.")
        return 0
    else:
        print("❌ ALGUMAS VERIFICAÇÕES FALHARAM!")
        print("   Corrija os problemas antes de fazer deploy.")
        return 1


if __name__ == '__main__':
    exit_code = run_security_check()
    sys.exit(exit_code)
