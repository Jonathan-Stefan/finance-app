import dash
import dash_bootstrap_components as dbc
from flask import jsonify, request
from urllib import request as urllib_request
import re
import time
from html import unescape

# Importar configurações de segurança
from config import Config
from security import add_security_headers, check_production_readiness

estilos = ["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css", "https://fonts.googleapis.com/icon?family=Material+Icons", dbc.themes.COSMO]
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"


app = dash.Dash(__name__, external_stylesheets=estilos + [dbc_css],
                meta_tags=[
                    {"name": "viewport", "content": "width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes"}
                ])

app.config['suppress_callback_exceptions'] = True
app.scripts.config.serve_locally = True
server = app.server

# Cache simples em memória para cotações (TTL em segundos)
QUOTE_CACHE_TTL_SECONDS = 60
_quote_cache = {}

# Configurar secret key do Flask
server.secret_key = Config.SECRET_KEY

# Adicionar cabeçalhos de segurança em todas as respostas
@server.after_request
def apply_security_headers(response):
    return add_security_headers(response)


@server.route('/api/investimentos/cotacao', methods=['GET'])
def api_cotacao_investimento():
    """Endpoint para buscar cotação de ativos usando Status Invest."""
    ticker = (request.args.get('ticker') or '').strip().upper()
    if not ticker:
        return jsonify({'error': 'Parâmetro ticker é obrigatório'}), 400

    # Cache por ticker (60s)
    now_ts = time.time()
    cached = _quote_cache.get(ticker)
    if cached and (now_ts - cached.get('ts', 0) <= QUOTE_CACHE_TTL_SECONDS):
        return jsonify(cached['payload'])

    ticker_lower = ticker.lower()

    # Tenta páginas mais comuns no Status Invest
    candidate_urls = [
        f"https://statusinvest.com.br/fundos-imobiliarios/{ticker_lower}",
        f"https://statusinvest.com.br/acoes/{ticker_lower}",
        f"https://statusinvest.com.br/fiagros/{ticker_lower}",
        f"https://statusinvest.com.br/fundos-de-investimento/{ticker_lower}",
        f"https://statusinvest.com.br/bdrs/{ticker_lower}",
        f"https://statusinvest.com.br/criptomoedas/{ticker_lower}",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def _fetch_html(url):
        req = urllib_request.Request(url, headers=headers)
        with urllib_request.urlopen(req, timeout=12) as response:
            return response.read().decode('utf-8', errors='ignore')

    def _is_not_found_page(html_content):
        text = html_content.lower()
        return (
            "ops. . ." in text
            and "nã" in text
            and "encontramos o que voc" in text
        )

    def _to_float_br(value):
        raw = (value or "").strip()
        if not raw:
            return None
        raw = raw.replace("R$", "").replace(" ", "")
        # Formato BR: 1.234,56 -> 1234.56
        raw = raw.replace(".", "").replace(",", ".")
        try:
            return float(raw)
        except Exception:
            return None

    def _extract_price(html_content):
        decoded = unescape(html_content)

        patterns = [
            r'"price"\s*:\s*"?([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+[\.,][0-9]+)"?',
            r'"lastPrice"\s*:\s*"?([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+[\.,][0-9]+)"?',
            r'cot[aã]?[cç][aã]o[^\d]{0,80}R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+[\.,][0-9]+)',
            r'class="value"[^>]*>\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+[\.,][0-9]+)\s*<',
            r'R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, decoded, flags=re.IGNORECASE | re.DOTALL)
            if match:
                price = _to_float_br(match.group(1))
                if price is not None:
                    return price

        return None

    try:
        resolved_url = None
        html_content = None

        for url in candidate_urls:
            try:
                html_try = _fetch_html(url)
            except Exception:
                continue

            if _is_not_found_page(html_try):
                continue

            # Garante que a página realmente se refere ao ticker consultado
            if ticker in html_try.upper() or f"data-code=\"{ticker}\"" in html_try.upper():
                resolved_url = url
                html_content = html_try
                break

        if not html_content:
            return jsonify({'error': 'Ticker não encontrado no Status Invest', 'ticker': ticker}), 404

        price = _extract_price(html_content)
        if price is None:
            return jsonify({'error': 'Não foi possível extrair cotação no Status Invest', 'ticker': ticker}), 502

        payload = {
            'ticker': ticker,
            'price': price,
            'currency': 'BRL',
            'source': 'status-invest',
            'url': resolved_url
        }

        _quote_cache[ticker] = {
            'ts': now_ts,
            'payload': payload
        }

        return jsonify(payload)
    except Exception as error:
        return jsonify({'error': f'Falha ao consultar cotação no Status Invest: {error}', 'ticker': ticker}), 502

# Verificar prontidão para produção
if Config.ENVIRONMENT == 'production':
    is_ready, issues = check_production_readiness()
    if not is_ready:
        print("⚠️  AVISOS DE SEGURANÇA:")
        for issue in issues:
            print(f"  - {issue}")