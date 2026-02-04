# Standard library imports
from datetime import datetime

# Third party imports
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash

# Local imports
from app import app
from db import (
    get_planos_by_user, insert_plano, update_plano, delete_plano,
    get_montantes_by_user, insert_montante, update_montante, delete_montante,
    get_anotacoes_planos, save_anotacoes_planos,
    calculate_plano_valor_acumulado, table_to_df,
    calcular_rendimento_investimento, atualizar_valores_investimentos
)
from constants import TipoInvestimento, TipoRendimento, TAXA_CDI_ANUAL

# =========  Layout  =========== #
layout = dbc.Col([
    dbc.Row([
        dbc.Col([
            html.H3("Planos e Metas", className="text-center mb-4", 
                   style={"color": "#2c3e50", "font-weight": "bold"}),
        ])
    ]),
    
    # Principais Planos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(
                    html.Div([
                        html.H5("Principais Planos", className="d-inline", 
                               style={"color": "#2c3e50", "font-weight": "bold"}),
                        dbc.Button("Editar", color="warning", size="sm", 
                                  id="btn-editar-planos", className="float-end")
                    ]),
                    style={"background-color": "#e8f4f8"}
                ),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id="graph-plano-1", config={"displayModeBar": False})
                        ], xs=12, md=4),
                        dbc.Col([
                            dcc.Graph(id="graph-plano-2", config={"displayModeBar": False})
                        ], xs=12, md=4),
                        dbc.Col([
                            dcc.Graph(id="graph-plano-3", config={"displayModeBar": False})
                        ], xs=12, md=4),
                    ])
                ])
            ], className="mb-3")
        ], xs=12, lg=8),
        
        # Grau de Compromisso + Anotações
        dbc.Col([
            # Velocímetro
            dbc.Card([
                dbc.CardHeader(
                    html.H5("Grau de Compromisso (Mês Atual)", 
                           style={"color": "#2c3e50", "font-weight": "bold", "margin": "0"}),
                    style={"background-color": "#e8f4f8"}
                ),
                dbc.CardBody([
                    dcc.Graph(id="graph-velocimetro", config={"displayModeBar": False}),
                    html.Div([
                        html.P([
                            html.Strong("Valor total de despesas: "),
                            html.Span("R$ 0,00", id="valor-total-despesas", 
                                    style={"color": "#3498db"})
                        ], className="mb-2"),
                        html.P([
                            html.Strong("Valor quitado: "),
                            html.Span("R$ 0,00", id="valor-quitado", 
                                    style={"color": "#27ae60"})
                        ], className="mb-2"),
                        html.P([
                            html.Strong("Valor a quitar: "),
                            html.Span("R$ 0,00", id="valor-a-quitar", 
                                    style={"color": "#e74c3c"})
                        ], className="mb-0"),
                    ], className="text-center")
                ])
            ], className="mb-3"),
            
            # Anotações
            dbc.Card([
                dbc.CardHeader(
                    html.H5("Anotações", 
                           style={"color": "#2c3e50", "font-weight": "bold", "margin": "0"}),
                    style={"background-color": "#e8f4f8"}
                ),
                dbc.CardBody([
                    dbc.Textarea(
                        id="textarea-anotacoes",
                        placeholder="Escreva suas anotações aqui...",
                        style={"height": "150px", "resize": "none"}
                    ),
                    dbc.Button("Salvar", color="primary", size="sm", 
                             className="mt-2 w-100", id="btn-salvar-anotacoes")
                ])
            ])
        ], xs=12, lg=4),
    ], className="mb-3"),
    
    # Tabelas
    dbc.Row([
        # Planos do Mês Atual
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(
                    html.Div([
                        html.H5("Planos do Mês Atual", className="d-inline", 
                               style={"color": "#2c3e50", "font-weight": "bold"}),
                        dbc.Button("➕", color="success", size="sm", 
                                  id="btn-add-plano-mes", className="float-end")
                    ]),
                    style={"background-color": "#e8f4f8"}
                ),
                dbc.CardBody([
                    html.Div(id="tabela-planos-mes")
                ])
            ])
        ], xs=12, lg=6),
        
        # Montante Acumulado
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(
                    html.Div([
                        html.H5("Montante Acumulado", className="d-inline", 
                               style={"color": "#2c3e50", "font-weight": "bold"}),
                        dbc.Button("➕", color="success", size="sm", 
                                  id="btn-add-montante", className="float-end")
                    ]),
                    style={"background-color": "#e8f4f8"}
                ),
                dbc.CardBody([
                    html.Div(id="tabela-montante-acumulado")
                ])
            ])
        ], xs=12, lg=6),
    ]),
    
    # Modal para adicionar/editar plano
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Adicionar Plano", id="modal-plano-title")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Nome do Plano:"),
                    dbc.Input(id="input-nome-plano", placeholder="Ex: Financiamento da moto"),
                ], width=12, className="mb-3"),
                dbc.Col([
                    dbc.Label("Valor Total da Meta:"),
                    dbc.Input(id="input-valor-total-plano", type="number", 
                            placeholder="Ex: 10000.00"),
                ], width=12, className="mb-3"),
                dbc.Col([
                    html.P([
                        html.Strong("Valor Acumulado: "),
                        html.Span("R$ 0,00", id="display-valor-acumulado-plano",
                                style={"color": "#27ae60", "font-size": "1.2rem"})
                    ], className="text-center mb-2"),
                    html.Small("O valor acumulado é calculado automaticamente a partir das receitas destinadas a este plano.",
                             className="text-muted d-block text-center")
                ], width=12, className="mb-3"),
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-plano", className="ms-auto", color="secondary"),
            dbc.Button("Salvar", id="btn-salvar-plano", color="primary"),
        ])
    ], id="modal-plano", size="lg", is_open=False, centered=True),
    
    # Modal para adicionar investimento/montante
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Adicionar Investimento", id="modal-montante-title")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Instituição/Nome:"),
                    dbc.Input(id="input-inst-montante", placeholder="Ex: Itaú, Nubank, XP"),
                ], width=12, className="mb-3"),
                
                dbc.Col([
                    dbc.Label("Tipo de Investimento:"),
                    dbc.Select(
                        id="select-tipo-montante",
                        options=[
                            {"label": "Poupança", "value": "Poupança"},
                            {"label": "CDB", "value": "CDB"},
                            {"label": "LCI", "value": "LCI"},
                            {"label": "LCA", "value": "LCA"},
                            {"label": "Tesouro Selic", "value": "Tesouro Selic"},
                            {"label": "Tesouro IPCA+", "value": "Tesouro IPCA+"},
                            {"label": "Tesouro Prefixado", "value": "Tesouro Prefixado"},
                            {"label": "Fundos de Investimento", "value": "Fundos de Investimento"},
                            {"label": "Ações", "value": "Ações"},
                            {"label": "Criptomoedas", "value": "Criptomoedas"},
                            {"label": "Outro", "value": "Outro"},
                        ],
                        value="Poupança"
                    ),
                ], width=6, className="mb-3"),
                
                dbc.Col([
                    dbc.Label("Tipo de Rendimento:"),
                    dbc.Select(
                        id="select-tipo-rendimento",
                        options=[
                            {"label": "Sem rendimento", "value": "Sem rendimento"},
                            {"label": "% do CDI", "value": "% do CDI"},
                            {"label": "Taxa fixa (% a.a.)", "value": "Taxa fixa (% a.a.)"},
                            {"label": "IPCA + (% a.a.)", "value": "IPCA + (% a.a.)"},
                            {"label": "100% da Selic", "value": "100% da Selic"},
                            {"label": "Poupança (0.5% a.m.)", "value": "Poupança (0.5% a.m.)"},
                        ],
                        value="Sem rendimento"
                    ),
                ], width=6, className="mb-3"),
                
                dbc.Col([
                    dbc.Label("Taxa/Percentual:"),
                    dbc.Input(
                        id="input-taxa-rendimento", 
                        type="number", 
                        placeholder="Ex: 100 (para 100% do CDI)",
                        step="0.01"
                    ),
                    dbc.FormText("Para CDI: 100 = 100% do CDI. Para taxa fixa: valor em % a.a.")
                ], width=6, className="mb-3"),
                
                dbc.Col([
                    dbc.Label("Data de Início:"),
                    dcc.DatePickerSingle(
                        id='date-inicio-investimento',
                        date=datetime.today().date(),
                        display_format='DD/MM/YYYY',
                        style={"width": "100%"}
                    ),
                ], width=6, className="mb-3"),
                
                dbc.Col([
                    dbc.Label("Valor Inicial Investido:"),
                    dbc.Input(
                        id="input-valor-inicial-montante", 
                        type="number", 
                        placeholder="Ex: 200.00",
                        step="0.01"
                    ),
                ], width=6, className="mb-3"),
                
                dbc.Col([
                    dbc.Label("Valor Atual:"),
                    dbc.Input(
                        id="input-valor-montante", 
                        type="number", 
                        placeholder="Ex: 205.50",
                        step="0.01"
                    ),
                    dbc.FormText("Será atualizado automaticamente com os rendimentos")
                ], width=6, className="mb-3"),
                
                # Informações de rendimento
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💰 Resumo do Investimento", className="mb-3"),
                            html.Div([
                                html.P([
                                    html.Strong("Rendimento estimado diário: "),
                                    html.Span("R$ 0,00", id="display-rendimento-diario",
                                            style={"color": "#27ae60"})
                                ], className="mb-1"),
                                html.P([
                                    html.Strong("Rendimento estimado mensal: "),
                                    html.Span("R$ 0,00", id="display-rendimento-mensal",
                                            style={"color": "#27ae60"})
                                ], className="mb-1"),
                                html.P([
                                    html.Strong("Rendimento estimado anual: "),
                                    html.Span("R$ 0,00", id="display-rendimento-anual",
                                            style={"color": "#27ae60"})
                                ], className="mb-0"),
                            ])
                        ])
                    ], color="light", className="mb-2")
                ], width=12),
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-montante", className="ms-auto", color="secondary"),
            dbc.Button("Salvar", id="btn-salvar-montante", color="primary"),
        ])
    ], id="modal-montante", size="lg", is_open=False, centered=True),
    
    # Stores para dados e controle
    dcc.Store(id="store-planos-data", data=[]),
    dcc.Store(id="store-montantes-data", data=[]),
    dcc.Store(id="store-anotacoes-data", data=""),
    dcc.Store(id="store-plano-edit-id", data=None),
    dcc.Store(id="store-montante-edit-id", data=None),
    dcc.Store(id="store-refresh-planos", data=0),
    
], style={"padding": "20px"})


