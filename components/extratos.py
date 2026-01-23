import dash
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash.dash_table.Format import Group
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

from app import app
from dash_bootstrap_templates import template_from_url, ThemeChangerAIO
graph_margin=dict(l=25, r=25, t=25, b=0)

# =========  Layout  =========== #
layout = dbc.Col([
    # Stores temporários para dados editados
    dcc.Store(id='temp-receitas-data', data=None),
    dcc.Store(id='temp-despesas-data', data=None),
    
    dbc.Row([
        dbc.Col([html.Legend("Tabela de receitas")], width=8),
        dbc.Col([
            dbc.Button("Salvar Alterações", id="btn-salvar-receitas", color="success", size="sm", className="float-end")
        ], width=4),
    ], className="mb-2"),
    dbc.Row([
        html.Div(id="tabela-receitas", className="dbc"),
    ]),
    html.Div(id="msg-receitas", className="mt-2"),

    dbc.Row([
        dbc.Col([html.Legend("Tabela de despesas")], width=8),
        dbc.Col([
            dbc.Button("Salvar Alterações", id="btn-salvar-despesas", color="success", size="sm", className="float-end")
        ], width=4),
    ], className="mb-2 mt-4"),
    dbc.Row([
        html.Div(id="tabela-despesas", className="dbc"),
    ]),
    html.Div(id="msg-despesas", className="mt-2"),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='bar-graph', style={"margin-right": "20px"}),
        ], width=9),

        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H4("Despesas"),
                    html.Legend("R$ -", id="valor_despesa_card", style={'font-size': '60px'}),
                    html.H6("Total de despesas"),
                ], style={'text-align': 'center', 'padding-top': '30px'}))
        ], width=3),
    ], className="mt-4"),
], style={"padding": "10px"})

# =========  Callbacks  =========== #
# Helpers
def _yesno_to_int(value):
    if value in (1, "1", True):
        return 1
    if value in (0, "0", False):
        return 0
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("sim", "s", "true", "yes"):
            return 1
        if v in ("não", "nao", "n", "false", "no"):
            return 0
    return None


def _parse_float(value):
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def _normalize_date(value):
    if value in (None, "", "-"):
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.strftime('%Y-%m-%d')


def _normalize_row(row):
    # Normaliza Status para despesas (se existir)
    status = row.get("Status")
    if status not in ("Pago", "A vencer", "Vencido"):
        status = None
    
    return {
        "Valor": _parse_float(row.get("Valor")),
        "Efetuado": _yesno_to_int(row.get("Efetuado")),
        "Status": status,
        "Fixo": _yesno_to_int(row.get("Fixo")),
        "Data": _normalize_date(row.get("Data")),
        "Categoria": None if row.get("Categoria") in (None, "", "-") else row.get("Categoria"),
        "Descrição": None if row.get("Descrição") in (None, "", "-") else row.get("Descrição"),
    }


def _row_map(rows):
    if not rows:
        return {}
    mapped = {}
    for r in rows:
        rid = r.get("id")
        if rid is not None:
            try:
                rid = int(rid)
            except Exception:
                pass
            mapped[rid] = r
    return mapped


