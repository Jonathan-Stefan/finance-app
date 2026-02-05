import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import template_from_url, ThemeChangerAIO
from db import table_to_df, delete_transacao, update_transacao

# Local imports
from app import app
from constants import (
    COLOR_SUCCESS, GRAPH_MARGIN, TABLE_PAGE_SIZE,
    StatusDespesa, EFETUADO_SIM, EFETUADO_NAO, FIXO_SIM, FIXO_NAO
)

from utils.validators import (
    yesno_to_int, parse_float_value, normalize_date,
    normalize_string, validate_status
)

# =========  Layout  =========== #
layout = dbc.Col([
    # Stores temporários para dados editados
    dcc.Store(id='temp-receitas-data', data=None),
    dcc.Store(id='temp-despesas-data', data=None),
    # Stores para guardar estado original da tabela (antes de edições)
    dcc.Store(id='original-receitas-data', data=None),
    dcc.Store(id='original-despesas-data', data=None),
    
    # Filtro de período
    dbc.Row([
        dbc.Col([
            html.Label("Filtrar por período:"),
            dcc.DatePickerRange(
                id='date-picker-extratos',
                month_format='Do MMM, YY',
                end_date_placeholder_text='Data...',
                with_portal=True,
                updatemode='singledate',
                display_format='DD/MM/YYYY'
            ),
        ], width=12)
    ], className="mb-3"),
    
    dbc.Row([
        dbc.Col([html.Legend("Tabela de receitas")], width=8),
        dbc.Col([
            dbc.Button("Salvar Alterações", id="btn-salvar-receitas", color="success", size="sm", className="float-end")
        ], width=4),
    ], className="mb-2"),
    dbc.Row([
        dash_table.DataTable(
            id='datatable-receitas',
            columns=[
                {"name": "ID", "id": "id", "editable": False},
                {"name": "Valor", "id": "Valor"},
                {"name": "Efetuado", "id": "Efetuado", "presentation": "dropdown"},
                {"name": "Fixo", "id": "Fixo", "presentation": "dropdown"},
                {"name": "Data", "id": "Data"},
                {"name": "Categoria", "id": "Categoria"},
                {"name": "Descrição", "id": "Descrição"},
            ],
            dropdown={
                'Efetuado': {
                    'options': [
                        {'label': EFETUADO_SIM, 'value': EFETUADO_SIM},
                        {'label': EFETUADO_NAO, 'value': EFETUADO_NAO}
                    ]
                },
                'Fixo': {
                    'options': [
                        {'label': FIXO_SIM, 'value': FIXO_SIM},
                        {'label': FIXO_NAO, 'value': FIXO_NAO}
                    ]
                }
            },
            data=[],
            editable=True,
            row_deletable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="single",
            page_action="native",
            page_current=0,
            page_size=10,
            style_cell_conditional=[
                {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden'}
            ],
            style_header_conditional=[
                {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden'}
            ],
        ),
    ]),
    html.Div(id="msg-receitas", className="mt-2"),

    dbc.Row([
        dbc.Col([html.Legend("Tabela de despesas")], width=8),
        dbc.Col([
            dbc.Button("Salvar Alterações", id="btn-salvar-despesas", color="success", size="sm", className="float-end")
        ], width=4),
    ], className="mb-2 mt-4"),
    dbc.Row([
        dash_table.DataTable(
            id='datatable-despesas',
            columns=[
                {"name": "ID", "id": "id", "editable": False},
                {"name": "Valor", "id": "Valor"},
                {"name": "Status", "id": "Status", "presentation": "dropdown"},
                {"name": "Fixo", "id": "Fixo", "presentation": "dropdown"},
                {"name": "Data", "id": "Data"},
                {"name": "Categoria", "id": "Categoria"},
                {"name": "Descrição", "id": "Descrição"},
            ],
            dropdown={
                'Status': {
                    'options': [
                        {'label': StatusDespesa.PAGO, 'value': StatusDespesa.PAGO},
                        {'label': StatusDespesa.A_VENCER, 'value': StatusDespesa.A_VENCER},
                        {'label': StatusDespesa.VENCIDO, 'value': StatusDespesa.VENCIDO}
                    ]
                },
                'Fixo': {
                    'options': [
                        {'label': FIXO_SIM, 'value': FIXO_SIM},
                        {'label': FIXO_NAO, 'value': FIXO_NAO}
                    ]
                }
            },
            data=[],
            editable=True,
            row_deletable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="single",
            page_action="native",
            page_current=0,
            page_size=10,
            style_cell_conditional=[
                {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden'}
            ],
            style_header_conditional=[
                {'if': {'column_id': 'id'}, 'width': '0px', 'minWidth': '0px', 'maxWidth': '0px', 'overflow': 'hidden'}
            ],
            style_data_conditional=[
                {
                    'if': {
                        'filter_query': f'{{Status}} = "{StatusDespesa.VENCIDO}"',
                        'column_id': 'Status'
                    },
                    'backgroundColor': '#ffcccc',
                    'color': 'darkred',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': f'{{Status}} = "{StatusDespesa.PAGO}"',
                        'column_id': 'Status'
                    },
                    'backgroundColor': '#ccffcc',
                    'color': 'darkgreen'
                },
                {
                    'if': {
                        'filter_query': f'{{Status}} = "{StatusDespesa.A_VENCER}"',
                        'column_id': 'Status'
                    },
                    'backgroundColor': '#ffffcc',
                    'color': '#cc8800'
                }
            ],
        ),
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
def _normalize_row(row):
    """Normaliza uma linha de dados para atualização no banco"""
    # Normaliza Status para despesas
    status = validate_status(row.get("Status"))
    
    # Para receitas, Efetuado ainda existe
    efetuado = yesno_to_int(row.get("Efetuado"))
    
    result = {
        "Valor": parse_float_value(row.get("Valor")),
        "Fixo": yesno_to_int(row.get("Fixo")),
        "Data": normalize_date(row.get("Data")),
        "Categoria": normalize_string(row.get("Categoria")),
        "Descrição": normalize_string(row.get("Descrição")),
    }
    
    # Adiciona Efetuado apenas se existir (para receitas)
    if efetuado is not None:
        result["Efetuado"] = efetuado
    
    # Adiciona Status apenas se existir (para despesas)
    if status is not None:
        result["Status"] = status
    
    return result

# Tabela receitas - atualizar dados
@app.callback(
    Output('datatable-receitas', 'data'),
    [Input('store-receitas', 'data'),
     Input('date-picker-extratos', 'start_date'),
     Input('date-picker-extratos', 'end_date')]
)
def atualizar_dados_receitas(data, start_date, end_date):
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["id", "Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "user_id"])
    
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    
    # Aplicar filtro de período
    if start_date and end_date:
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()
        df = df[(df['Data'] >= start) & (df['Data'] <= end)]

    df['Efetuado'] = df['Efetuado'].astype(object)
    df.loc[df['Efetuado'] == 0, 'Efetuado'] = EFETUADO_NAO
    df.loc[df['Efetuado'] == 1, 'Efetuado'] = EFETUADO_SIM

    df['Fixo'] = df['Fixo'].astype(object)
    df.loc[df['Fixo'] == 0, 'Fixo'] = FIXO_NAO
    df.loc[df['Fixo'] == 1, 'Fixo'] = FIXO_SIM

    df = df.fillna('-')
    df = df.drop(columns=[c for c in ["user_id"] if c in df.columns])
    df = df.sort_values(by='Data', ascending=True)
    
    return df.to_dict('records')

# Tabela despesas - atualizar dados
@app.callback(
    Output('datatable-despesas', 'data'),
    [Input('store-despesas', 'data'),
     Input('date-picker-extratos', 'start_date'),
     Input('date-picker-extratos', 'end_date')]
)
def atualizar_dados_despesas(data, start_date, end_date):
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["id", "Valor", "Status", "Fixo", "Data", "Categoria", "Descrição", "user_id"])
    
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    
    # Aplicar filtro de período
    if start_date and end_date:
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()
        df = df[(df['Data'] >= start) & (df['Data'] <= end)]

    # Se tiver Status, usa ele; senão mantém Efetuado (migração)
    if 'Status' not in df.columns:
        df['Status'] = df.get('Efetuado', 0).apply(lambda x: StatusDespesa.PAGO if x == 1 else StatusDespesa.A_VENCER)
    
    # Normaliza Status (garante que não tenha valores inválidos)
    df['Status'] = df['Status'].fillna(StatusDespesa.A_VENCER)

    df['Fixo'] = df['Fixo'].astype(object)
    df.loc[df['Fixo'] == 0, 'Fixo'] = FIXO_NAO
    df.loc[df['Fixo'] == 1, 'Fixo'] = FIXO_SIM

    df = df.fillna('-')
    # Remove colunas desnecessárias
    df = df.drop(columns=[c for c in ["user_id", "Efetuado"] if c in df.columns])
    df = df.sort_values(by='Data', ascending=True)

    return df.to_dict('records')

# Capturar estado original da tabela de receitas ao carregar
@app.callback(
    Output('original-receitas-data', 'data'),
    Input('datatable-receitas', 'data'),
    State('original-receitas-data', 'data'),
    prevent_initial_call=True
)
def capture_original_receitas(data, original_data):
    # Só guarda o estado original na primeira vez (quando ainda é None)
    if original_data is None:
        return data
    return dash.no_update

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
    Output('original-receitas-data', 'data', allow_duplicate=True),
    Input('btn-salvar-receitas', 'n_clicks'),
    State('temp-receitas-data', 'data'),
    State('original-receitas-data', 'data'),
    State('store-user', 'data'),
    State('store-refresh-receitas', 'data'),
    prevent_initial_call=True
)
def sync_receitas(n_clicks, data, original_data, user, refresh):
    if not n_clicks:
        return dash.no_update, "", dash.no_update
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000), dash.no_update
    if data is None:
        return dash.no_update, dbc.Alert("Sem dados para salvar", color="warning", duration=3000), dash.no_update
    
    # Mapear registros atuais da tabela
    curr = {}
    for r in data:
        try:
            if r.get('id') is not None and str(r.get('id')).strip():
                curr[int(r['id'])] = r
        except (ValueError, TypeError):
            continue
    
    # Mapear registros originais da tabela (antes das edições)
    orig = {}
    if original_data:
        for r in original_data:
            try:
                if r.get('id') is not None and str(r.get('id')).strip():
                    orig[int(r['id'])] = r
            except (ValueError, TypeError):
                continue
    
    curr_ids = set(curr.keys())
    orig_ids = set(orig.keys())
    
    # IDs removidos manualmente da tabela
    removed_ids = orig_ids - curr_ids
    # IDs que existem em ambos (podem ter sido editados)
    existing_ids = orig_ids & curr_ids
    
    deletados = 0
    atualizados = 0
    
    # Deletar linhas removidas manualmente pelo usuário
    for rid in removed_ids:
        delete_transacao('receitas', rid, user['id'])
        deletados += 1
    
    # Atualizar linhas modificadas
    for rid in existing_ids:
        new_row = _normalize_row(curr[rid])
        old_row = _normalize_row(orig[rid])
        if new_row != old_row:
            update_transacao('receitas', rid, new_row, user['id'])
            atualizados += 1
    
    if atualizados > 0 or deletados > 0:
        msg_parts = []
        if atualizados > 0:
            msg_parts.append(f"{atualizados} receita(s) atualizada(s)")
        if deletados > 0:
            msg_parts.append(f"{deletados} receita(s) deletada(s)")
        mensagem = ", ".join(msg_parts)
        # Resetar estado original após salvar
        return (refresh or 0) + 1, dbc.Alert(f"✓ {mensagem}", color="success", duration=4000), None
    else:
        return dash.no_update, dbc.Alert("Nenhuma alteração detectada", color="info", duration=3000), dash.no_update

# Capturar estado original da tabela de despesas ao carregar
@app.callback(
    Output('original-despesas-data', 'data'),
    Input('datatable-despesas', 'data'),
    State('original-despesas-data', 'data'),
    prevent_initial_call=True
)
def capture_original_despesas(data, original_data):
    # Só guarda o estado original na primeira vez (quando ainda é None)
    if original_data is None:
        return data
    return dash.no_update

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
    Output('original-despesas-data', 'data', allow_duplicate=True),
    Input('btn-salvar-despesas', 'n_clicks'),
    State('temp-despesas-data', 'data'),
    State('original-despesas-data', 'data'),
    State('store-user', 'data'),
    State('store-refresh-despesas', 'data'),
    prevent_initial_call=True
)
def sync_despesas(n_clicks, data, original_data, user, refresh):
    if not n_clicks:
        return dash.no_update, "", dash.no_update
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000), dash.no_update
    if data is None:
        return dash.no_update, dbc.Alert("Sem dados para salvar", color="warning", duration=3000), dash.no_update
    
    # Mapear registros atuais da tabela
    curr = {}
    for r in data:
        try:
            if r.get('id') is not None and str(r.get('id')).strip():
                curr[int(r['id'])] = r
        except (ValueError, TypeError):
            continue
    
    # Mapear registros originais da tabela (antes das edições)
    orig = {}
    if original_data:
        for r in original_data:
            try:
                if r.get('id') is not None and str(r.get('id')).strip():
                    orig[int(r['id'])] = r
            except (ValueError, TypeError):
                continue
    
    curr_ids = set(curr.keys())
    orig_ids = set(orig.keys())
    
    # IDs removidos manualmente da tabela
    removed_ids = orig_ids - curr_ids
    # IDs que existem em ambos (podem ter sido editados)
    existing_ids = orig_ids & curr_ids
    
    deletados = 0
    atualizados = 0
    
    # Deletar linhas removidas manualmente pelo usuário
    for rid in removed_ids:
        delete_transacao('despesas', rid, user['id'])
        deletados += 1
    
    # Atualizar linhas modificadas
    for rid in existing_ids:
        new_row = _normalize_row(curr[rid])
        old_row = _normalize_row(orig[rid])
        if new_row != old_row:
            update_transacao('despesas', rid, new_row, user['id'])
            atualizados += 1
    
    if atualizados > 0 or deletados > 0:
        msg_parts = []
        if atualizados > 0:
            msg_parts.append(f"{atualizados} despesa(s) atualizada(s)")
        if deletados > 0:
            msg_parts.append(f"{deletados} despesa(s) deletada(s)")
        mensagem = ", ".join(msg_parts)
        # Resetar estado original após salvar
        return (refresh or 0) + 1, dbc.Alert(f"✓ {mensagem}", color="success", duration=4000), None
    else:
        return dash.no_update, dbc.Alert("Nenhuma alteração detectada", color="info", duration=3000), dash.no_update

# Bar Graph            
@app.callback(
    Output('bar-graph', 'figure'),
    [Input('store-despesas', 'data'),
    Input('date-picker-extratos', 'start_date'),
    Input('date-picker-extratos', 'end_date'),
    Input(ThemeChangerAIO.ids.radio("theme"), "value")]
)
def bar_chart(data, start_date, end_date, theme):
    df = pd.DataFrame(data)
    
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
        
        # Aplicar filtro de período apenas se ambos start_date e end_date estiverem preenchidos
        if start_date and end_date:
            start = pd.to_datetime(start_date).date()
            end = pd.to_datetime(end_date).date()
            df['Data'] = df['Data'].dt.date
            df = df[(df['Data'] >= start) & (df['Data'] <= end)]
    
    if df.empty:
        graph = go.Figure()
        graph.update_layout(
            title="Despesas Gerais",
            margin=GRAPH_MARGIN,
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
    
    df_grouped = df.groupby("Categoria")["Valor"].sum().reset_index()
    graph = px.bar(df_grouped, x='Categoria', y='Valor', title="Despesas Gerais")
    graph.update_layout(margin=GRAPH_MARGIN,template=template_from_url(theme))
    graph.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return graph

# Simple card
@app.callback(
    Output('valor_despesa_card', 'children'),
    [Input('store-despesas', 'data'),
    Input('date-picker-extratos', 'start_date'),
    Input('date-picker-extratos', 'end_date')]
)
def display_desp(data, start_date, end_date):
    df = pd.DataFrame(data)
    
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
        
        # Aplicar filtro de período apenas se ambos start_date e end_date estiverem preenchidos
        if start_date and end_date:
            start = pd.to_datetime(start_date).date()
            end = pd.to_datetime(end_date).date()
            df['Data'] = df['Data'].dt.date
            df = df[(df['Data'] >= start) & (df['Data'] <= end)]
    
    valor = df['Valor'].sum() if not df.empty else 0
    
    return f"R$ {valor:.2f}"
