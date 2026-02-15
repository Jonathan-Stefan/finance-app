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
from constants import GRAPH_MARGIN, StatusDespesa
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


def _normalize_status_value(value):
    if pd.isna(value):
        return StatusDespesa.A_VENCER

    text = str(value).strip().lower()

    if text in {"pago", "paga", "paid", "1", "true", "sim", "yes"}:
        return StatusDespesa.PAGO
    if text in {"vencido", "vencida", "overdue", "atrasado", "2"}:
        return StatusDespesa.VENCIDO
    if text in {"a vencer", "avencer", "aberto", "pendente", "0", "false", "nao", "não", "no"}:
        return StatusDespesa.A_VENCER

    return StatusDespesa.A_VENCER


def _normalize_efetuado_value(value):
    if pd.isna(value):
        return 0

    text = str(value).strip().lower()
    if text in {"1", "true", "sim", "s", "yes", "y", "pago", "recebido"}:
        return 1
    if text in {"0", "false", "nao", "não", "n", "no", "pendente"}:
        return 0

    try:
        return 1 if float(text) == 1 else 0
    except Exception:
        return 0


def _normalize_despesas_for_saldo(df):
    """Normaliza despesas e mantém apenas colunas necessárias para regras de saldo."""
    if df.empty:
        return df

    if 'Status' in df.columns:
        df['Status'] = df['Status'].apply(_normalize_status_value)
    elif 'Efetuado' in df.columns:
        df['Efetuado'] = df['Efetuado'].apply(_normalize_efetuado_value)
        df['Status'] = df['Efetuado'].apply(lambda x: StatusDespesa.PAGO if x == 1 else StatusDespesa.A_VENCER)
    else:
        df['Status'] = StatusDespesa.A_VENCER

    if 'Valor' in df.columns:
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

    return df


def _normalize_receitas_for_saldo(df):
    """Normaliza receitas e mantém apenas colunas necessárias para regras de saldo."""
    if df.empty:
        return df

    if 'Efetuado' not in df.columns:
        df['Efetuado'] = 1
    else:
        df['Efetuado'] = df['Efetuado'].apply(_normalize_efetuado_value)

    if 'Valor' in df.columns:
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

    return df


def _apply_saldo_rules(df_despesas, df_receitas):
    """Aplica regra de saldo: despesas em aberto e receitas efetivadas."""
    df_despesas = _normalize_despesas_for_saldo(df_despesas)
    df_receitas = _normalize_receitas_for_saldo(df_receitas)

    if not df_despesas.empty and 'Status' in df_despesas.columns:
        df_despesas = df_despesas[df_despesas['Status'] != StatusDespesa.PAGO]

    if not df_receitas.empty and 'Efetuado' in df_receitas.columns:
        df_receitas = df_receitas[df_receitas['Efetuado'] == 1]

    return df_despesas, df_receitas

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
            ], xs=12, sm=12, md=3, lg=3),

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
            ], xs=12, sm=12, md=3, lg=3),

            # Despesas totais
            dbc.Col([
                dbc.CardGroup([
                    dbc.Card([
                        html.Legend("Despesas totais"),
                        html.H5("R$ -", id="p-despesa-total-dashboards"),
                    ], style={"padding-left": "20px", "padding-top": "10px"}),
                    dbc.Card(
                        html.Div(className="fa fa-meh-o", style=card_icon), 
                        color="danger",
                        style={"maxWidth": 75, "height": 100, "margin-left": "-10px"},
                    )
                ])
            ], xs=12, sm=12, md=3, lg=3),

            # Despesas em aberto
            dbc.Col([
                dbc.CardGroup([
                    dbc.Card([
                        html.Legend("Desp. em aberto"),
                        html.H5("R$ -", id="p-despesa-dashboards"),
                    ], style={"padding-left": "20px", "padding-top": "10px"}),
                    dbc.Card(
                        html.Div(className="fa fa-clock-o", style=card_icon), 
                        color="warning",
                        style={"maxWidth": 75, "height": 100, "margin-left": "-10px"},
                    )
                ])
            ], xs=12, sm=12, md=3, lg=3),
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
                        display_format='DD/MM/YYYY',
                        style={'z-index': '100'}),
                ], style={"padding": "20px", "height": "100%"}), 
            ], xs=12, sm=12, md=12, lg=4, className="mb-3"),

            dbc.Col(
                dbc.Card(dcc.Graph(id="graph1"), style={"padding": "10px", "height": "100%"}), xs=12, sm=12, md=12, lg=8, className="mb-3"
            ),
        ], className="g-2 equal-height-row"),

        dbc.Row([
            dbc.Col(dbc.Card(dcc.Graph(id="graph2"), style={"padding": "10px", "height": "100%"}), xs=12, sm=12, md=12, lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dcc.Graph(id="graph3"), style={"padding": "10px", "height": "100%"}), xs=12, sm=6, md=6, lg=3, className="mb-3"),
            dbc.Col(dbc.Card(dcc.Graph(id="graph4"), style={"padding": "10px", "height": "100%"}), xs=12, sm=6, md=6, lg=3, className="mb-3"),
        ], className="g-2 equal-height-row")
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

    # Regra consistente com saldo: considerar apenas receitas efetivadas
    df = _normalize_receitas_for_saldo(df)
    if 'Efetuado' in df.columns:
        df = df[df['Efetuado'] == 1]
    
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

    return [([{"label": x, "value": x} for x in df.Categoria.unique()]), val, f"R$ {valor:.2f}"]

# Dropdown Despesa
@app.callback([Output("dropdown-despesa", "options"),
    Output("dropdown-despesa", "value"),
    Output("p-despesa-total-dashboards", "children"),
    Output("p-despesa-dashboards", "children")],
    [Input("store-despesas", "data"),
    Input('date-picker-config', 'start_date'),
    Input('date-picker-config', 'end_date')])
