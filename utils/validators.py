"""
Funções de validação e normalização de dados
Centraliza lógica de conversão e validação usada em múltiplos componentes
"""

import pandas as pd
from constants import YES_WORDS, NO_WORDS, EMPTY_VALUES


def yesno_to_int(value):
    """
    Converte valores Sim/Não para 1/0
    
    Args:
        value: Valor a ser convertido (string, int, bool)
        
    Returns:
        1 para valores afirmativos, 0 para negativos, None para inválidos
    """
    if value in YES_WORDS:
        return 1
    if value in NO_WORDS:
        return 0
    if isinstance(value, str):
        v = value.strip().lower()
        if v in YES_WORDS:
            return 1
        if v in NO_WORDS:
            return 0
    return None


def parse_float_value(value):
    """
    Parse seguro de valores float, aceitando vírgula como separador decimal
    
    Args:
        value: Valor a ser convertido
        
    Returns:
        Float convertido ou None se inválido
    """
    if value in EMPTY_VALUES:
        return None
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        return None


def normalize_date(value):
    """
    Normaliza datas para formato ISO (YYYY-MM-DD)
    
    Args:
        value: Data em qualquer formato aceito pelo pandas
        
    Returns:
        String no formato ISO ou None se inválido
    """
    if value in EMPTY_VALUES:
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.strftime('%Y-%m-%d')


def is_empty(value):
    """
    Verifica se um valor é considerado vazio
    
    Args:
        value: Valor a verificar
        
    Returns:
        True se vazio, False caso contrário
    """
    return value in EMPTY_VALUES


def normalize_string(value):
    """
    Normaliza string, retornando None para valores vazios
    
    Args:
        value: String a normalizar
        
    Returns:
        String normalizada ou None se vazia
    """
    if is_empty(value):
        return None
    return str(value).strip()


def validate_status(status):
    """
    Valida se um status de despesa é válido
    
    Args:
        status: Status a validar
        
    Returns:
        Status se válido, None caso contrário
    """
    from constants import StatusDespesa
    valid_statuses = [s.value for s in StatusDespesa]
    if status in valid_statuses:
        return status
    return None


def format_currency(value):
    """
    Formata valor como moeda brasileira
    
    Args:
        value: Valor numérico
        
    Returns:
        String formatada como R$ X.XX
    """
    if value is None or pd.isna(value):
        return "R$ 0.00"
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0.00"