# Tabela receitas
@app.callback(
    Output('tabela-receitas', 'children'),
    Input('store-receitas', 'data')
)
def imprimir_tabela_receitas(data):
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["id", "Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "user_id"])
    
    df['Data'] = pd.to_datetime(df['Data']).dt.date

    df['Efetuado'] = df['Efetuado'].astype(object)
    df.loc[df['Efetuado'] == 0, 'Efetuado'] = 'Não'
    df.loc[df['Efetuado'] == 1, 'Efetuado'] = 'Sim'

    df['Fixo'] = df['Fixo'].astype(object)
    df.loc[df['Fixo'] == 0, 'Fixo'] = 'Não'
    df.loc[df['Fixo'] == 1, 'Fixo'] = 'Sim'

    df = df.fillna('-')
    df = df.drop(columns=[c for c in ["user_id"] if c in df.columns])

    df.sort_values(by='Data', ascending=False)

    tabela = dash_table.DataTable(
        id='datatable-receitas',
        columns=[
            {"name": "ID", "id": "id", "editable": False} if i == "id" else
            {"name": i, "id": i, "deletable": False, "selectable": False, "hideable": True}
            for i in df.columns
        ],

        data=df.to_dict('records'),
        editable=True,
        row_deletable=True,
        filter_action="native",    
        sort_action="native",       
        sort_mode="single",  
        selected_columns=[],        
        selected_rows=[],          
        page_action="native",      
        page_current=0,             
        page_size=10,
        style_cell_conditional=[
            {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden', 'textAlign': 'left'}
        ],
        style_header_conditional=[
            {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden'}
        ],
    ),

    return tabela


# Tabela despesas
@app.callback(
    Output('tabela-despesas', 'children'),
    Input('store-despesas', 'data')
)
def imprimir_tabela_despesas(data):
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["id", "Valor", "Status", "Fixo", "Data", "Categoria", "Descrição", "user_id"])
    
    df['Data'] = pd.to_datetime(df['Data']).dt.date

    # Se tiver Status, usa ele; senão mantém Efetuado (migração)
    if 'Status' not in df.columns:
        df['Status'] = df.get('Efetuado', 0).apply(lambda x: 'Pago' if x == 1 else 'A vencer')
    
    # Normaliza Status (garante que não tenha valores inválidos)
    df['Status'] = df['Status'].fillna('A vencer')

    df['Fixo'] = df['Fixo'].astype(object)
    df.loc[df['Fixo'] == 0, 'Fixo'] = 'Não'
    df.loc[df['Fixo'] == 1, 'Fixo'] = 'Sim'

    df = df.fillna('-')
    # Remove colunas desnecessárias
    df = df.drop(columns=[c for c in ["user_id", "Efetuado"] if c in df.columns])

    df.sort_values(by='Data', ascending=False)

    tabela = dash_table.DataTable(
        id='datatable-despesas',
        columns=[
            {"name": "ID", "id": "id", "editable": False} if i == "id" else
            {"name": i, "id": i, "deletable": False, "selectable": False, "hideable": True, 
             "presentation": "dropdown"} if i == "Status" else
            {"name": i, "id": i, "deletable": False, "selectable": False, "hideable": True}
            for i in df.columns
        ],
        dropdown={
            'Status': {
                'options': [
                    {'label': 'Pago', 'value': 'Pago'},
                    {'label': 'A vencer', 'value': 'A vencer'},
                    {'label': 'Vencido', 'value': 'Vencido'}
                ]
            }
        },

        data=df.to_dict('records'),
        editable=True,
        row_deletable=True,
        filter_action="native",    
        sort_action="native",       
        sort_mode="single",  
        selected_columns=[],        
        selected_rows=[],          
        page_action="native",      
        page_current=0,             
        page_size=10,
        style_cell_conditional=[
            {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden', 'textAlign': 'left'}
        ],
        style_header_conditional=[
            {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden'}
        ],
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Status} = "Vencido"',
                    'column_id': 'Status'
                },
                'backgroundColor': '#ffcccc',
                'color': 'darkred',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{Status} = "Pago"',
                    'column_id': 'Status'
                },
                'backgroundColor': '#ccffcc',
                'color': 'darkgreen'
            },
            {
                'if': {
                    'filter_query': '{Status} = "A vencer"',
                    'column_id': 'Status'
                },
                'backgroundColor': '#ffffcc',
                'color': '#cc8800'
            }
        ],
    ),

    return tabela


# Capturar dados editados da tabela de receitas
@app.callback(
    Output('temp-receitas-data', 'data'),
    Input('datatable-receitas', 'data'),
    prevent_initial_call=True
)
def capture_receitas_edits(data):
    return data


# Sync receitas (update/delete)
@app.callback(
    Output('store-refresh-receitas', 'data', allow_duplicate=True),
    Output('msg-receitas', 'children'),
    Input('btn-salvar-receitas', 'n_clicks'),
    State('temp-receitas-data', 'data'),
    State('store-user', 'data'),
    State('store-refresh-receitas', 'data'),
    prevent_initial_call=True
)
def sync_receitas(n_clicks, data, user, refresh):
    if not n_clicks:
        return dash.no_update, ""
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000)
    if data is None:
        return dash.no_update, dbc.Alert("Sem dados para salvar", color="warning", duration=3000)
    
    from db import table_to_df, delete_transacao, update_transacao
    prev_records = table_to_df('receitas', user_id=user['id'], include_id=True).to_dict('records')
    
    # Mapear registros atuais e anteriores por ID
    curr = {int(r['id']): r for r in data if r.get('id') is not None and str(r.get('id')).strip()}
    prev = {int(r['id']): r for r in prev_records if r.get('id') is not None}
    
    curr_ids = set(curr.keys())
    prev_ids = set(prev.keys())
    
    # IDs removidos
    removed_ids = prev_ids - curr_ids
    # IDs que ainda existem (podem ter sido editados)
    existing_ids = prev_ids & curr_ids
    
    changed = False
    deletados = 0
    atualizados = 0
    
    # Deletar linhas removidas
    for rid in removed_ids:
        delete_transacao('receitas', rid, user['id'])
        deletados += 1
        changed = True
    
    # Atualizar linhas modificadas
    for rid in existing_ids:
        new_row = _normalize_row(curr[rid])
        old_row = _normalize_row(prev[rid])
        if new_row != old_row:
            update_transacao('receitas', rid, new_row, user['id'])
            atualizados += 1
            changed = True
    
    if changed:
        msg_parts = []
        if atualizados > 0:
            msg_parts.append(f"{atualizados} receita(s) atualizada(s)")
        if deletados > 0:
            msg_parts.append(f"{deletados} receita(s) deletada(s)")
        mensagem = ", ".join(msg_parts)
        return (refresh or 0) + 1, dbc.Alert(f"✓ {mensagem}", color="success", duration=4000)
    else:
        return dash.no_update, dbc.Alert("Nenhuma alteração detectada", color="info", duration=3000)


