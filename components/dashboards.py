# Standard library imports
import calendar
from datetime import date, datetime, timedelta

# Third party imports
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

# Local imports
from app import app
from constants import GRAPH_MARGIN
from globals import *

card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": 30,
    "margin": "auto",
}

today = datetime.today()
# Início do mês
start_date = today.replace(day=1).date()
# Primeiro dia do próximo mês
if today.month == 12:
    next_month = today.replace(year=today.year + 1, month=1, day=1)
else:
    next_month = today.replace(month=today.month + 1, day=1)
    # Fim do mês atual
end_date = (next_month - timedelta(days=1)).date()

# =========  Layout  =========== #
layout = dbc.Col([
        dbc.Row([
            # Saldo
            dbc.Col([
                dbc.CardGroup([
                    dbc.Card([
                            html.Legend("Saldo"),
                            html.H5("R$ -", id="p-saldo-dashboards", style={}),
                    ], style={"padding-left": "20px", "padding-top": "10px"}),
                    dbc.Card(
                        html.Div(className="fa fa-university", style=card_icon), 
                        color="warning",
                        style={"maxWidth": 75, "height": 100, "margin-left": "-10px"},
                    )
                ])
            ], xs=12, sm=12, md=4, lg=4),

            # Receita
            dbc.Col([
                dbc.CardGroup([
                    dbc.Card([
                            html.Legend("Receita"),
                            html.H5("R$ -", id="p-receita-dashboards"),
                    ], style={"padding-left": "20px", "padding-top": "10px"}),
                    dbc.Card(
                        html.Div(className="fa fa-smile-o", style=card_icon), 
                        color="success",
                        style={"maxWidth": 75, "height": 100, "margin-left": "-10px"},
                    )
                ])
            ], xs=12, sm=12, md=4, lg=4),

            # Despesa
            dbc.Col([
                dbc.CardGroup([
                    dbc.Card([
                        html.Legend("Despesas"),
                        html.H5("R$ -", id="p-despesa-dashboards"),
                    ], style={"padding-left": "20px", "padding-top": "10px"}),
                    dbc.Card(
                        html.Div(className="fa fa-meh-o", style=card_icon), 
                        color="danger",
                        style={"maxWidth": 75, "height": 100, "margin-left": "-10px"},
                    )
                ])
            ], xs=12, sm=12, md=4, lg=4),
        ], className="g-2 mb-2"),

        # Alertas de Orçamento
        dbc.Row([
            dbc.Col([
                html.Div(id="alertas-orcamento")
            ], width=12)
        ], className="mb-2"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    html.Legend("Filtrar lançamentos", className="card-title"),
                    html.Label("Categorias das receitas"),
                    html.Div(
                        dcc.Dropdown(
                        id="dropdown-receita",
                        clearable=False,
                        style={"width": "100%"},
                        persistence=True,
                        persistence_type="session",
                        multi=True)                       
                    ),
                    
                    html.Label("Categorias das despesas", style={"margin-top": "10px"}),
                    dcc.Dropdown(
                        id="dropdown-despesa",
                        clearable=False,
                        style={"width": "100%"},
                        persistence=True,
                        persistence_type="session",
                        multi=True
                    ),
                    html.Legend("Período de Análise", style={"margin-top": "10px"}),
                    dcc.DatePickerRange(
                        month_format='Do MMM, YY',
                        end_date_placeholder_text='Data...',
                        start_date=start_date,
                        end_date=end_date,
                        with_portal=True,
                        updatemode='singledate',
                        id='date-picker-config',
                        style={'z-index': '100'}),
                ], style={"padding": "20px"}), 
            ], xs=12, sm=12, md=12, lg=4, className="mb-3"),

            dbc.Col(
                dbc.Card(dcc.Graph(id="graph1"), style={"padding": "10px"}), xs=12, sm=12, md=12, lg=8, className="mb-3"
            ),
        ], className="g-2"),

        dbc.Row([
            dbc.Col(dbc.Card(dcc.Graph(id="graph2"), style={"padding": "10px"}), xs=12, sm=12, md=12, lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dcc.Graph(id="graph3"), style={"padding": "10px"}), xs=12, sm=6, md=6, lg=3, className="mb-3"),
            dbc.Col(dbc.Card(dcc.Graph(id="graph4"), style={"padding": "10px"}), xs=12, sm=6, md=6, lg=3, className="mb-3"),
        ], className="g-2")
    ])



