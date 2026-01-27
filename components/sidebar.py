# Standard library imports
import json
import os
from datetime import date, datetime

# Third party imports
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import ThemeChangerAIO

# Local imports
from app import app
from constants import (
    DEFAULT_AVATAR, TABLE_MIN_YEAR, TABLE_MAX_YEAR,
    StatusDespesa, COLOR_SUCCESS, COLOR_DANGER, COLOR_INFO
)
from db import (
    delete_cat, get_user_profile_photo, insert_cat,
    insert_transacao, table_to_df, update_user_profile_photo
)
from globals import cat_despesa, cat_receita


# ========= Layout ========= #
layout = dbc.Col([
                html.H1("FINANCE APP", className="text-primary"),
                html.P("By Jônathan", className="text-info"),
                html.Hr(),


    # Seção PERFIL ------------------------
                dbc.Button(id='botao_avatar',
                    children=[html.Img(src="/assets/img_hom.png", id="avatar_change", alt="Avatar", className='perfil_avatar'),
                ], style={'background-color': 'transparent', 'border-color': 'transparent'}),

                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Selecionar Perfil")),
                    dbc.ModalBody([
                        dbc.Row([
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardImg(id="preview-upload-perfil", src="/assets/img_hom.png", className='perfil_avatar', top=True),
                                    dbc.CardBody([
                                        html.H4("Foto Personalizada", className="card-title"),
                                        dcc.Upload(
                                            id='upload-perfil',
                                            children=dbc.Button("Escolher Foto", color="info", style={"width": "100%"}),
                                            multiple=False,
                                            accept='image/*'
                                        ),
                                        html.Div(id='output-upload-status', style={'margin-top': '10px', 'font-size': '12px'}),
                                        dbc.Button("Salvar Foto", color="success", id="btn-perfil-customizado", style={'margin-top': '10px', 'width': '100%'}),
                                    ]),
                                ]),
                            ], width=6),
                            
                        ], style={"padding": "5px"}),                        
                    ]),
                ],
                style={"background-color": "rgba(0, 0, 0, 0.5)"},
                id="modal-perfil",
                size="lg",
                is_open=False,
                centered=True,
                backdrop=True
                ),  

    # Seção NOVO ------------------------
                dbc.Row([
                    dbc.Col([
                        dbc.Button(color="success", id="open-novo-receita",
                                children=["+ Receita"], className="w-100"),
                    ], xs=6, sm=6, md=6),

                    dbc.Col([
                        dbc.Button(color="danger", id="open-novo-despesa",
                                children=["- Despesa"], className="w-100"),
                    ], xs=6, sm=6, md=6)
                ], className="mb-3"),


                # Modal Receita            
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Adicionar receita")),
                    dbc.ModalBody([
                        dbc.Row([
                            dbc.Col([
                                    dbc.Label("Descrição: "),
                                    dbc.Input(placeholder="Ex.: dividendos da bolsa, herança...", id="txt-receita"),
                            ], width=6), 
                            dbc.Col([
                                    dbc.Label("Valor: "),
                                    dbc.Input(placeholder="$100.00", id="valor_receita", value="")
                            ], width=6)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Data: "),
                                dcc.DatePickerSingle(id='date-receitas',
                                    min_date_allowed=date(2020, 1, 1),
                                    max_date_allowed=date(2030, 12, 31),
                                    date=datetime.today(),
                                    style={"width": "100%"}
                                ),
                            ], width=4),

                            dbc.Col([
                                dbc.Label("Extras", className="mb-2"),
                                dbc.Checklist(
                                    options=[{"label": "Foi recebida", "value": 1},
                                        {"label": "Receita Recorrente", "value": 2}],
                                    value=[1],
                                    id="switches-input-receita",
                                    switch=True),
                            ], width=4),

                            dbc.Col([
                                html.Label("Categoria da receita"),
                                dbc.Select(id="select_receita", 
                                    options=[{"label": i, "value": i} for i in cat_receita], 
                                    value=cat_receita[0] if cat_receita else None)
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Destinar para Plano (opcional)"),
                                dcc.Dropdown(id="select_plano_receita", 
                                    placeholder="Nenhum (receita geral)",
                                    clearable=True)
                            ], width=4)
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Accordion([
                                    dbc.AccordionItem(children=[
                                            dbc.Row([
                                                dbc.Col([
                                                    html.Legend("Adicionar categoria", style={'color': 'green'}),
                                                    dbc.Input(type="text", placeholder="Nova categoria...", id="input-add-receita", value="", className="mb-2"),
                                                    dbc.Button("Adicionar", className="btn btn-success", id="add-category-receita"),
                                                    html.Div(id="category-div-add-receita", className="mt-2"),
                                                ], width=6),

                                                dbc.Col([
                                                    html.Legend("Excluir categorias", style={'color': 'red'}),
                                                    dbc.Checklist(
                                                        id="checklist-selected-style-receita",
                                                        options=[{"label": i, "value": i} for i in cat_receita],
                                                        value=[],
                                                        label_checked_style={"color": "red"},
                                                        input_checked_style={"backgroundColor": "#fa7268",
                                                            "borderColor": "#ea6258"},
                                                        className="mb-2"
                                                    ),                                                            
                                                    dbc.Button("Remover", color="warning", id="remove-category-receita"),
                                                ], width=6)
                                            ], className="g-3"),
                                        ], title="Adicionar/Remover Categorias",
                                    ),
                                ], flush=True, start_collapsed=True, id='accordion-receita'),
                                    
                                    html.Div(id="id_teste_receita", className="mt-3"),
                                
                                    dbc.ModalFooter([
                                        dbc.Button("Adicionar Receita", id="salvar_receita", color="success"),
                                        dbc.Popover(dbc.PopoverBody("Receita Salva"), target="salvar_receita", placement="left", trigger="click"),
                                        ])
                            ], className="mt-3"),
                        ])
                ],
                style={"background-color": "rgba(17, 140, 79, 0.05)"},
                id="modal-novo-receita",
                size="lg",
                is_open=False,
                centered=True,
                backdrop=True),


                ### Modal Despesa ###
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Adicionar despesa")),
                    dbc.ModalBody([
                        dbc.Row([
                            dbc.Col([
                                    dbc.Label("Descrição: "),
                                    dbc.Input(placeholder="Ex.: Gasolina, Energia, Agua...", id="txt-despesa", className = "card"),
                            ], width=6), 
                            dbc.Col([
                                    dbc.Label("Valor: "),
                                    dbc.Input(placeholder="$100.00", id="valor_despesa", value="", className = "card")
                            ], width=6)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Data: "),
                                dcc.DatePickerSingle(id='date-despesas',
                                    min_date_allowed=date(2020, 1, 1),
                                    max_date_allowed=date(2030, 12, 31),
                                    date=datetime.today(),
                                    style={"width": "100%"}
                                ),
                            ], width=4),

                            dbc.Col([
                                dbc.Label("Status", className="mb-2"),
                                dbc.Select(
                                    id="select-status-despesa",
                                    options=[
                                        {"label": "Pago", "value": "Pago"},
                                        {"label": "A vencer", "value": "A vencer"},
                                        {"label": "Vencido", "value": "Vencido"}
                                    ],
                                    value="A vencer",
                                    className="mb-2"
                                ),
                                dbc.FormText("Despesa Recorrente?"),
                                dbc.Checklist(
                                    options=[{"label": "Sim", "value": 2}],
                                    value=[],
                                    id="switches-input-despesa",
                                    switch=True),
                            ], width=4),

                            dbc.Col([
                                html.Label("Categoria da despesa"),
                                dbc.Select(id="select_despesa", 
                                    options=[{"label": i, "value": i} for i in cat_despesa],
                                    value=cat_despesa[0] if cat_despesa else None)
                            ], width=4)
                        ]),
                        
                        dbc.Row([
                            dbc.Accordion([
                                    dbc.AccordionItem(children=[
                                        dbc.Row([
                                            dbc.Col([
                                                html.Legend("Adicionar categoria", style={'color': 'green'}),
                                                dbc.Input(type="text", placeholder="Nova categoria...", id="input-add-despesa", value="", className="mb-2"),
                                                dbc.Button("Adicionar", className="btn btn-success", id="add-category-despesa"),
                                                html.Div(id="category-div-add-despesa", className="mt-2"),
                                            ], width=6),

                                            dbc.Col([
                                                html.Legend("Excluir categorias", style={'color': 'red'}),
                                                dbc.Checklist(
                                                    id="checklist-selected-style-despesa",
                                                    options=[{"label": i, "value": i} for i in cat_despesa],
                                                    value=[],
                                                    label_checked_style={"color": "red"},
                                                    input_checked_style={"backgroundColor": "#fa7268",
                                                        "borderColor": "#ea6258"},
                                                    className="mb-2"
                                                ),                                                            
                                                dbc.Button("Remover", color="warning", id="remove-category-despesa"),
                                            ], width=6)
                                        ], className="g-3"),
                                    ], title="Adicionar/Remover Categorias",
                                    ),
                                ], flush=True, start_collapsed=True, id='accordion-despesa'),
                                                        
                            dbc.ModalFooter([
                                dbc.Button("Adicionar despesa", color="error", id="salvar_despesa", value="despesa"),
                                dbc.Popover(dbc.PopoverBody("Despesa Salva"), target="salvar_despesa", placement="left", trigger="click"),
                            ]
                            )
                        ], className="mt-3"),
                    ])
                ],
                style={"background-color": "rgba(17, 140, 79, 0.05)"},
                id="modal-novo-despesa",
                size="lg",
                is_open=False,
                centered=True,
                backdrop=True),
            
