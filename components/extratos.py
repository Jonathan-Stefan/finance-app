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
    # Store para rastrear deleções manuais
    dcc.Store(id='deleted-receitas-ids', data=[]),
    dcc.Store(id='deleted-despesas-ids', data=[]),
    
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
        dbc.Col([html.Legend("Tabela de receitas")], width=6),
        dbc.Col([
            dbc.Button("Deletar Selecionados", id="btn-deletar-receitas", color="danger", size="sm", className="float-end me-2"),
            dbc.Button("Salvar Alterações", id="btn-salvar-receitas", color="success", size="sm", className="float-end")
        ], width=6),
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
        dbc.Col([html.Legend("Tabela de despesas")], width=6),
        dbc.Col([
            dbc.Button("Deletar Selecionados", id="btn-deletar-despesas", color="danger", size="sm", className="float-end me-2"),
            dbc.Button("Salvar Alterações", id="btn-salvar-despesas", color="success", size="sm", className="float-end")
        ], width=6),
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
                {"name": "Forma Pagto", "id": "forma_pagamento", "presentation": "dropdown"},
                {"name": "Cartão", "id": "cartao_id", "presentation": "dropdown"},
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
                },
                'forma_pagamento': {
                    'options': [
                        {'label': '💵 Dinheiro', 'value': 'dinheiro'},
                        {'label': '💳 Cartão', 'value': 'cartao'}
                    ]
                },
                'cartao_id': {
                    'options': []  # Será preenchido dinamicamente
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
            dbc.Card(
                dcc.Graph(id='bar-graph', style={"height": "340px"}),
                style={"padding": "10px", "height": "360px"},
                className="extratos-resumo-card"
            )
        ], width=9),

        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H4("Despesas"),
                    html.Legend("R$ -", id="valor_despesa_card", style={'font-size': '60px'}),
                    html.H6("Total de despesas"),
                ], style={'text-align': 'center', 'padding-top': '30px'}),
                style={"height": "360px"},
                className="extratos-resumo-card"
            )
        ], width=3),
    ], className="mt-4 equal-height-row extratos-resumo-row"),
    
    # Modal para selecionar cartão
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Selecionar Cartão")),
        dbc.ModalBody([
            html.P("Esta despesa foi paga com cartão de crédito. Selecione qual cartão:"),
            dbc.Select(id="select-cartao-extratos", options=[], placeholder="Selecione um cartão"),
            html.Div(id="feedback-cartao-extratos", className="mt-2")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-cartao-extratos", color="secondary"),
            dbc.Button("Confirmar", id="btn-confirmar-cartao-extratos", color="primary")
        ])
    ], id="modal-cartao-extratos", is_open=False),
    
    # Store para linha sendo editada
    dcc.Store(id="store-linha-editada-despesa", data=None),
    
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
    
    # Adiciona forma_pagamento e cartao_id para despesas
    if 'forma_pagamento' in row:
        forma_pag = row.get('forma_pagamento', 'dinheiro')
        result["forma_pagamento"] = forma_pag if forma_pag and forma_pag != '-' else 'dinheiro'
        
        # Se for cartão, salva o cartao_id
        if forma_pag == 'cartao' and 'cartao_id' in row:
            cartao_id = row.get('cartao_id')
            if cartao_id and str(cartao_id).strip() and cartao_id != '-':
                try:
                    result["cartao_id"] = int(cartao_id)
                    
                    # Calcular fatura_mes e fatura_ano baseado na Data
                    if result.get("Data"):
                        from datetime import datetime
                        data = result["Data"]
                        if isinstance(data, str):
                            data_obj = datetime.strptime(data, "%Y-%m-%d")
                            result["fatura_mes"] = data_obj.month
                            result["fatura_ano"] = data_obj.year
                            print(f"[EXTRATOS] Calculado fatura_mes={result['fatura_mes']}, fatura_ano={result['fatura_ano']} da Data={data}")
                except (ValueError, TypeError):
                    result["cartao_id"] = None
            else:
                result["cartao_id"] = None
        else:
            result["cartao_id"] = None
    
    print(f"[EXTRATOS] _normalize_row resultado: {result}")
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
     Input('date-picker-extratos', 'end_date'),
     Input('store-user', 'data')]
)
def atualizar_dados_despesas(data, start_date, end_date, user):
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["id", "Valor", "Status", "Fixo", "Data", "Categoria", "Descrição", "user_id", "forma_pagamento", "cartao_id"])
    
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
    
    # Forma de pagamento (padrão: dinheiro para registros antigos)
    if 'forma_pagamento' not in df.columns:
        df['forma_pagamento'] = 'dinheiro'
    df['forma_pagamento'] = df['forma_pagamento'].fillna('dinheiro')
    
    # Manter cartao_id como está (será usado para edição)
    if 'cartao_id' not in df.columns:
        df['cartao_id'] = None
    
    # Limpar cartao_id se Status não é "Pago" (garantir consistência)
    if 'Status' in df.columns and 'cartao_id' in df.columns:
        df.loc[df['Status'] != StatusDespesa.PAGO, 'cartao_id'] = None
        df.loc[df['Status'] != StatusDespesa.PAGO, 'forma_pagamento'] = 'dinheiro'
    
    # Converter para string vazia se for None/NaN para exibir no DataTable
    df['cartao_id'] = df['cartao_id'].apply(lambda x: int(x) if pd.notna(x) and x else '')

    df = df.fillna('-')
    # Remove colunas desnecessárias mas MANTÉM cartao_id
    df = df.drop(columns=[c for c in ["user_id", "Efetuado"] if c in df.columns])
    df = df.sort_values(by='Data', ascending=True)

    return df.to_dict('records')

