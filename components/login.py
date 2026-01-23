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
            dbc.Input(id='login-password', type='password'),

            html.Div(id='login-message', style={'margin-top': '10px'}),

            dbc.Button('Entrar', id='login-button', color='primary', style={'margin-top': '10px'}),

            html.Hr(),

            html.P("Ainda não tem conta?"),
            dbc.Input(id='register-username', type='text', placeholder='Novo usuário'),
            dbc.Input(
                id='register-password',
                type='password',
                placeholder='Nova senha',
                style={'margin-top': '5px'}
            ),
            dbc.Button('Registrar', id='register-button', color='secondary', style={'margin-top': '10px'}),

            html.Div(id='register-message', style={'margin-top': '10px'})
        ])
    ], style={'maxWidth': 500, 'margin': '40px auto'})
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
    Input('register-button', 'n_clicks'),
    State('register-username', 'value'),
    State('register-password', 'value'),
    prevent_initial_call=True
)
def do_register(n, username, password):
    if not username or not password:
        return 'Usuário e senha são obrigatórios.'

    try:
        uid = create_user(username, password)
        if uid:
            return f'Usuário {username} criado com sucesso. Faça login.'
        return 'Erro ao criar usuário.'
    except Exception as e:
        return f'Erro: {e}'