# Capturar dados editados da tabela de despesas
@app.callback(
    Output('temp-despesas-data', 'data'),
    Input('datatable-despesas', 'data'),
    prevent_initial_call=True
)
def capture_despesas_edits(data):
    return data


# Sync despesas (update/delete)
@app.callback(
    Output('store-refresh-despesas', 'data', allow_duplicate=True),
    Output('msg-despesas', 'children'),
    Input('btn-salvar-despesas', 'n_clicks'),
    State('temp-despesas-data', 'data'),
    State('store-user', 'data'),
    State('store-refresh-despesas', 'data'),
    prevent_initial_call=True
)
def sync_despesas(n_clicks, data, user, refresh):
    if not n_clicks:
        return dash.no_update, ""
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000)
    if data is None:
        return dash.no_update, dbc.Alert("Sem dados para salvar", color="warning", duration=3000)
    
    from db import table_to_df, delete_transacao, update_transacao
    prev_records = table_to_df('despesas', user_id=user['id'], include_id=True).to_dict('records')
    
    # Mapear registros atuais e anteriores por ID
    curr = {int(r['id']): r for r in data if r.get('id') is not None and str(r.get('id')).strip()}
    prev = {int(r['id']): r for r in prev_records if r.get('id') is not None}
    
    curr_ids = set(curr.keys())
    prev_ids = set(prev.keys())
    
    # IDs removidos
    removed_ids = prev_ids - curr_ids
    # IDs que ainda existem (podem ter sido editados)
    existing_ids = prev_ids & curr_ids
    
    changed = False
    deletados = 0
    atualizados = 0
    
    # Deletar linhas removidas
    for rid in removed_ids:
        delete_transacao('despesas', rid, user['id'])
        deletados += 1
        changed = True
    
    # Atualizar linhas modificadas
    for rid in existing_ids:
        new_row = _normalize_row(curr[rid])
        old_row = _normalize_row(prev[rid])
        if new_row != old_row:
            update_transacao('despesas', rid, new_row, user['id'])
            atualizados += 1
            changed = True
    
    if changed:
        msg_parts = []
        if atualizados > 0:
            msg_parts.append(f"{atualizados} despesa(s) atualizada(s)")
        if deletados > 0:
            msg_parts.append(f"{deletados} despesa(s) deletada(s)")
        mensagem = ", ".join(msg_parts)
        return (refresh or 0) + 1, dbc.Alert(f"✓ {mensagem}", color="success", duration=4000)
    else:
        return dash.no_update, dbc.Alert("Nenhuma alteração detectada", color="info", duration=3000)

# Bar Graph            
@app.callback(
    Output('bar-graph', 'figure'),
    [Input('store-despesas', 'data'),
    Input(ThemeChangerAIO.ids.radio("theme"), "value")]
)
def bar_chart(data, theme):
    df = pd.DataFrame(data)
    
    if df.empty:
        graph = go.Figure()
        graph.update_layout(
            title="Despesas Gerais",
            margin=graph_margin,
            template=template_from_url(theme),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[{
                'text': 'Sem dados de despesas',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
        return graph
    
    df_grouped = df.groupby("Categoria").sum()[["Valor"]].reset_index()
    graph = px.bar(df_grouped, x='Categoria', y='Valor', title="Despesas Gerais")
    graph.update_layout(margin=graph_margin,template=template_from_url(theme))
    graph.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return graph

# Simple card
@app.callback(
    Output('valor_despesa_card', 'children'),
    Input('store-despesas', 'data')
)
def display_desp(data):
    df = pd.DataFrame(data)
    valor = df['Valor'].sum() if not df.empty else 0
    
    return f"R$ {valor}"