# Rastrear remoções de linhas na tabela de receitas
@app.callback(
    Output('deleted-receitas-ids', 'data'),
    Input('datatable-receitas', 'data'),
    State('datatable-receitas', 'data_previous'),
    State('deleted-receitas-ids', 'data'),
    prevent_initial_call=True
)
def track_receitas_deletions(current_data, previous_data, deleted_ids):
    if previous_data is None or current_data is None:
        return deleted_ids or []
    
    # Extrair IDs atuais e anteriores
    current_ids = set()
    for r in current_data:
        if r.get('id') is not None and str(r.get('id')).strip():
            try:
                current_ids.add(int(r['id']))
            except (ValueError, TypeError):
                pass
    
    previous_ids = set()
    for r in previous_data:
        if r.get('id') is not None and str(r.get('id')).strip():
            try:
                previous_ids.add(int(r['id']))
            except (ValueError, TypeError):
                pass
    
    # Detectar remoções (cliques no X)
    removed = previous_ids - current_ids
    if removed:
        deleted_list = deleted_ids or []
        for rid in removed:
            if rid not in deleted_list:
                deleted_list.append(rid)
        return deleted_list
    
    return deleted_ids or []

# Processar deleções de receitas
@app.callback(
    Output('store-refresh-receitas', 'data', allow_duplicate=True),
    Output('msg-receitas', 'children', allow_duplicate=True),
    Output('deleted-receitas-ids', 'data', allow_duplicate=True),
    Input('btn-deletar-receitas', 'n_clicks'),
    State('deleted-receitas-ids', 'data'),
    State('store-user', 'data'),
    State('store-refresh-receitas', 'data'),
    prevent_initial_call=True
)
def deletar_receitas(n_clicks, deleted_ids, user, refresh):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000), dash.no_update
    if not deleted_ids:
        return dash.no_update, dbc.Alert("Nenhuma linha selecionada para deletar", color="warning", duration=3000), dash.no_update
    
    deletados = 0
    for rid in deleted_ids:
        try:
            delete_transacao('receitas', rid, user['id'])
            deletados += 1
        except Exception as e:
            print(f"Erro ao deletar receita {rid}: {e}")
    
    if deletados > 0:
        return (refresh or 0) + 1, dbc.Alert(f"✓ {deletados} receita(s) deletada(s)", color="success", duration=4000), []
    else:
        return dash.no_update, dbc.Alert("Erro ao deletar receitas", color="danger", duration=3000), dash.no_update

