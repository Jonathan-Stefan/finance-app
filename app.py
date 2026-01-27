import dash
import dash_bootstrap_components as dbc

# Importar configurações de segurança
from config import Config
from security import add_security_headers, check_production_readiness

estilos = ["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css", "https://fonts.googleapis.com/icon?family=Material+Icons", dbc.themes.COSMO]
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"


app = dash.Dash(__name__, external_stylesheets=estilos + [dbc_css],
                meta_tags=[
                    {"name": "viewport", "content": "width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes"}
                ])

app.config['suppress_callback_exceptions'] = True
app.scripts.config.serve_locally = True
server = app.server

# Configurar secret key do Flask
server.secret_key = Config.SECRET_KEY

# Adicionar cabeçalhos de segurança em todas as respostas
@server.after_request
def apply_security_headers(response):
    return add_security_headers(response)

# Verificar prontidão para produção
if Config.ENVIRONMENT == 'production':
    is_ready, issues = check_production_readiness()
    if not is_ready:
        print("⚠️  AVISOS DE SEGURANÇA:")
        for issue in issues:
            print(f"  - {issue}")