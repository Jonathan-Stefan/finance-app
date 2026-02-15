from dash import html, dcc
import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# import from folders
from app import *
from components import sidebar, dashboards, extratos, login, admin, planos, orcamentos
from globals import *

# DataFrames and Dcc.Store (loaded from SQLite)
from db import table_to_df

df_receitas = table_to_df('receitas')
df_receitas_aux = df_receitas.to_dict()

df_despesas = table_to_df('despesas')
df_despesas_aux = df_despesas.to_dict()

list_receitas = table_to_df('cat_receita')
list_receitas_aux = list_receitas.to_dict()

list_despesas = table_to_df('cat_despesa')
list_despesas_aux = list_despesas.to_dict()


# =========  Layout  =========== #
content = html.Div(id="page-content")

# Serve layout como função para garantir que os `dcc.Store` sejam carregados do DB a cada carregamento de página
def serve_layout():
    # Inicializa stores vazios: os dados serão carregados quando o usuário fizer login
    return dbc.Container(children=[
        dcc.Location(id="url"),
        dcc.Store(id="store-user", storage_type='session'), 
        dcc.Store(id='store-receitas', data={}),
        dcc.Store(id="store-despesas", data={}),
        dcc.Store(id='stored-cat-receitas', data={}),
        dcc.Store(id='stored-cat-despesas', data={}),
        # stores para sinalizar reloads
        dcc.Store(id='store-refresh-receitas', data=0),
        dcc.Store(id='store-refresh-despesas', data=0),
        dcc.Store(id='store-refresh-cat-receitas', data=0),
        dcc.Store(id='store-refresh-cat-despesas', data=0),
        
        dbc.Row([
            dbc.Col([
                sidebar.layout
            ], xs=12, sm=12, md=3, lg=2, id="sidebar-col"),

            dbc.Col([
                content
            ], xs=12, sm=12, md=9, lg=10),
        ], className="g-0")

    ], fluid=True, style={"padding": "0px"}, className="dbc")

app.layout = serve_layout


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("store-user", "data")
)
def render_page_content(pathname, user):

    # Se está na página de login, sempre renderiza login
    if pathname in ("/", "/login"):
        return login.layout
    
    # Para outras páginas, verifica autenticação
    if not user:
        return login.layout  # bloqueia acesso sem login

    if pathname == "/dashboards":
        return dashboards.layout

    if pathname == "/extratos":
        return extratos.layout
    
    if pathname == "/planos":
        return planos.layout
    
    if pathname == "/orcamentos":
        return orcamentos.layout
    
    if pathname == "/admin":
        # Verifica se o usuário é admin
        if not user.get('is_admin'):
            return html.Div([
                dbc.Alert(
                    [
                        html.H4("⛔ Acesso Negado", className="alert-heading"),
                        html.P("Você não tem permissão para acessar esta página."),
                        html.Hr(),
                        html.P("Apenas administradores podem acessar o painel de administração.", className="mb-0")
                    ],
                    color="danger",
                    style={"margin": "50px auto", "max-width": "600px"}
                )
            ])
        return admin.layout

    return html.Div([
        html.H3("404 - Página não encontrada"),
        html.P(f"Rota inválida: {pathname}")
    ])

        

# Callback responsável por recarregar os stores do usuário autenticado
@app.callback(
    [Output('store-receitas', 'data'), Output('store-despesas', 'data'), Output('stored-cat-receitas', 'data'), Output('stored-cat-despesas', 'data')],
    [Input('store-user', 'data'), Input('store-refresh-receitas', 'data'), Input('store-refresh-despesas', 'data'), Input('store-refresh-cat-receitas', 'data'), Input('store-refresh-cat-despesas', 'data')]
)
def reload_user_stores(user, r_rec, r_des, r_cat_rec, r_cat_des):
    user_id = user['id'] if user and 'id' in user else None
    from db import table_to_df, update_status_vencidos
    
    print(f"[RELOAD_STORES] user_id={user_id}, r_rec={r_rec}, r_des={r_des}, r_cat_rec={r_cat_rec}, r_cat_des={r_cat_des}")

    if user_id is None:
        return {}, {}, {}, {}

    # Atualiza status vencidos automaticamente antes de carregar dados
    update_status_vencidos(user_id)

    df_receitas = table_to_df('receitas', user_id=user_id, include_id=True).to_dict('records')
    df_despesas = table_to_df('despesas', user_id=user_id, include_id=True).to_dict('records')
    list_receitas = table_to_df('cat_receita', user_id=user_id).to_dict('records')
    list_despesas = table_to_df('cat_despesa', user_id=user_id).to_dict('records')
    
    print(f"[RELOAD_STORES] Carregadas {len(list_despesas)} categorias de despesa e {len(list_receitas)} categorias de receita")

    return df_receitas, df_despesas, list_receitas, list_despesas

if __name__ == '__main__':
    app.run(debug=True)

'''if __name__ == '__main__':
    import os
    # Detecta se está em produção
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('PORT', 8050))
    host = os.getenv('HOST', '0.0.0.0')
    
    app.run(debug=debug_mode, host=host, port=port)'''