# Sync receitas (update/delete)
@app.callback(
    Output('store-refresh-receitas', 'data', allow_duplicate=True),
    Output('msg-receitas', 'children'),
    Output('deleted-receitas-ids', 'data', allow_duplicate=True),
    Input('btn-salvar-receitas', 'n_clicks'),
    State('datatable-receitas', 'data'),
    State('deleted-receitas-ids', 'data'),
    State('store-receitas', 'data'),
    State('store-user', 'data'),
    State('store-refresh-receitas', 'data'),
    prevent_initial_call=True
)
def sync_receitas(n_clicks, current_data, deleted_ids, all_data, user, refresh):
    if not n_clicks:
        return dash.no_update, "", dash.no_update
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000), dash.no_update
    if not current_data:
        return dash.no_update, dbc.Alert("Sem dados para salvar", color="warning", duration=3000), dash.no_update
    
    # Mapear TODOS os registros do store (fonte de verdade)
    all_records = {}
    if all_data:
        for r in all_data:
            try:
                if r.get('id') is not None and str(r.get('id')).strip():
                    all_records[int(r['id'])] = r
            except (ValueError, TypeError):
                continue
    
    deletados = 0
    atualizados = 0
    
    # Processar atualizações comparando tabela atual com store
    if current_data:
        for row in current_data:
            try:
                if row.get('id') is not None and str(row.get('id')).strip():
                    rid = int(row['id'])
                    if rid in all_records:
                        new_row = _normalize_row(row)
                        old_row = _normalize_row(all_records[rid])
                        if new_row != old_row:
                            update_transacao('receitas', rid, new_row, user['id'])
                            atualizados += 1
            except (ValueError, TypeError):
                continue
    
    if atualizados > 0 or deletados > 0:
        msg_parts = []
        if atualizados > 0:
            msg_parts.append(f"{atualizados} receita(s) atualizada(s)")
        if deletados > 0:
            msg_parts.append(f"{deletados} receita(s) deletada(s)")
        mensagem = ", ".join(msg_parts)
        return (refresh or 0) + 1, dbc.Alert(f"✓ {mensagem}", color="success", duration=4000), []
    else:
        return dash.no_update, dbc.Alert("Nenhuma alteração detectada", color="info", duration=3000), dash.no_update

# Rastrear remoções de linhas na tabela de despesas
@app.callback(
    Output('deleted-despesas-ids', 'data'),
    Input('datatable-despesas', 'data'),
    State('datatable-despesas', 'data_previous'),
    State('deleted-despesas-ids', 'data'),
    prevent_initial_call=True
)
def track_despesas_deletions(current_data, previous_data, deleted_ids):
    if previous_data is None or current_data is None:
        return deleted_ids or []
    
    # Extrair IDs atuais e anteriores
    current_ids = set()
    for r in current_data:
        if r.get('id') is not None and str(r.get('id')).strip():
            try:
                current_ids.add(int(r['id']))
            except (ValueError, TypeError):
                pass
    
    previous_ids = set()
    for r in previous_data:
        if r.get('id') is not None and str(r.get('id')).strip():
            try:
                previous_ids.add(int(r['id']))
            except (ValueError, TypeError):
                pass
    
    # Detectar remoções (cliques no X)
    removed = previous_ids - current_ids
    if removed:
        deleted_list = deleted_ids or []
        for rid in removed:
            if rid not in deleted_list:
                deleted_list.append(rid)
        return deleted_list
    
    return deleted_ids or []

# Processar deleções de despesas
@app.callback(
    Output('store-refresh-despesas', 'data', allow_duplicate=True),
    Output('msg-despesas', 'children', allow_duplicate=True),
    Output('deleted-despesas-ids', 'data', allow_duplicate=True),
    Input('btn-deletar-despesas', 'n_clicks'),
    State('deleted-despesas-ids', 'data'),
    State('store-user', 'data'),
    State('store-refresh-despesas', 'data'),
    prevent_initial_call=True
)
def deletar_despesas(n_clicks, deleted_ids, user, refresh):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000), dash.no_update
    if not deleted_ids:
        return dash.no_update, dbc.Alert("Nenhuma linha selecionada para deletar", color="warning", duration=3000), dash.no_update
    
    deletados = 0
    for rid in deleted_ids:
        try:
            delete_transacao('despesas', rid, user['id'])
            deletados += 1
        except Exception as e:
            print(f"Erro ao deletar despesa {rid}: {e}")
    
    if deletados > 0:
        return (refresh or 0) + 1, dbc.Alert(f"✓ {deletados} despesa(s) deletada(s)", color="success", duration=4000), []
    else:
        return dash.no_update, dbc.Alert("Erro ao deletar despesas", color="danger", duration=3000), dash.no_update