# =========  Callbacks  =========== #

# Carregar dados do usuário logado
@app.callback(
    [Output("store-planos-data", "data"),
     Output("store-montantes-data", "data"),
     Output("store-anotacoes-data", "data")],
    [Input("store-user", "data"),
     Input("store-refresh-planos", "data")]
)
def load_user_planos(user, refresh):
    if not user or 'id' not in user:
        return [], [], ""
    
    user_id = user['id']
    
    # Atualizar valores dos investimentos com base nos rendimentos
    atualizar_valores_investimentos(user_id)
    
    planos = get_planos_by_user(user_id)
    montantes = get_montantes_by_user(user_id)
    anotacoes = get_anotacoes_planos(user_id)
    
    # Atualizar valor acumulado de cada plano baseado nas receitas
    for plano in planos:
        plano['valor_acumulado'] = calculate_plano_valor_acumulado(
            plano['id'], user_id
        )
    
    return planos, montantes, anotacoes


# Atualizar valor acumulado quando edita plano (desabilitado temporariamente)
# Este callback será reativado se implementarmos edição de planos
# @app.callback(
#     Output("display-valor-acumulado-plano", "children"),
#     [Input("store-plano-edit-id", "data"),
#      Input("store-user", "data")]
# )
# def update_valor_acumulado_display(plano_id, user):
#     if not plano_id or not user or 'id' not in user:
#         return "R$ 0,00"
#     
#     valor = calculate_plano_valor_acumulado(plano_id, user['id'])
#     return f"R$ {valor:,.2f}"


