import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output, State
from datetime import datetime

from app import app
from db import (
    get_orcamentos, set_orcamento, delete_orcamento,
    get_gastos_por_categoria, table_to_df
)

# =========  Layout  =========== #
layout = dbc.Col([
    dcc.Store(id='store-refresh-orcamentos', data=0),
    
    dbc.Row([
        dbc.Col([
            html.H3("Gerenciar Orçamentos Mensais", className="mb-3"),
            html.P("Defina limites de gastos por categoria para controlar melhor suas finanças."),
        ])
    ]),
    
    # Seletor de Mês/Ano
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Mês"),
                            dbc.Select(
                                id="select-mes-orcamento",
                                options=[
                                    {"label": "Janeiro", "value": 1},
                                    {"label": "Fevereiro", "value": 2},
                                    {"label": "Março", "value": 3},
                                    {"label": "Abril", "value": 4},
                                    {"label": "Maio", "value": 5},
                                    {"label": "Junho", "value": 6},
                                    {"label": "Julho", "value": 7},
                                    {"label": "Agosto", "value": 8},
                                    {"label": "Setembro", "value": 9},
                                    {"label": "Outubro", "value": 10},
                                    {"label": "Novembro", "value": 11},
                                    {"label": "Dezembro", "value": 12},
                                ],
                                value=datetime.now().month
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Ano"),
                            dbc.Input(
                                id="input-ano-orcamento",
                                type="number",
                                value=datetime.now().year,
                                min=2020,
                                max=2030
                            )
                        ], width=6),
                    ])
                ])
            ], className="mb-3")
        ], width=12)
    ]),
    
    # Adicionar Novo Orçamento
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Adicionar/Atualizar Orçamento")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Categoria de Despesa"),
                            dcc.Dropdown(
                                id="select-categoria-orcamento",
                                placeholder="Selecione uma categoria..."
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Valor Limite (R$)"),
                            dbc.Input(
                                id="input-valor-orcamento",
                                type="number",
                                placeholder="Ex: 500.00",
                                step=0.01,
                                min=0
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("\u00a0"),
                            dbc.Button(
                                "Salvar Orçamento",
                                id="btn-salvar-orcamento",
                                color="success",
                                className="w-100"
                            )
                        ], width=2, className="d-flex align-items-end"),
                    ]),
                    html.Div(id="msg-orcamento", className="mt-2")
                ])
            ], className="mb-3")
        ], width=12)
    ]),
    
    # Lista de Orçamentos e Progresso
    dbc.Row([
        dbc.Col([
            html.H4("Orçamentos do Mês Selecionado", className="mb-3"),
            html.Div(id="lista-orcamentos")
        ], width=12)
    ])
], style={"padding": "20px"})


# =========  Callbacks  =========== #

# Carregar categorias de despesa
@app.callback(
    Output("select-categoria-orcamento", "options"),
    Input("store-user", "data")
)
def load_categorias_despesa(user):
    if not user or 'id' not in user:
        return []
    
    df = table_to_df('cat_despesa', user_id=user['id'])
    if df.empty or 'Categoria' not in df.columns:
        return []
    
    return [{"label": cat, "value": cat} for cat in df['Categoria'].tolist()]


# Salvar orçamento
@app.callback(
    [Output("msg-orcamento", "children"),
     Output("store-refresh-orcamentos", "data"),
     Output("input-valor-orcamento", "value"),
     Output("select-categoria-orcamento", "value")],
    Input("btn-salvar-orcamento", "n_clicks"),
    [State("select-categoria-orcamento", "value"),
     State("input-valor-orcamento", "value"),
     State("select-mes-orcamento", "value"),
     State("input-ano-orcamento", "value"),
     State("store-user", "data"),
     State("store-refresh-orcamentos", "data")],
    prevent_initial_call=True
)
def salvar_orcamento(n_clicks, categoria, valor, mes, ano, user, refresh):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not user or 'id' not in user:
        return dbc.Alert("Faça login para salvar orçamentos.", color="danger"), dash.no_update, dash.no_update, dash.no_update
    
    if not categoria or not valor:
        return dbc.Alert("Preencha categoria e valor.", color="warning"), dash.no_update, dash.no_update, dash.no_update
    
    try:
        set_orcamento(categoria, float(valor), int(mes), int(ano), user['id'])
        return (
            dbc.Alert(f"Orçamento de R$ {valor:.2f} definido para {categoria}!", color="success", duration=3000),
            (refresh or 0) + 1,
            None,
            None
        )
    except Exception as e:
        return dbc.Alert(f"Erro ao salvar: {e}", color="danger"), dash.no_update, dash.no_update, dash.no_update