# =========  Callbacks  =========== #
# Dropdown Receita
@app.callback([Output("dropdown-receita", "options"),
    Output("dropdown-receita", "value"),
    Output("p-receita-dashboards", "children")],
    [Input("store-receitas", "data"),
    Input('date-picker-config', 'start_date'),
    Input('date-picker-config', 'end_date')])
def populate_dropdownvalues_receitas(data, start_date, end_date):
    df = pd.DataFrame(data)
    
    # Excluir receitas que são destinadas a planos específicos
    if not df.empty and 'plano_id' in df.columns:
        df = df[df['plano_id'].isna()]
    
    if df.empty or 'Categoria' not in df.columns or 'Valor' not in df.columns:
        return [[], [], "R$ 0"]
    
    # Filtrar por período se houver dados de data
    if 'Data' in df.columns and start_date and end_date:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        start = pd.to_datetime(start_date, errors='coerce')
        end = pd.to_datetime(end_date, errors='coerce')
        if not pd.isna(start) and not pd.isna(end):
            mask = (df['Data'] >= start) & (df['Data'] <= end)
            df = df.loc[mask]
    
    valor = df['Valor'].sum()
    val = df.Categoria.unique().tolist()

    return [([{"label": x, "value": x} for x in df.Categoria.unique()]), val, f"R$ {valor}"]

# Dropdown Despesa
@app.callback([Output("dropdown-despesa", "options"),
    Output("dropdown-despesa", "value"),
    Output("p-despesa-dashboards", "children")],
    [Input("store-despesas", "data"),
    Input('date-picker-config', 'start_date'),
    Input('date-picker-config', 'end_date')])
def populate_dropdownvalues_despesas(data, start_date, end_date):
    df = pd.DataFrame(data)
    
    if df.empty or 'Categoria' not in df.columns or 'Valor' not in df.columns:
        return [[], [], "R$ 0"]
    
    # Filtrar por período se houver dados de data
    if 'Data' in df.columns and start_date and end_date:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        start = pd.to_datetime(start_date, errors='coerce')
        end = pd.to_datetime(end_date, errors='coerce')
        if not pd.isna(start) and not pd.isna(end):
            mask = (df['Data'] >= start) & (df['Data'] <= end)
            df = df.loc[mask]
    
    valor = df['Valor'].sum()
    val = df.Categoria.unique().tolist()

    return [([{"label": x, "value": x} for x in df.Categoria.unique()]), val, f"R$ {valor}"]

# VALOR - saldo
@app.callback(
    Output("p-saldo-dashboards", "children"),
    [Input("store-despesas", "data"),
    Input("store-receitas", "data"),
    Input('date-picker-config', 'start_date'),
    Input('date-picker-config', 'end_date')])
def saldo_total(despesas, receitas, start_date, end_date):
    df_despesas = pd.DataFrame(despesas)
    df_receitas = pd.DataFrame(receitas)
    
    # Excluir receitas que são destinadas a planos específicos
    if not df_receitas.empty and 'plano_id' in df_receitas.columns:
        df_receitas = df_receitas[df_receitas['plano_id'].isna()]
    
    # Filtrar despesas por período
    if not df_despesas.empty and 'Data' in df_despesas.columns and start_date and end_date:
        df_despesas['Data'] = pd.to_datetime(df_despesas['Data'], errors='coerce')
        start = pd.to_datetime(start_date, errors='coerce')
        end = pd.to_datetime(end_date, errors='coerce')
        if not pd.isna(start) and not pd.isna(end):
            mask = (df_despesas['Data'] >= start) & (df_despesas['Data'] <= end)
            df_despesas = df_despesas.loc[mask]
    
    # Filtrar receitas por período
    if not df_receitas.empty and 'Data' in df_receitas.columns and start_date and end_date:
        df_receitas['Data'] = pd.to_datetime(df_receitas['Data'], errors='coerce')
        start = pd.to_datetime(start_date, errors='coerce')
        end = pd.to_datetime(end_date, errors='coerce')
        if not pd.isna(start) and not pd.isna(end):
            mask = (df_receitas['Data'] >= start) & (df_receitas['Data'] <= end)
            df_receitas = df_receitas.loc[mask]

    valor_despesas = df_despesas['Valor'].sum() if not df_despesas.empty and 'Valor' in df_despesas.columns else 0
    valor_receitas = df_receitas['Valor'].sum() if not df_receitas.empty and 'Valor' in df_receitas.columns else 0
    valor = valor_receitas - valor_despesas

    return f"R$ {valor}"
    