def populate_dropdownvalues_despesas(data, start_date, end_date):
    df = pd.DataFrame(data)
    
    if df.empty or 'Categoria' not in df.columns or 'Valor' not in df.columns:
        return [[], [], "R$ 0", "R$ 0"]

    df_normalized = _normalize_despesas_for_saldo(df.copy())
    
    # Filtrar por período ANTES de separar totais e abertas
    if 'Data' in df_normalized.columns and start_date and end_date:
        df_normalized['Data'] = pd.to_datetime(df_normalized['Data'], errors='coerce')
        start = pd.to_datetime(start_date, errors='coerce')
        end = pd.to_datetime(end_date, errors='coerce')
        if not pd.isna(start) and not pd.isna(end):
            mask = (df_normalized['Data'] >= start) & (df_normalized['Data'] <= end)
            df_normalized = df_normalized.loc[mask]
    
    # DESPESAS TOTAIS: todas do período
    df_total = df_normalized.copy()
    
    # DESPESAS EM ABERTO: apenas as não pagas do período
    df_abertas = df_normalized[df_normalized['Status'] != StatusDespesa.PAGO] if 'Status' in df_normalized.columns else df_normalized

    valor_total = df_total['Valor'].sum() if not df_total.empty else 0
    valor_abertas = df_abertas['Valor'].sum() if not df_abertas.empty else 0
    val = df_normalized.Categoria.unique().tolist() if not df_normalized.empty else []

    return [([{"label": x, "value": x} for x in val]), val, f"R$ {valor_total:.2f}", f"R$ {valor_abertas:.2f}"]

# VALOR - saldo
@app.callback(
    Output("p-saldo-dashboards", "children"),
    [Input("store-despesas", "data"),
    Input("store-receitas", "data"),
    Input('date-picker-config', 'start_date'),
    Input('date-picker-config', 'end_date'),
    Input("store-user", "data")])
def saldo_total(despesas, receitas, start_date, end_date, user):
    df_despesas = pd.DataFrame(despesas)
    df_receitas = pd.DataFrame(receitas)
    
    # Excluir receitas que são destinadas a planos específicos
    if not df_receitas.empty and 'plano_id' in df_receitas.columns:
        df_receitas = df_receitas[df_receitas['plano_id'].isna()]
    
    # Normalização
    df_despesas = _normalize_despesas_for_saldo(df_despesas)
    df_receitas = _normalize_receitas_for_saldo(df_receitas)

    # LÓGICA CORRETA DE SALDO:
    # Saldo = Receitas efetivadas - Despesas PAGAS (exceto as pagas no cartão, pois viram fatura)
    # As despesas pagas no cartão NÃO saem do saldo imediatamente, só quando pagar a fatura
    
    # Receitas efetivadas (todas as efetivadas, independente de período)
    if not df_receitas.empty and 'Efetuado' in df_receitas.columns:
        df_receitas_efetivadas = df_receitas[df_receitas['Efetuado'] == 1]
    else:
        df_receitas_efetivadas = df_receitas
    
    # Despesas pagas (Status == PAGO) mas EXCLUINDO as que foram pagas no cartão
    # Porque despesas pagas no cartão não saem do saldo agora, só quando pagar a fatura
    if not df_despesas.empty and 'Status' in df_despesas.columns:
        df_despesas_pagas = df_despesas[df_despesas['Status'] == StatusDespesa.PAGO]
        
        # Excluir despesas pagas no cartão (que não são faturas)
        # Despesas no cartão geram faturas, e são as faturas que diminuem o saldo
        if 'forma_pagamento' in df_despesas_pagas.columns:
            df_despesas_pagas = df_despesas_pagas[
                (df_despesas_pagas['forma_pagamento'] != 'cartao') | 
                (df_despesas_pagas.get('eh_fatura', 0) == 1)
            ]
    else:
        df_despesas_pagas = pd.DataFrame()

    valor_receitas = df_receitas_efetivadas['Valor'].sum() if not df_receitas_efetivadas.empty and 'Valor' in df_receitas_efetivadas.columns else 0
    valor_despesas_pagas = df_despesas_pagas['Valor'].sum() if not df_despesas_pagas.empty and 'Valor' in df_despesas_pagas.columns else 0
    
    # Buscar saldo inicial do usuário
    saldo_inicial = 0
    if user and 'id' in user:
        from db import connect_db
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT saldo_inicial FROM users WHERE id = %s", (user['id'],))
        result = cur.fetchone()
        conn.close()
        if result and result[0]:
            saldo_inicial = float(result[0])
    
    # Saldo = Saldo inicial + Receitas efetivadas - Despesas pagas (dinheiro/faturas)
    saldo = saldo_inicial + valor_receitas - valor_despesas_pagas

    return f"R$ {saldo:.2f}"
    
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

    # Regras consistentes com saldo (despesas em aberto e receitas efetivadas)
    df_ds, df_rc = _apply_saldo_rules(df_ds, df_rc)

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

    # Regras consistentes com saldo (despesas em aberto e receitas efetivadas)
    df_ds, df_rc = _apply_saldo_rules(df_ds, df_rc)

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

    # Regras consistentes com saldo para receitas
    df = _normalize_receitas_for_saldo(df)
    if not df.empty and 'Efetuado' in df.columns:
        df = df[df['Efetuado'] == 1]
    
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

    # Regras consistentes com saldo para despesas
    df = _normalize_despesas_for_saldo(df)
    if not df.empty and 'Status' in df.columns:
        df = df[df['Status'] != StatusDespesa.PAGO]
    
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