# Gráficos de Planos (Donut Charts)
@app.callback(
    [Output("graph-plano-1", "figure"),
     Output("graph-plano-2", "figure"),
     Output("graph-plano-3", "figure")],
    Input("store-planos-data", "data")
)
def update_planos_graphs(planos):
    figures = []
    colors = [["#FFA726", "#E0E0E0"], ["#FFA726", "#E0E0E0"], ["#FFA726", "#E0E0E0"]]
    
    for i in range(3):
        if i < len(planos):
            plano = planos[i]
            percentual = (plano["valor_acumulado"] / plano["valor_total"]) * 100 if plano["valor_total"] > 0 else 0
            
            fig = go.Figure(data=[go.Pie(
                values=[percentual, 100-percentual],
                hole=0.7,
                marker=dict(colors=colors[i]),
                textinfo='none',
                hoverinfo='label+percent',
                showlegend=False
            )])
            
            fig.add_annotation(
                text=f"{percentual:.1f}%",
                x=0.5, y=0.5,
                font_size=28,
                showarrow=False,
                font=dict(color="#2c3e50", weight="bold")
            )
            
            fig.update_layout(
                height=250,
                width=None,
                autosize=True,
                margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text=plano["nome"],
                    font=dict(size=14, color="#2c3e50"),
                    x=0.5,
                    xanchor='center'
                )
            )
        else:
            # Gráfico vazio com mensagem "Sem dados"
            fig = go.Figure()
            fig.add_annotation(
                text="Sem dados",
                x=0.5, y=0.5,
                font_size=18,
                showarrow=False,
                font=dict(color="#95a5a6"),
                xref="paper",
                yref="paper"
            )
            fig.update_layout(
                height=250,
                autosize=True,
                margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False)
            )
        
        figures.append(fig)
    
    return figures