# Gráfico 1
@app.callback(
    Output('graph1', 'figure'),
    [Input('store-despesas', 'data'),
    Input('store-receitas', 'data'),
    Input("dropdown-despesa", "value"),
    Input("dropdown-receita", "value"),
    Input(ThemeChangerAIO.ids.radio("theme"), "value")])
def update_output(data_despesa, data_receita, despesa, receita, theme):
    df_ds = pd.DataFrame(data_despesa)
    df_rc = pd.DataFrame(data_receita)
    
    # Excluir receitas que são destinadas a planos específicos
    if not df_rc.empty and 'plano_id' in df_rc.columns:
        df_rc = df_rc[df_rc['plano_id'].isna()]

    # Validar se DataFrames têm colunas necessárias
    fig = go.Figure()
    
    if df_ds.empty or 'Data' not in df_ds.columns or 'Valor' not in df_ds.columns or 'Categoria' not in df_ds.columns:
        df_ds = pd.DataFrame(columns=['Data', 'Valor', 'Categoria', 'Mes', 'Acumulo'])
    else:
        df_ds = df_ds.sort_values(by='Data', ascending=True)
        df_ds["Data"] = pd.to_datetime(df_ds["Data"], errors="coerce")
        df_ds["Mes"] = df_ds["Data"].dt.month
    
    if df_rc.empty or 'Data' not in df_rc.columns or 'Valor' not in df_rc.columns or 'Categoria' not in df_rc.columns:
        df_rc = pd.DataFrame(columns=['Data', 'Valor', 'Categoria', 'Mes', 'Acumulo'])
    else:
        df_rc = df_rc.sort_values(by='Data', ascending=True)
        df_rc["Data"] = pd.to_datetime(df_rc["Data"], errors="coerce")
        df_rc["Mes"] = df_rc["Data"].dt.month

    # garante listas de categorias selecionadas
    if not receita:
        receita = df_rc['Categoria'].unique().tolist() if not df_rc.empty and len(df_rc) > 0 else []
    if not despesa:
        despesa = df_ds['Categoria'].unique().tolist() if not df_ds.empty and len(df_ds) > 0 else []

    # aplica filtros por categoria antes de calcular acumulados
    if not df_ds.empty and len(despesa) > 0:
        df_ds = df_ds[df_ds['Categoria'].isin(despesa)]
    if not df_rc.empty and len(receita) > 0:
        df_rc = df_rc[df_rc['Categoria'].isin(receita)]

    # calcula acumulados após filtro
    if not df_ds.empty and len(df_ds) > 0:
        df_ds['Acumulo'] = df_ds['Valor'].cumsum()
    if not df_rc.empty and len(df_rc) > 0:
        df_rc['Acumulo'] = df_rc['Valor'].cumsum()

    # saldo mensal a partir dos dados filtrados
    if not df_rc.empty and not df_ds.empty and len(df_rc) > 0 and len(df_ds) > 0:
        df_receitas_mes = df_rc.groupby("Mes")["Valor"].sum()
        df_despesas_mes = df_ds.groupby("Mes")["Valor"].sum()
        df_saldo_mes = df_receitas_mes - df_despesas_mes
        df_saldo_mes = df_saldo_mes.reset_index(name='Valor')
        df_saldo_mes['Acumulado'] = df_saldo_mes['Valor'].cumsum()
        # converte número do mês para abreviação de forma segura
        df_saldo_mes['Mes'] = df_saldo_mes['Mes'].apply(lambda x: calendar.month_abbr[int(x)] if not pd.isna(x) else '')
    
    # Adiciona trace apenas se há dados
    if not df_rc.empty and len(df_rc) > 0 and 'Acumulo' in df_rc.columns:
        fig.add_trace(go.Scatter(name='Receitas', x=df_rc['Data'], y=df_rc['Acumulo'], fill='tonextx', mode='lines'))

    fig.update_layout(margin=GRAPH_MARGIN, template=template_from_url(theme))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