# Mostrar lista de orçamentos com progresso
@app.callback(
    Output("lista-orcamentos", "children"),
    [Input("select-mes-orcamento", "value"),
     Input("input-ano-orcamento", "value"),
     Input("store-user", "data"),
     Input("store-refresh-orcamentos", "data"),
     Input("store-refresh-despesas", "data")]
)
def mostrar_orcamentos(mes, ano, user, refresh_orc, refresh_desp):
    if not user or 'id' not in user or not mes or not ano:
        return dbc.Alert("Selecione mês e ano.", color="info")
    
    user_id = user['id']
    
    # Buscar orçamentos
    orcamentos = get_orcamentos(user_id, mes, ano)
    
    if not orcamentos:
        return dbc.Alert("Nenhum orçamento definido para este período. Adicione orçamentos acima.", color="info")
    
    # Buscar gastos do mês
    gastos = get_gastos_por_categoria(user_id, mes, ano)
    
    # Criar cards de progresso
    cards = []
    for orc in orcamentos:
        categoria = orc['categoria']
        limite = orc['valor_limite']
        gasto = gastos.get(categoria, 0)
        percentual = (gasto / limite * 100) if limite > 0 else 0
        
        # Definir cor baseada no percentual
        if percentual >= 100:
            cor_barra = "danger"
            cor_card = "danger"
        elif percentual >= 80:
            cor_barra = "warning"
            cor_card = "warning"
        else:
            cor_barra = "success"
            cor_card = "success"
        
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5(categoria, className="card-title"),
                    html.P(f"R$ {gasto:.2f} de R$ {limite:.2f}", className="mb-2"),
                    dbc.Progress(
                        value=min(percentual, 100),
                        color=cor_barra,
                        style={"height": "20px"},
                        className="mb-2"
                    ),
                    html.Small(f"{percentual:.1f}% utilizado"),
                    html.Br(),
                    dbc.Button(
                        "Excluir",
                        id={"type": "btn-delete-orc", "index": orc['id']},
                        color="danger",
                        size="sm",
                        outline=True,
                        className="mt-2"
                    )
                ])
            ], color=cor_card, outline=True)
        ], xs=12, sm=6, md=4, lg=3, className="mb-3")
        
        cards.append(card)
    
    return dbc.Row(cards)


# Deletar orçamento
@app.callback(
    Output("store-refresh-orcamentos", "data", allow_duplicate=True),
    Input({"type": "btn-delete-orc", "index": dash.dependencies.ALL}, "n_clicks"),
    [State("store-user", "data"),
     State("store-refresh-orcamentos", "data")],
    prevent_initial_call=True
)
def deletar_orcamento(n_clicks, user, refresh):
    if not any(n_clicks):
        return dash.no_update
    
    if not user or 'id' not in user:
        return dash.no_update
    
    # Identificar qual botão foi clicado
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    triggered_id = ctx.triggered[0]['prop_id']
    import json
    button_id = json.loads(triggered_id.split('.')[0])
    orcamento_id = button_id['index']
    
    try:
        delete_orcamento(orcamento_id, user['id'])
        return (refresh or 0) + 1
    except Exception as e:
        print(f"Erro ao deletar orçamento: {e}")
        return dash.no_update