# Sync despesas (update/delete)
@app.callback(
    Output('store-refresh-despesas', 'data', allow_duplicate=True),
    Output('msg-despesas', 'children'),
    Output('deleted-despesas-ids', 'data', allow_duplicate=True),
    Input('btn-salvar-despesas', 'n_clicks'),
    State('datatable-despesas', 'data'),
    State('deleted-despesas-ids', 'data'),
    State('store-despesas', 'data'),
    State('store-user', 'data'),
    State('store-refresh-despesas', 'data'),
    prevent_initial_call=True
)
def sync_despesas(n_clicks, current_data, deleted_ids, all_data, user, refresh):
    if not n_clicks:
        return dash.no_update, "", dash.no_update
    if not user or 'id' not in user:
        return dash.no_update, dbc.Alert("Usuário não autenticado", color="danger", duration=3000), dash.no_update
    if not current_data:
        return dash.no_update, dbc.Alert("Sem dados para salvar", color="warning", duration=3000), dash.no_update
    
    # Mapear TODOS os registros do store (fonte de verdade)
    all_records = {}
    if all_data:
        for r in all_data:
            try:
                if r.get('id') is not None and str(r.get('id')).strip():
                    all_records[int(r['id'])] = r
            except (ValueError, TypeError):
                continue
    
    deletados = 0
    atualizados = 0
    
    # Processar atualizações comparando tabela atual com store
    if current_data:
        for row in current_data:
            try:
                if row.get('id') is not None and str(row.get('id')).strip():
                    rid = int(row['id'])
                    if rid in all_records:
                        new_row = _normalize_row(row)
                        old_row = _normalize_row(all_records[rid])
                        if new_row != old_row:
                            update_transacao('despesas', rid, new_row, user['id'])
                            atualizados += 1
            except (ValueError, TypeError):
                continue
    
    if atualizados > 0 or deletados > 0:
        msg_parts = []
        if atualizados > 0:
            msg_parts.append(f"{atualizados} despesa(s) atualizada(s)")
        if deletados > 0:
            msg_parts.append(f"{deletados} despesa(s) deletada(s)")
        mensagem = ", ".join(msg_parts)
        return (refresh or 0) + 1, dbc.Alert(f"✓ {mensagem}", color="success", duration=4000), []
    else:
        return dash.no_update, dbc.Alert("Nenhuma alteração detectada", color="info", duration=3000), dash.no_update

# Bar Graph# Bar Graph            
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


# Atualizar dropdown de cartões na tabela de despesas
@app.callback(
    Output('datatable-despesas', 'dropdown'),
    [Input('store-user', 'data'),
     Input('store-despesas', 'data')]
)
def update_cartoes_dropdown(user, despesas_data):
    from constants import StatusDespesa, FIXO_SIM, FIXO_NAO
    
    # Dropdown base
    dropdown_base = {
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
        },
        'forma_pagamento': {
            'options': [
                {'label': '💵 Dinheiro', 'value': 'dinheiro'},
                {'label': '💳 Cartão', 'value': 'cartao'}
            ]
        },
        'cartao_id': {'options': [{'label': '-', 'value': ''}]}
    }
    
    if not user or 'id' not in user:
        return dropdown_base
    
    try:
        from db import get_cartoes
        cartoes = get_cartoes(user['id'])
        
        if cartoes:
            cartoes_options = [{'label': c['nome'], 'value': c['id']} for c in cartoes if c.get('ativo', 1)]
            # Adicionar opção vazia no início
            cartoes_options.insert(0, {'label': '-', 'value': ''})
            dropdown_base['cartao_id']['options'] = cartoes_options
            
            print(f"[EXTRATOS] Dropdown atualizado com {len(cartoes_options)} opções de cartão")
        
        return dropdown_base
    except Exception as e:
        print(f"[EXTRATOS] Erro ao atualizar dropdown de cartões: {e}")
        import traceback
        traceback.print_exc()
        return dropdown_base
