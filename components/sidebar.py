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
                html.P(id="user-info", className="text-info"),
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

    # Modal Trocar Senha ------------------------
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Trocar Senha")),
                    dbc.ModalBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Senha Atual:"),
                                dbc.Input(type="password", id="input-current-password", placeholder="Digite sua senha atual"),
                            ], width=12),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Nova Senha:"),
                                dbc.Input(type="password", id="input-new-password", placeholder="Digite a nova senha"),
                            ], width=12),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Confirmar Nova Senha:"),
                                dbc.Input(type="password", id="input-confirm-password", placeholder="Confirme a nova senha"),
                            ], width=12),
                        ], className="mb-3"),
                        html.Div(id="change-password-message", style={'margin-top': '10px'}),
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="cancel-change-password", color="secondary"),
                        dbc.Button("Salvar Nova Senha", id="save-new-password", color="success"),
                    ]),
                ],
                style={"background-color": "rgba(0, 0, 0, 0.5)"},
                id="modal-change-password",
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
                        
                        # Campo de parcelas que aparece apenas quando "Despesa Recorrente" está marcado
                        html.Div(id="parcelas-container", children=[
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Número de Parcelas"),
                                    dbc.Input(
                                        id="input-parcelas",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        placeholder="Ex: 12",
                                        value=1
                                    ),
                                    dbc.FormText("Quantas vezes essa despesa se repetirá nos próximos meses?")
                                ], width=6)
                            ], className="mb-3")
                        ], style={'display': 'none'}),  # Inicialmente escondido
                        
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
                    dbc.NavLink("Orçamentos", href="/orcamentos", active="exact"),
                    dbc.NavLink("Planos e Metas", href="/planos", active="exact"),
                ], vertical=True, pills=True, id='nav_buttons', style={"margin-bottom": "10px"}),
            
            # Link Admin (condicional - será exibido apenas para admins via callback)
            html.Div(id="admin-nav-link"),
            
            dbc.Button(
                "Trocar Senha",
                id="open-change-password",
                color="warning",
                outline=True,
                className="w-100",
                style={"margin-top": "10px"}
            ),
            
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

# Mostrar/esconder campo de parcelas quando marcar despesa recorrente
@app.callback(
    Output("parcelas-container", "style"),
    Input("switches-input-despesa", "value")
)
def toggle_parcelas_field(switches):
    if 2 in switches:  # 2 é o valor para "Despesa Recorrente"
        return {'display': 'block'}
    return {'display': 'none'}

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

