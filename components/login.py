import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash import no_update


from app import app
from db import verify_user, create_user

layout = html.Div([
    dbc.Card([
        dbc.CardHeader(html.H3("Login")),
        dbc.CardBody([
            dbc.Label("Usuário"),
            dbc.Input(id='login-username', type='text'),

            dbc.Label("Senha", style={'margin-top': '10px'}),
            html.Div([
                dbc.Input(
                    id='login-password',
                    type='password',
                    style={'paddingRight': '40px'}
                ),
                html.I(
                    id='toggle-login-password-icon',
                    className="fas fa-eye",
                    n_clicks=0,
                    style={
                        'position': 'absolute',
                        'right': '12px',
                        'top': '50%',
                        'transform': 'translateY(-50%)',
                        'cursor': 'pointer',
                        'fontSize': '16px',
                        'color': '#6c757d',
                        'zIndex': 10
                    }
                )
            ], style={'position': 'relative'}),

            html.Div(id='login-message', style={'margin-top': '10px'}),

            dbc.Button('Entrar', id='login-button', color='primary', style={'margin-top': '10px', 'width': '100%'}),

            html.Hr(),

            html.Div([
                html.P("Ainda não tem conta?", style={'marginBottom': '10px', 'textAlign': 'center'}),
                dbc.Button('Fazer Cadastro', id='open-register-modal', color='link', style={'width': '100%'})
            ])
        ])
    ], style={'maxWidth': 500, 'margin': '40px auto'}),

    # Modal de Registro
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Criar Nova Conta")),
        dbc.ModalBody([
            dbc.Label("Usuário"),
            dbc.Input(id='register-username', type='text', placeholder='Escolha um nome de usuário'),

            dbc.Label("Senha", style={'margin-top': '10px'}),
            html.Div([
                dbc.Input(
                    id='register-password',
                    type='password',
                    placeholder='Escolha uma senha',
                    style={'paddingRight': '40px'}
                ),
                html.I(
                    id='toggle-register-password-icon',
                    className="fas fa-eye",
                    n_clicks=0,
                    style={
                        'position': 'absolute',
                        'right': '12px',
                        'top': '50%',
                        'transform': 'translateY(-50%)',
                        'cursor': 'pointer',
                        'fontSize': '16px',
                        'color': '#6c757d',
                        'zIndex': 10
                    }
                )
            ], style={'position': 'relative'}),

            html.Div(id='register-message', style={'margin-top': '10px'})
        ]),
        dbc.ModalFooter([
            dbc.Button('Cancelar', id='close-register-modal', color='secondary', outline=True),
            dbc.Button('Criar Conta', id='register-button', color='primary')
        ])
    ], id='register-modal', is_open=False, centered=True),

    # Toast de sucesso
    dbc.Toast(
        "Cadastro realizado com sucesso! Faça login para continuar.",
        id="success-toast",
        header="Sucesso",
        is_open=False,
        dismissable=True,
        icon="success",
        duration=4000,
        style={
            "position": "fixed",
            "top": "50%",
            "left": "50%",
            "transform": "translate(-50%, -50%)",
            "width": 400,
            "zIndex": 9999
        }
    )
])

@app.callback(
    Output('store-user', 'data'),
    Output('login-message', 'children'),
    Output('url', 'pathname', allow_duplicate=True),
    Input('login-button', 'n_clicks'),
    State('login-username', 'value'),
    State('login-password', 'value'),
    prevent_initial_call=True
)
def auth_control(n_login, username, password):
    if not n_login:
        raise PreventUpdate
        
    if not username or not password:
        return no_update, 'Usuário e senha são obrigatórios.', no_update

    user = verify_user(username, password)
    if not user:
        return no_update, 'Usuário ou senha inválidos.', no_update

    return user, f'Bem-vindo, {user["username"]}!', '/dashboards'

@app.callback(
    Output('register-message', 'children'),
    Output('success-toast', 'is_open'),
    Output('register-username', 'value'),
    Output('register-password', 'value'),
    Output('register-modal', 'is_open', allow_duplicate=True),
    Input('register-button', 'n_clicks'),
    State('register-username', 'value'),
    State('register-password', 'value'),
    prevent_initial_call=True
)
def do_register(n, username, password):
    if not username or not password:
        return 'Usuário e senha são obrigatórios.', False, no_update, no_update, True

    try:
        uid = create_user(username, password)
        if uid:
            return '', True, '', '', False  # Limpa campos, mostra toast e fecha modal
        return 'Erro ao criar usuário.', False, no_update, no_update, True
    except Exception as e:
        return f'Erro: {e}', False, no_update, no_update, True

@app.callback(
    Output('login-password', 'type'),
    Output('toggle-login-password-icon', 'className'),
    Input('toggle-login-password-icon', 'n_clicks'),
    prevent_initial_call=False
)
def toggle_login_password_visibility(n_clicks):
    if n_clicks % 2 == 0:
        return 'password', 'fas fa-eye'
    else:
        return 'text', 'fas fa-eye-slash'

@app.callback(
    Output('register-password', 'type'),
    Output('toggle-register-password-icon', 'className'),
    Input('toggle-register-password-icon', 'n_clicks'),
    prevent_initial_call=False
)
def toggle_register_password_visibility(n_clicks):
    if n_clicks % 2 == 0:
        return 'password', 'fas fa-eye'
    else:
        return 'text', 'fas fa-eye-slash'

@app.callback(
    Output('register-modal', 'is_open'),
    Input('open-register-modal', 'n_clicks'),
    Input('close-register-modal', 'n_clicks'),
    State('register-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_register_modal(open_clicks, close_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'open-register-modal':
        return True
    elif button_id == 'close-register-modal':
        return False
    
    return is_open