# Velocímetro
@app.callback(
    [Output("graph-velocimetro", "figure"),
     Output("valor-total-despesas", "children"),
     Output("valor-quitado", "children"),
     Output("valor-a-quitar", "children")],
    [Input("store-planos-data", "data"),
     Input("store-user", "data")]
)
def update_velocimetro(planos, user):
    # Calcular valores reais com base nas despesas do usuário
    if not user or 'id' not in user:
        total_quitado = 0
        total_a_quitar = 0
        percentual = 0
    else:
        user_id = user['id']
        # Buscar despesas do mês atual
        df_despesas = table_to_df('despesas', user_id=user_id)
        
        if not df_despesas.empty:
            # Filtrar despesas do mês atual
            df_despesas['Data'] = pd.to_datetime(df_despesas['Data'], errors='coerce')
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            df_mes = df_despesas[
                (df_despesas['Data'].dt.month == mes_atual) & 
                (df_despesas['Data'].dt.year == ano_atual)
            ]
            
            # Calcular valores
            despesas_pagas = df_mes[df_mes['Status'] == 'Pago']
            despesas_pendentes = df_mes[df_mes['Status'].isin(['A vencer', 'Vencido'])]
            
            total_quitado = despesas_pagas['Valor'].sum() if len(despesas_pagas) > 0 else 0
            total_a_quitar = despesas_pendentes['Valor'].sum() if len(despesas_pendentes) > 0 else 0
        else:
            total_quitado = 0
            total_a_quitar = 0
    
    total_mes = total_quitado + total_a_quitar
    percentual = (total_quitado / total_mes * 100) if total_mes > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentual,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "", 'font': {'size': 16}},
        number={'suffix': "%", 'font': {'size': 40, 'color': "#2c3e50"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': "#2c3e50", 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': '#e74c3c'},
                {'range': [30, 70], 'color': '#f39c12'},
                {'range': [70, 100], 'color': '#27ae60'}
            ],
            'threshold': {
                'line': {'color': "#2c3e50", 'width': 4},
                'thickness': 0.75,
                'value': percentual
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        autosize=True,
        margin=dict(t=10, b=10, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#2c3e50", 'family': "Arial"}
    )
    
    return fig, f"R$ {total_mes:,.2f}", f"R$ {total_quitado:,.2f}", f"R$ {total_a_quitar:,.2f}"


# Tabela de Planos (metas de juntar dinheiro)
@app.callback(
    Output("tabela-planos-mes", "children"),
    [Input("store-planos-data", "data"),
     Input("store-user", "data")]
)
def update_tabela_planos(planos, user):
    if not planos:
        return html.P("Nenhum plano cadastrado. Clique em ➕ para adicionar.", 
                     className="text-muted text-center")
    
    if not user or 'id' not in user:
        return html.P("Faça login para ver seus planos.", className="text-muted text-center")
    
    rows = []
    
    for plano in planos:
        valor_acumulado = plano.get("valor_acumulado", 0)
        valor_total = plano.get("valor_total", 0)
        percentual = (valor_acumulado / valor_total * 100) if valor_total > 0 else 0
        
        rows.append(html.Tr([
            html.Td(plano["nome"]),
            html.Td(f"R$ {valor_acumulado:,.2f}", className="text-end"),
            html.Td(f"R$ {valor_total:,.2f}", className="text-end"),
            html.Td(f"{percentual:.1f}%", className="text-center"),
            html.Td([
                dbc.Button("🗑️", color="danger", size="sm", 
                          id={"type": "btn-delete-plano", "index": plano['id']})
            ], className="text-center")
        ]))
    
    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Plano/Meta", style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
            html.Th("Valor Acumulado", className="text-end", 
                   style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
            html.Th("Meta Total", className="text-end", 
                   style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
            html.Th("Progresso", className="text-center", 
                   style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
            html.Th("Ações", className="text-center", 
                   style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
        ])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True, striped=True, size="sm")
    
    return table


# Tabela de Montante Acumulado
@app.callback(
    Output("tabela-montante-acumulado", "children"),
    Input("store-montantes-data", "data")
)
def update_tabela_montantes(montantes):
    if not montantes:
        return html.P("Nenhum montante cadastrado. Clique em ➕ para adicionar.", 
                     className="text-muted text-center")
    
    rows = []
    for montante in montantes:
        rows.append(html.Tr([
            html.Td(montante["instituicao"]),
            html.Td(montante["tipo"]),
            html.Td(f"R$ {montante['valor']:,.2f}", className="text-end"),
            html.Td([
                dbc.Button("🗑️", color="danger", size="sm",
                          id={"type": "btn-delete-montante", "index": montante['id']})
            ], className="text-center")
        ]))
    
    # Total
    total = sum([m["valor"] for m in montantes])
    rows.append(html.Tr([
        html.Td(html.Strong("Total Geral"), colSpan=2),
        html.Td(html.Strong(f"R$ {total:,.2f}"), className="text-end"),
        html.Td(""),
    ], style={"background-color": "#f8f9fa"}))
    
    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Nome", style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
            html.Th("Tipo", style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
            html.Th("Valor Acumulado", className="text-end", 
                   style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
            html.Th("Ações", className="text-center",
                   style={"background-color": "#2c3e50", "color": "white", "font-weight": "bold"}),
        ])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True, striped=True, size="sm")
    
    return table


# Salvar Plano
@app.callback(
    Output("store-refresh-planos", "data", allow_duplicate=True),
    Input("btn-salvar-plano", "n_clicks"),
    [State("input-nome-plano", "value"),
     State("input-valor-total-plano", "value"),
     State("store-user", "data"),
     State("store-refresh-planos", "data")],
    prevent_initial_call=True
)
def save_plano(n, nome, valor_total, user, refresh):
    if not n or not nome or not valor_total:
        return dash.no_update
    
    if not user or 'id' not in user:
        return dash.no_update
    
    user_id = user['id']
    # Valor acumulado inicial é sempre 0 para planos novos
    valor_acumulado = 0
    # Categoria não é mais usada, passar None ou string vazia
    categoria = ""
    
    insert_plano(nome, float(valor_total), valor_acumulado, categoria, user_id)
    
    return (refresh or 0) + 1


# Deletar Plano
@app.callback(
    Output("store-refresh-planos", "data", allow_duplicate=True),
    Input({"type": "btn-delete-plano", "index": dash.dependencies.ALL}, "n_clicks"),
    [State("store-user", "data"),
     State("store-refresh-planos", "data")],
    prevent_initial_call=True
)
def delete_plano_callback(n_clicks, user, refresh):
    if not any(n_clicks) or not user or 'id' not in user:
        return dash.no_update
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    plano_id = eval(button_id)["index"]
    
    delete_plano(plano_id, user['id'])
    
    return (refresh or 0) + 1


# Salvar Montante/Investimento
@app.callback(
    Output("store-refresh-planos", "data", allow_duplicate=True),
    Input("btn-salvar-montante", "n_clicks"),
    [State("input-inst-montante", "value"),
     State("select-tipo-montante", "value"),
     State("input-valor-montante", "value"),
     State("select-tipo-rendimento", "value"),
     State("input-taxa-rendimento", "value"),
     State("date-inicio-investimento", "date"),
     State("input-valor-inicial-montante", "value"),
     State("store-user", "data"),
     State("store-refresh-planos", "data")],
    prevent_initial_call=True
)
def save_montante(n, instituicao, tipo, valor, tipo_rendimento, taxa, data_inicio, valor_inicial, user, refresh):
    if not n or not instituicao or not tipo:
        return dash.no_update
    
    if not user or 'id' not in user:
        return dash.no_update
    
    # Valores padrão se não fornecidos
    valor = float(valor) if valor else 0
    valor_inicial = float(valor_inicial) if valor_inicial else valor
    taxa = float(taxa) if taxa else 0
    tipo_rendimento = tipo_rendimento if tipo_rendimento else "Sem rendimento"
    
    insert_montante(
        instituicao, tipo, valor, tipo_rendimento, taxa, 
        data_inicio, valor_inicial, user['id']
    )
    
    return (refresh or 0) + 1


# Deletar Montante
@app.callback(
    Output("store-refresh-planos", "data", allow_duplicate=True),
    Input({"type": "btn-delete-montante", "index": dash.dependencies.ALL}, "n_clicks"),
    [State("store-user", "data"),
     State("store-refresh-planos", "data")],
    prevent_initial_call=True
)
def delete_montante_callback(n_clicks, user, refresh):
    if not any(n_clicks) or not user or 'id' not in user:
        return dash.no_update
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    montante_id = eval(button_id)["index"]
    
    delete_montante(montante_id, user['id'])
    
    return (refresh or 0) + 1


# Salvar Anotações
@app.callback(
    Output("store-anotacoes-data", "data", allow_duplicate=True),
    Input("btn-salvar-anotacoes", "n_clicks"),
    [State("textarea-anotacoes", "value"),
     State("store-user", "data")],
    prevent_initial_call=True
)
def save_anotacoes(n, conteudo, user):
    if not n or not user or 'id' not in user:
        return dash.no_update
    
    save_anotacoes_planos(user['id'], conteudo or "")
    
    return conteudo or ""


# Carregar anotações no textarea
@app.callback(
    Output("textarea-anotacoes", "value"),
    Input("store-anotacoes-data", "data")
)
def load_anotacoes(anotacoes):
    return anotacoes or ""


# Modals
@app.callback(
    Output("modal-plano", "is_open"),
    [Input("btn-editar-planos", "n_clicks"),
     Input("btn-add-plano-mes", "n_clicks"),
     Input("btn-cancelar-plano", "n_clicks"),
     Input("btn-salvar-plano", "n_clicks")],
    [State("modal-plano", "is_open")],
    prevent_initial_call=True
)
def toggle_modal_plano(n1, n2, n3, n4, is_open):
    if n1 or n2 or n3 or n4:
        return not is_open
    return is_open


# Callback para calcular rendimentos em tempo real no modal
@app.callback(
    [Output("display-rendimento-diario", "children"),
     Output("display-rendimento-mensal", "children"),
     Output("display-rendimento-anual", "children")],
    [Input("input-valor-inicial-montante", "value"),
     Input("select-tipo-rendimento", "value"),
     Input("input-taxa-rendimento", "value"),
     Input("date-inicio-investimento", "date")],
    prevent_initial_call=False
)
def calcular_rendimentos_display(valor_inicial, tipo_rendimento, taxa, data_inicio):
    from datetime import datetime, date
    
    if not valor_inicial or not tipo_rendimento or tipo_rendimento == "Sem rendimento":
        return "R$ 0,00", "R$ 0,00", "R$ 0,00"
    
    valor_inicial = float(valor_inicial) if valor_inicial else 0
    taxa = float(taxa) if taxa else 0
    
    # Calcula dias decorridos desde o início
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio.split('T')[0], '%Y-%m-%d').date()
            dias = (date.today() - data_inicio_obj).days
            if dias < 0:
                dias = 0
        except:
            dias = 0
    else:
        dias = 0
    
    resultado = calcular_rendimento_investimento(
        valor_inicial, tipo_rendimento, taxa, dias
    )
    
    return (
        f"R$ {resultado['rendimento_diario']:.2f}",
        f"R$ {resultado['rendimento_mensal']:.2f}",
        f"R$ {resultado['rendimento_anual']:.2f}"
    )
    return is_open


@app.callback(
    Output("modal-montante", "is_open"),
    [Input("btn-add-montante", "n_clicks"),
     Input("btn-cancelar-montante", "n_clicks"),
     Input("btn-salvar-montante", "n_clicks")],
    [State("modal-montante", "is_open")],
    prevent_initial_call=True
)
def toggle_modal_montante(n1, n2, n3, is_open):
    if n1 or n2 or n3:
        return not is_open
    return is_open