# Gráfico 2
@app.callback(
    Output('graph2', 'figure'),
    [Input('store-receitas', 'data'),
    Input('store-despesas', 'data'),
    Input('dropdown-receita', 'value'),
    Input('dropdown-despesa', 'value'),
    Input('date-picker-config', 'start_date'),
    Input('date-picker-config', 'end_date'), 
    Input(ThemeChangerAIO.ids.radio("theme"), "value")]    
)
def graph2_show(data_receita, data_despesa, receita, despesa, start_date, end_date, theme):
    df_ds = pd.DataFrame(data_despesa)
    df_rc = pd.DataFrame(data_receita)
    
    # Excluir receitas que são destinadas a planos específicos
    if not df_rc.empty and 'plano_id' in df_rc.columns:
        df_rc = df_rc[df_rc['plano_id'].isna()]

    # Validar colunas necessárias
    if df_rc.empty or 'Categoria' not in df_rc.columns or 'Valor' not in df_rc.columns or 'Data' not in df_rc.columns:
        df_rc = pd.DataFrame(columns=['Data', 'Valor', 'Categoria', 'Output'])
    else:
        # adiciona coluna Output para legenda
        df_rc['Output'] = 'Receitas'
    
    if df_ds.empty or 'Categoria' not in df_ds.columns or 'Valor' not in df_ds.columns or 'Data' not in df_ds.columns:
        df_ds = pd.DataFrame(columns=['Data', 'Valor', 'Categoria', 'Output'])
    else:
        # adiciona coluna Output para legenda
        df_ds['Output'] = 'Despesas'

    # concatena e normaliza datas
    df_final = pd.concat([df_rc, df_ds], ignore_index=True, sort=False) if len([df for df in [df_rc, df_ds] if not df.empty])>0 else pd.DataFrame()
    if df_final.empty:
        fig = px.bar(pd.DataFrame(columns=['Data','Valor','Output']), x="Data", y="Valor", color='Output', barmode="group")
        fig.update_layout(margin=GRAPH_MARGIN, template=template_from_url(theme))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    # garante que Data seja datetime
    df_final['Data'] = pd.to_datetime(df_final['Data'], errors='coerce')

    # interpreta start/end
    start = pd.to_datetime(start_date, errors='coerce')
    end = pd.to_datetime(end_date, errors='coerce')

    if not pd.isna(start) and not pd.isna(end):
        mask = (df_final['Data'] >= start) & (df_final['Data'] <= end)
        df_final = df_final.loc[mask]

    # categorias padrão (se nenhum filtro selecionado)
    if not receita:
        receita = df_rc['Categoria'].unique().tolist() if not df_rc.empty and len(df_rc) > 0 else []
    if not despesa:
        despesa = df_ds['Categoria'].unique().tolist() if not df_ds.empty and len(df_ds) > 0 else []

    # aplica filtro de categorias
    if not df_final.empty and (len(receita) > 0 or len(despesa) > 0):
        df_final = df_final[df_final['Categoria'].isin(receita) | df_final['Categoria'].isin(despesa)]

    if df_final.empty:
        fig = px.bar(pd.DataFrame(columns=['Data','Valor','Output']), x="Data", y="Valor", color='Output', barmode="group")
        fig.update_layout(margin=GRAPH_MARGIN, template=template_from_url(theme))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    fig = px.bar(df_final.sort_values('Data'), x="Data", y="Valor", color='Output', barmode="group")        
    fig.update_layout(margin=GRAPH_MARGIN, template=template_from_url(theme))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    return fig