# Pop-up trocar senha
@app.callback(
    Output("modal-change-password", "is_open"),
    Output("input-current-password", "value"),
    Output("input-new-password", "value"),
    Output("input-confirm-password", "value"),
    Output("change-password-message", "children"),
    Input("open-change-password", "n_clicks"),
    Input("cancel-change-password", "n_clicks"),
    Input("save-new-password", "n_clicks"),
    State("modal-change-password", "is_open"),
    State("input-current-password", "value"),
    State("input-new-password", "value"),
    State("input-confirm-password", "value"),
    State('store-user', 'data'),
    prevent_initial_call=True
)
def manage_change_password(n_open, n_cancel, n_save, is_open, current_password, new_password, confirm_password, user):
    from db import verify_user, update_user_password
    from security import validate_password_strength
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, "", "", "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Abrir modal
    if button_id == "open-change-password":
        return True, "", "", "", ""
    
    # Cancelar
    if button_id == "cancel-change-password":
        return False, "", "", "", ""
    
    # Salvar nova senha
    if button_id == "save-new-password":
        if not user or 'id' not in user or 'username' not in user:
            return True, current_password, new_password, confirm_password, dbc.Alert("Erro: usuário não autenticado", color="danger")
        
        # Validar campos preenchidos
        if not current_password or not new_password or not confirm_password:
            return True, current_password, new_password, confirm_password, dbc.Alert("Preencha todos os campos", color="warning")
        
        # Verificar senha atual
        if not verify_user(user['username'], current_password):
            return True, current_password, new_password, confirm_password, dbc.Alert("Senha atual incorreta", color="danger")
        
        # Verificar se as novas senhas coincidem
        if new_password != confirm_password:
            return True, current_password, new_password, confirm_password, dbc.Alert("As senhas não coincidem", color="warning")
        
        # Validar força da nova senha
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return True, current_password, new_password, confirm_password, dbc.Alert(message, color="warning")
        
        # Atualizar senha
        try:
            update_user_password(user['id'], new_password)
            return False, "", "", "", dbc.Alert("Senha alterada com sucesso!", color="success")
        except Exception as e:
            return True, current_password, new_password, confirm_password, dbc.Alert(f"Erro ao alterar senha: {str(e)}", color="danger")
    
    return is_open, current_password, new_password, confirm_password, ""

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
    import dash
    txt1 = []
    style1 = {}
    user_id = user['id'] if user and 'id' in user else None
    
    triggered = dash.callback_context.triggered_id
    print(f"[CALLBACK] add_category_despesa - TRIGGERED: {triggered}, n={n}, n2={n2}, txt='{txt}', user_id={user_id}, refresh_cat_despesas={refresh_cat_despesas}")

    # lista atual baseada no store (que já deve ser do usuário) ou vazia
    cat_despesa = [item['Categoria'] for item in data if 'Categoria' in item] if data else []

    if n and triggered == "add-category-despesa":
        print(f"[CALLBACK] Botão 'Adicionar' foi clicado!")
        if user_id is None:
            txt1 = "Faça login para adicionar categorias."
            style1 = {'color': 'red'}
        elif txt == "" or txt is None:
            txt1 = "O campo de texto não pode estar vazio para o registro de uma nova categoria."
            style1 = {'color': 'red'}
        else:
            try:
                print(f"[CALLBACK] Tentando inserir categoria '{txt}' para user_id={user_id}")
                insert_cat('cat_despesa', txt, user_id)
                txt1 = f'A categoria {txt} foi adicionada com sucesso!'
                style1 = {'color': 'green'}
            except Exception as e:
                print(f"[CALLBACK] Erro ao inserir categoria: {e}")
                txt1 = f'Erro ao adicionar categoria: {e}'
                style1 = {'color': 'red'}

    if n2 and triggered == "remove-category-despesa":
        print(f"[CALLBACK] Botão 'Remover' foi clicado!")
        if user_id is None:
            txt1 = "Faça login para remover categorias."
            style1 = {'color': 'red'}
        elif len(check_delete) > 0:
            for c in check_delete:
                delete_cat('cat_despesa', c, user_id)

    # atualiza lista completa de categorias apenas do usuário
    if user_id is None:
        df_cat_despesa = pd.DataFrame(columns=['Categoria'])
        print(f"[CALLBACK] user_id é None, usando DataFrame vazio")
    else:
        df_cat_despesa = table_to_df('cat_despesa', user_id=user_id)
        print(f"[CALLBACK] table_to_df retornou: shape={df_cat_despesa.shape}, columns={df_cat_despesa.columns.tolist()}, empty={df_cat_despesa.empty}")
        if not df_cat_despesa.empty:
            print(f"[CALLBACK] Primeiras linhas do DataFrame:\n{df_cat_despesa.head()}")
        
        if df_cat_despesa.empty or 'Categoria' not in df_cat_despesa.columns:
            print(f"[CALLBACK] DataFrame vazio ou sem coluna Categoria, criando vazio")
            df_cat_despesa = pd.DataFrame(columns=['Categoria'])
    
    opt_despesa = [{"label": i, "value": i} for i in df_cat_despesa['Categoria'].tolist()]
    selected_value = opt_despesa[0]["value"] if opt_despesa else None

    data_return = df_cat_despesa.to_dict()

    # sinaliza reload apenas quando adiciona/remove categoria
    triggered_id = dash.callback_context.triggered_id
    if triggered_id in ("add-category-despesa", "remove-category-despesa"):
        new_refresh = (refresh_cat_despesas or 0) + 1
    else:
        new_refresh = refresh_cat_despesas
    
    print(f"[CALLBACK] add_category_despesa - triggered_id={triggered_id}, new_refresh={new_refresh}, opt_despesa={opt_despesa}")

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
        if df_cat_receita.empty or 'Categoria' not in df_cat_receita.columns:
            df_cat_receita = pd.DataFrame(columns=['Categoria'])
    
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
        State("input-parcelas", "value"),
        State('store-despesas', 'data'),
        State('store-user', 'data'),
        State('store-refresh-despesas', 'data')
    ])
def salve_form_despesa(n, descricao, valor, date, switches, categoria, status, num_parcelas, dict_despesas, user, refresh_despesas):
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

        # Verifica se é despesa recorrente com parcelas
        if fixo == 1 and num_parcelas and int(num_parcelas) > 1:
            # Usa a função de inserção parcelada
            from db import insert_despesa_parcelada
            insert_despesa_parcelada(valor, status, fixo, date_iso, categoria, descricao, user_id, int(num_parcelas))
        else:
            # Insere apenas uma transação no DB associada ao usuário (com Status)
            insert_transacao('despesas', valor, status, fixo, date_iso, categoria, descricao, user_id)

        # sinaliza reload para store 'store-despesas'
        return (refresh_despesas or 0) + 1

    # se nada mudou, não altera o contador
    return refresh_despesas


# =========  Callback para exibir nome do usuário  =========== #
@app.callback(
    Output("user-info", "children"),
    Input('store-user', 'data')
)
def display_user_info(user):
    if user and 'username' in user:
        return f"Bem-vindo, {user['username']}"
    return "By Visitante"