# Seção NAV ------------------------
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Dashboard", href="/dashboards", active="exact"),
                    dbc.NavLink("Extratos", href="/extratos", active="exact"),
                    dbc.NavLink("Planos e Metas", href="/planos", active="exact"),
                ], vertical=True, pills=True, id='nav_buttons', style={"margin-bottom": "10px"}),
            
            # Link Admin (condicional - será exibido apenas para admins via callback)
            html.Div(id="admin-nav-link"),
            
            dbc.Button(
                "Logout",
                id="logout-button",
                color="secondary",
                outline=True,
                className="w-100",
                style={"margin-top": "10px"}
            ),
            ThemeChangerAIO(aio_id="theme", radio_props={"value":dbc.themes.CYBORG})


        ], id='sidebar_completa'
    )

# =========  Callbacks  =========== #
# Mostrar link de Admin apenas para administradores
@app.callback(
    Output('admin-nav-link', 'children'),
    Input('store-user', 'data')
)
def show_admin_link(user):
    if user and user.get('is_admin'):
        return dbc.Nav([
            dbc.NavLink("🔐 Admin", href="/admin", active="exact", style={"color": "#ff9800", "font-weight": "bold"}),
        ], vertical=True, pills=True, style={"margin-bottom": "10px"})
    return html.Div()