# Gráfico 3
@app.callback(
    Output('graph3', "figure"),
    [Input('store-receitas', 'data'),
    Input('dropdown-receita', 'value'),
    Input(ThemeChangerAIO.ids.radio("theme"), "value")]
)
def pie_receita(data_receita, receita, theme):
    df = pd.DataFrame(data_receita)
    
    # Verifica se o DataFrame está vazio ou não tem dados
    if df.empty or 'Categoria' not in df.columns:
        fig = go.Figure()
        fig.update_layout(
            title={'text': "Receitas"},
            margin=GRAPH_MARGIN,
            template=template_from_url(theme),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    df = df[df['Categoria'].isin(receita)]

    fig = px.pie(df, values=df.Valor, names=df.Categoria, hole=.2)
    fig.update_layout(title={'text': "Receitas"})
    fig.update_layout(margin=GRAPH_MARGIN, template=template_from_url(theme))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                  
    return fig    

# Gráfico 4
@app.callback(
    Output('graph4', "figure"),
    [Input('store-despesas', 'data'),
    Input('dropdown-despesa', 'value'),
    Input(ThemeChangerAIO.ids.radio("theme"), "value")]
)
def pie_despesa(data_despesa, despesa, theme):
    df = pd.DataFrame(data_despesa)
    
    # Verifica se o DataFrame está vazio ou não tem dados
    if df.empty or 'Categoria' not in df.columns:
        fig = go.Figure()
        fig.update_layout(
            title={'text': "Despesas"},
            margin=GRAPH_MARGIN,
            template=template_from_url(theme),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    df = df[df['Categoria'].isin(despesa)]

    fig = px.pie(df, values=df.Valor, names=df.Categoria, hole=.2)
    fig.update_layout(title={'text': "Despesas"})

    fig.update_layout(margin=GRAPH_MARGIN, template=template_from_url(theme))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    return fig


# Alertas de Orçamento
@app.callback(
    Output("alertas-orcamento", "children"),
    [Input("store-despesas", "data"),
     Input("store-user", "data"),
     Input('date-picker-config', 'start_date'),
     Input('date-picker-config', 'end_date')]
)
def mostrar_alertas_orcamento(despesas, user, start_date, end_date):
    if not user or 'id' not in user:
        return None
    
    from db import get_orcamentos, get_gastos_por_categoria
    
    # Pegar mês e ano do período selecionado
    try:
        data_inicio = pd.to_datetime(start_date)
        mes = data_inicio.month
        ano = data_inicio.year
    except:
        mes = datetime.now().month
        ano = datetime.now().year
    
    # Buscar orçamentos
    orcamentos = get_orcamentos(user['id'], mes, ano)
    
    if not orcamentos:
        return None
    
    # Buscar gastos
    gastos = get_gastos_por_categoria(user['id'], mes, ano)
    
    # Criar alertas
    alertas = []
    for orc in orcamentos:
        categoria = orc['categoria']
        limite = orc['valor_limite']
        gasto = gastos.get(categoria, 0)
        percentual = (gasto / limite * 100) if limite > 0 else 0
        
        # Mostrar apenas orçamentos em alerta (>= 80%)
        if percentual >= 80:
            if percentual >= 100:
                cor = "danger"
                icone = "🚨"
                mensagem = f"{icone} {categoria}: R$ {gasto:.2f} / R$ {limite:.2f} - LIMITE EXCEDIDO!"
            else:
                cor = "warning"
                icone = "⚠️"
                mensagem = f"{icone} {categoria}: R$ {gasto:.2f} / R$ {limite:.2f} - {percentual:.0f}% do orçamento"
            
            alertas.append(
                dbc.Col([
                    dbc.Alert([
                        html.Strong(mensagem),
                        dbc.Progress(
                            value=min(percentual, 100),
                            color=cor,
                            style={"height": "10px", "margin-top": "5px"}
                        )
                    ], color=cor, className="mb-0")
                ], xs=12, sm=6, md=4, lg=3)
            )
    
    if not alertas:
        return None
    
    return dbc.Row(alertas, className="g-2")
