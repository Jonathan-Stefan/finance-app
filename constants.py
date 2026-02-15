"""
Constantes do projeto Finance App
Centraliza todos os valores fixos e magic numbers usados na aplicação
"""

from enum import Enum


# ========= Enums ========= #
class StatusDespesa(str, Enum):
    """Status possíveis para uma despesa"""
    PAGO = "Pago"
    A_VENCER = "A vencer"
    VENCIDO = "Vencido"


class TipoTransacao(str, Enum):
    """Tipos de transação"""
    RECEITA = "receitas"
    DESPESA = "despesas"


class FormaPagamento(str, Enum):
    """Formas de pagamento possíveis para despesas"""
    DINHEIRO = "dinheiro"
    CARTAO = "cartao"


# ========= Status e Estados ========= #
# Valores booleanos
SIM = 1
NAO = 0

# Status strings para receitas (Efetuado)
EFETUADO_SIM = "Sim"
EFETUADO_NAO = "Não"

# Fixo
FIXO_SIM = "Sim"
FIXO_NAO = "Não"


# ========= Cores Bootstrap ========= #
COLOR_SUCCESS = "success"
COLOR_DANGER = "danger"
COLOR_WARNING = "warning"
COLOR_INFO = "info"
COLOR_PRIMARY = "primary"
COLOR_SECONDARY = "secondary"


# ========= Caminhos e Assets ========= #
DEFAULT_AVATAR = "/assets/img_hom.png"


# ========= Configurações de Tabela ========= #
TABLE_PAGE_SIZE = 10
TABLE_MIN_YEAR = 2020
TABLE_MAX_YEAR = 2030


# ========= Mensagens ========= #
MSG_USUARIO_NAO_AUTENTICADO = "Usuário não autenticado"
MSG_SEM_DADOS = "Sem dados para salvar"
MSG_NENHUMA_ALTERACAO = "Nenhuma alteração detectada"
MSG_ALTERACOES_SALVAS = "Alterações salvas com sucesso"


# ========= Rotas ========= #
ROUTE_LOGIN = "/login"
ROUTE_DASHBOARD = "/dashboards"
ROUTE_EXTRATOS = "/extratos"
ROUTE_ADMIN = "/admin"
ROUTE_ROOT = "/"


# ========= Database ========= #
DB_NAME = "finance.db"

# Tabelas
TABLE_USERS = "users"
TABLE_RECEITAS = "receitas"
TABLE_DESPESAS = "despesas"
TABLE_CAT_RECEITA = "cat_receita"
TABLE_CAT_DESPESA = "cat_despesa"

# Colunas permitidas para update
ALLOWED_FIELDS_TRANSACAO = {"Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "Status"}


# ========= Configurações de Gráficos ========= #
GRAPH_MARGIN = dict(l=25, r=25, t=25, b=0)


# ========= Validação ========= #
# Palavras que significam "sim" em validação
YES_WORDS = ("sim", "s", "true", "yes", "1", 1, True)

# Palavras que significam "não" em validação
NO_WORDS = ("não", "nao", "n", "false", "no", "0", 0, False)

# Valores considerados vazios
EMPTY_VALUES = (None, "", "-")


# ========= Investimentos ========= #
class TipoInvestimento(str, Enum):
    """Tipos de investimentos disponíveis"""
    POUPANCA = "Poupança"
    CDB = "CDB"
    LCI = "LCI"
    LCA = "LCA"
    TESOURO_SELIC = "Tesouro Selic"
    TESOURO_IPCA = "Tesouro IPCA+"
    TESOURO_PREFIXADO = "Tesouro Prefixado"
    FUNDOS = "Fundos de Investimento"
    ACOES = "Ações"
    CRIPTOMOEDAS = "Criptomoedas"
    OUTRO = "Outro"

class TipoRendimento(str, Enum):
    """Tipos de rendimento disponíveis"""
    SEM_RENDIMENTO = "Sem rendimento"
    CDI = "% do CDI"
    TAXA_FIXA = "Taxa fixa (% a.a.)"
    IPCA_PLUS = "IPCA + (% a.a.)"
    SELIC = "100% da Selic"
    POUPANCA_RENDIMENTO = "Poupança (0.5% a.m.)"

# Taxa CDI atual (atualizar periodicamente)
TAXA_CDI_ANUAL = 10.65  # % ao ano (exemplo: 10.65% a.a.)
TAXA_SELIC_ANUAL = 10.75  # % ao ano
TAXA_IPCA_ANUAL = 4.50  # % ao ano

# Tabela de IOF Regressivo (aplicável a investimentos com resgate antes de 30 dias)
# Formato: (dias_corridos, alíquota_percentual)
TABELA_IOF = {
    1: 96.0,
    2: 93.0,
    3: 90.0,
    4: 86.0,
    5: 83.0,
    6: 80.0,
    7: 76.0,
    8: 73.0,
    9: 70.0,
    10: 66.0,
    11: 63.0,
    12: 60.0,
    13: 56.0,
    14: 53.0,
    15: 50.0,
    16: 46.0,
    17: 43.0,
    18: 40.0,
    19: 36.0,
    20: 33.0,
    21: 30.0,
    22: 26.0,
    23: 23.0,
    24: 20.0,
    25: 16.0,
    26: 13.0,
    27: 10.0,
    28: 6.0,
    29: 3.0,
    30: 0.0
}