# Logout
@app.callback(
    Output('store-user', 'data', allow_duplicate=True),
    Output('url', 'pathname', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def do_logout(n_clicks):
    if n_clicks:
        return None, '/login'
    return dash.no_update, dash.no_update

# Carregar planos no dropdown de receita
@app.callback(
    Output("select_plano_receita", "options"),
    Input("store-user", "data")
)
def load_planos_receita(user):
    if not user or 'id' not in user:
        return []
    
    from db import get_planos_by_user
    planos = get_planos_by_user(user['id'])
    return [{"label": plano['nome'], "value": plano['id']} for plano in planos]

# Pop-up receita
@app.callback(
    Output("modal-novo-receita", "is_open"),
    Input("open-novo-receita", "n_clicks"),
    State("modal-novo-receita", "is_open")
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open

# Pop-up despesa
@app.callback(
    Output("modal-novo-despesa", "is_open"),
    Input("open-novo-despesa", "n_clicks"),
    State("modal-novo-despesa", "is_open")
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open

# Pop-up perfis
@app.callback(
    Output("modal-perfil", "is_open"),
    Input("botao_avatar", "n_clicks"),
    State("modal-perfil", "is_open")
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open

# Preview da imagem de perfil
@app.callback(
    Output('preview-upload-perfil', 'src'),
    Output('output-upload-status', 'children'),
    Input('upload-perfil', 'contents'),
    State('upload-perfil', 'filename'),
    prevent_initial_call=True
)
def update_preview(contents, filename):
    if contents is not None:
        return contents, html.P(f"✓ {filename}", style={'color': 'green'})
    return dash.no_update, ""

# Salvar perfil customizado
@app.callback(
    Output('avatar_change', 'src'),
    Output('modal-perfil', 'is_open', allow_duplicate=True),
    Input('btn-perfil-customizado', 'n_clicks'),
    State('preview-upload-perfil', 'src'),
    State('store-user', 'data'),
    prevent_initial_call=True
)
def save_perfil(n_custom, custom_src, user):
    if n_custom and custom_src and custom_src.startswith('data:image'):
        if user and 'id' in user:
            user_id = user['id']
            update_user_profile_photo(user_id, custom_src)
            return custom_src, False
    return dash.no_update, dash.no_update

# Carregar avatar salvo quando o usuário faz login
@app.callback(
    Output('avatar_change', 'src', allow_duplicate=True),
    Output('preview-upload-perfil', 'src', allow_duplicate=True),
    Input('store-user', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_saved_avatar(user):
    if user and 'id' in user:
        photo_src = get_user_profile_photo(user['id'])
        return photo_src, photo_src
    return "/assets/img_hom.png", "/assets/img_hom.png"

# Add/Remove categoria despesa
@app.callback(
    [Output("category-div-add-despesa", "children"),
    Output("category-div-add-despesa", "style"),
    Output("select_despesa", "options"),
    Output("select_despesa", "value"),
    Output('checklist-selected-style-despesa', 'options'),
    Output('checklist-selected-style-despesa', 'value'),
    Output('store-refresh-cat-despesas', 'data')],

    [Input("add-category-despesa", "n_clicks"),
    Input("remove-category-despesa", 'n_clicks'),
    Input("modal-novo-despesa", "is_open")],

    [State("input-add-despesa", "value"),
    State('checklist-selected-style-despesa', 'value'),
    State('stored-cat-despesas', 'data'),
    State('store-user', 'data'),
    State('store-refresh-cat-despesas', 'data')]
)
def add_category_despesa(n, n2, is_open, txt, check_delete, data, user, refresh_cat_despesas):
    txt1 = []
    style1 = {}
    user_id = user['id'] if user and 'id' in user else None

    # lista atual baseada no store (que já deve ser do usuário) ou vazia
    cat_despesa = [item['Categoria'] for item in data if 'Categoria' in item] if data else []

    if n:
        if user_id is None:
            txt1 = "Faça login para adicionar categorias."
            style1 = {'color': 'red'}
        elif txt == "" or txt is None:
            txt1 = "O campo de texto não pode estar vazio para o registro de uma nova categoria."
            style1 = {'color': 'red'}
        else:
            try:
                insert_cat('cat_despesa', txt, user_id)
                txt1 = f'A categoria {txt} foi adicionada com sucesso!'
                style1 = {'color': 'green'}
            except Exception as e:
                txt1 = f'Erro ao adicionar categoria: {e}'
                style1 = {'color': 'red'}

    if n2:
        if user_id is None:
            txt1 = "Faça login para remover categorias."
            style1 = {'color': 'red'}
        elif len(check_delete) > 0:
            for c in check_delete:
                delete_cat('cat_despesa', c, user_id)

    # atualiza lista completa de categorias apenas do usuário
    if user_id is None:
        df_cat_despesa = pd.DataFrame(columns=['Categoria'])
    else:
        df_cat_despesa = table_to_df('cat_despesa', user_id=user_id)
    opt_despesa = [{"label": i, "value": i} for i in df_cat_despesa['Categoria'].tolist()]
    selected_value = opt_despesa[0]["value"] if opt_despesa else None

    data_return = df_cat_despesa.to_dict()

    # sinaliza reload apenas quando adiciona/remove categoria
    triggered_id = dash.callback_context.triggered_id
    if triggered_id in ("add-category-despesa", "remove-category-despesa"):
        new_refresh = (refresh_cat_despesas or 0) + 1
    else:
        new_refresh = refresh_cat_despesas

    return [txt1, style1, opt_despesa, selected_value, opt_despesa, [], new_refresh]

# Add/Remove categoria receita
@app.callback(
    [Output("category-div-add-receita", "children"),
    Output("category-div-add-receita", "style"),
    Output("select_receita", "options"),
    Output("select_receita", "value"),
    Output('checklist-selected-style-receita', 'options'),
    Output('checklist-selected-style-receita', 'value'),
    Output('store-refresh-cat-receitas', 'data')],

    [Input("add-category-receita", "n_clicks"),
    Input("remove-category-receita", 'n_clicks'),
    Input("modal-novo-receita", "is_open")],

    [State("input-add-receita", "value"),
    State('checklist-selected-style-receita', 'value'),
    State('stored-cat-receitas', 'data'),
    State('store-user', 'data'),
    State('store-refresh-cat-receitas', 'data')]
)
def add_category_receita(n, n2, is_open, txt, check_delete, data, user, refresh_cat_receitas):
    txt1 = []
    style1 = {}
    user_id = user['id'] if user and 'id' in user else None

    cat_receita = [item['Categoria'] for item in data if 'Categoria' in item] if data else []

    if n:
        if user_id is None:
            txt1 = "Faça login para adicionar categorias."
            style1 = {'color': 'red'}
        elif txt == "" or txt is None:
            txt1 = "O campo de texto não pode estar vazio para o registro de uma nova categoria."
            style1 = {'color': 'red'}
        else:
            try:
                insert_cat('cat_receita', txt, user_id)
                txt1 = f'A categoria {txt} foi adicionada com sucesso!'
                style1 = {'color': 'green'}
            except Exception as e:
                txt1 = f'Erro ao adicionar categoria: {e}'
                style1 = {'color': 'red'}

    if n2:
        if user_id is None:
            txt1 = "Faça login para remover categorias."
            style1 = {'color': 'red'}
        elif check_delete == []:
            pass
        else:
            for c in check_delete:
                delete_cat('cat_receita', c, user_id)

    if user_id is None:
        df_cat_receita = pd.DataFrame(columns=['Categoria'])
    else:
        df_cat_receita = table_to_df('cat_receita', user_id=user_id)
    opt_receita = [{"label": i, "value": i} for i in df_cat_receita['Categoria'].tolist()]
    selected_value = opt_receita[0]["value"] if opt_receita else None

    data_return = df_cat_receita.to_dict()

    # sinaliza reload apenas quando adiciona/remove categoria
    triggered_id = dash.callback_context.triggered_id
    if triggered_id in ("add-category-receita", "remove-category-receita"):
        new_refresh = (refresh_cat_receitas or 0) + 1
    else:
        new_refresh = refresh_cat_receitas

    return [txt1, style1, opt_receita, selected_value, opt_receita, [], new_refresh]

# Enviar Form receita
@app.callback(
    Output('store-refresh-receitas', 'data'),

    Input("salvar_receita", "n_clicks"),

    [
        State("txt-receita", "value"),
        State("valor_receita", "value"),
        State("date-receitas", "date"),
        State("switches-input-receita", "value"),
        State("select_receita", "value"),
        State("select_plano_receita", "value"),
        State('store-receitas', 'data'),
        State('store-user', 'data'),
        State('store-refresh-receitas', 'data')
    ]
)
def salve_form_receita(n, descricao, valor, date, switches, categoria, plano_id, dict_receitas, user, refresh_receitas):
    # garante colunas esperadas e insere linha de forma segura
    expected_cols = ['Valor', 'Efetuado', 'Fixo', 'Data', 'Categoria', 'Descrição', 'user_id']
    df_receitas = pd.DataFrame(dict_receitas)
    if df_receitas.empty:
        df_receitas = pd.DataFrame(columns=expected_cols)
    else:
        for c in expected_cols:
            if c not in df_receitas.columns:
                df_receitas[c] = None

    if n and not(valor == "" or valor == None):
        valor = round(float(valor), 2)
        date_iso = pd.to_datetime(date).strftime('%Y-%m-%d')
        categoria = categoria[0] if type(categoria) == list else categoria

        recebido = 1 if 1 in switches else 0
        fixo = 1 if 2 in switches else 0
        descricao = descricao if descricao not in (None, "") else 0
        user_id = user['id'] if user and 'id' in user else None

        # Insere apenas a nova transação no DB associada ao usuário
        insert_transacao('receitas', valor, recebido, fixo, date_iso, categoria, descricao, user_id, plano_id)

        # sinaliza reload para store 'store-receitas'
        return (refresh_receitas or 0) + 1

    # se nada mudou, não altera o contador
    return refresh_receitas

# Enviar Form despesa
@app.callback(
    Output('store-refresh-despesas', 'data'),

    Input("salvar_despesa", "n_clicks"),

    [
        State("txt-despesa", "value"),
        State("valor_despesa", "value"),
        State("date-despesas", "date"),
        State("switches-input-despesa", "value"),
        State("select_despesa", "value"),
        State("select-status-despesa", "value"),
        State('store-despesas', 'data'),
        State('store-user', 'data'),
        State('store-refresh-despesas', 'data')
    ])
def salve_form_despesa(n, descricao, valor, date, switches, categoria, status, dict_despesas, user, refresh_despesas):
    # garante colunas esperadas e insere linha de forma segura
    expected_cols = ['Valor', 'Status', 'Fixo', 'Data', 'Categoria', 'Descrição', 'user_id']
    df_despesas = pd.DataFrame(dict_despesas)
    if df_despesas.empty:
        df_despesas = pd.DataFrame(columns=expected_cols)
    else:
        for c in expected_cols:
            if c not in df_despesas.columns:
                df_despesas[c] = None

    if n and not(valor == "" or valor == None):
        valor = round(float(valor), 2)
        date_iso = pd.to_datetime(date).strftime('%Y-%m-%d')
        categoria = categoria[0] if type(categoria) == list else categoria

        fixo = 1 if 2 in switches else 0
        descricao = descricao if descricao not in (None, "") else 0
        user_id = user['id'] if user and 'id' in user else None

        # Insere apenas a nova transação no DB associada ao usuário (com Status)
        insert_transacao('despesas', valor, status, fixo, date_iso, categoria, descricao, user_id)

        # sinaliza reload para store 'store-despesas'
        return (refresh_despesas or 0) + 1

    # se nada mudou, não altera o contador
    return refresh_despesas