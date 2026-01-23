import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from app import app
from db import get_all_users, delete_user, change_user_admin_status

# =========  Layout  =========== #
layout = dbc.Col([
    dbc.Row([
        dbc.Col([
            html.H3("🔐 Painel de Administração", className="text-primary"),
            html.P("Gerenciamento de usuários do sistema", className="text-muted"),
            html.Hr(),
        ])
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("👥 Usuários do Sistema", className="mb-0")),
                dbc.CardBody([
                    html.Div(id="admin-users-table"),
                    html.Div(id="admin-message", className="mt-3"),
                ])
            ])
        ], width=12)
    ]),
    
    # Modal de confirmação para deletar usuário
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirmar Exclusão")),
        dbc.ModalBody([
            html.P(id="confirm-delete-text", className="mb-0"),
            html.P("Esta ação NÃO pode ser desfeita. Todos os dados do usuário (receitas, despesas e categorias) serão permanentemente deletados.", 
                   className="text-danger mt-2 mb-0", style={"font-weight": "bold"})
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="cancel-delete-user", color="secondary", className="me-2"),
            dbc.Button("Confirmar Exclusão", id="confirm-delete-user", color="danger"),
        ])
    ], id="modal-confirm-delete", is_open=False, centered=True),
    
    dcc.Store(id="store-user-to-delete", data=None),
    
], style={"padding": "20px"})


# =========  Callbacks  =========== #

@app.callback(
    Output("admin-users-table", "children"),
    Input("store-user", "data"),
    Input("admin-message", "children")  # Recarrega após operações
)
def load_users_table(current_user, _):
    """Carrega a tabela de usuários."""
    if not current_user or not current_user.get('is_admin'):
        return dbc.Alert("⛔ Acesso negado. Apenas administradores podem acessar esta página.", color="danger")
    
    users = get_all_users()
    
    if not users:
        return dbc.Alert("Nenhum usuário encontrado no sistema.", color="info")
    
    # Cria tabela com informações dos usuários
    table_data = []
    for user in users:
        admin_badge = "✓ Admin" if user['is_admin'] else ""
        is_current = " (você)" if user['id'] == current_user['id'] else ""
        
        table_data.append({
            'ID': user['id'],
            'Usuário': f"{user['username']}{is_current}",
            'Tipo': admin_badge if admin_badge else "Usuário",
            'Ações': user['id']  # Usado para identificar qual botão foi clicado
        })
    
    df = pd.DataFrame(table_data)
    
    # Cria linhas da tabela manualmente para adicionar botões
    table_rows = []
    
    # Cabeçalho
    table_rows.append(html.Tr([
        html.Th("ID", style={'width': '10%'}),
        html.Th("Usuário", style={'width': '35%'}),
        html.Th("Tipo", style={'width': '20%'}),
        html.Th("Ações", style={'width': '35%'}),
    ]))
    
    # Linhas de dados
    for _, row in df.iterrows():
        user_id = row['Ações']
        is_current_user = user_id == current_user['id']
        
        # Botões de ação
        action_buttons = []
        
        # Não permite deletar a si mesmo
        if not is_current_user:
            action_buttons.append(
                dbc.Button(
                    "🗑️ Deletar",
                    id={'type': 'delete-user-btn', 'index': user_id},
                    color="danger",
                    size="sm",
                    className="me-2"
                )
            )
        
        table_rows.append(html.Tr([
            html.Td(row['ID']),
            html.Td(row['Usuário']),
            html.Td(row['Tipo']),
            html.Td(action_buttons if action_buttons else "—"),
        ]))
    
    return dbc.Table(
        children=table_rows,
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        className="mt-3"
    )


@app.callback(
    Output("modal-confirm-delete", "is_open"),
    Output("store-user-to-delete", "data"),
    Output("confirm-delete-text", "children"),
    Input({'type': 'delete-user-btn', 'index': ALL}, 'n_clicks'),
    Input("cancel-delete-user", "n_clicks"),
    Input("confirm-delete-user", "n_clicks"),
    State("modal-confirm-delete", "is_open"),
    State("store-user-to-delete", "data"),
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, cancel_clicks, confirm_clicks, is_open, stored_user_id):
    """Controla o modal de confirmação de exclusão."""
    from dash import callback_context
    
    if not callback_context.triggered:
        return False, None, ""
    
    trigger_id = callback_context.triggered[0]['prop_id']
    
    # Se clicou em deletar
    if 'delete-user-btn' in trigger_id:
        # Encontra qual botão foi clicado
        for i, clicks in enumerate(delete_clicks):
            if clicks:
                import json
                prop_id = callback_context.triggered[0]['prop_id']
                user_id = json.loads(prop_id.split('.')[0])['index']
                
                # Busca informações do usuário
                users = get_all_users()
                user = next((u for u in users if u['id'] == user_id), None)
                
                if user:
                    confirm_text = f"Tem certeza que deseja deletar o usuário '{user['username']}' (ID: {user_id})?"
                    return True, user_id, confirm_text
        
        return False, None, ""
    
    # Se clicou em cancelar
    if "cancel-delete-user" in trigger_id:
        return False, None, ""
    
    # Se clicou em confirmar (não fecha o modal aqui, deixa o callback de delete fazer isso)
    return is_open, stored_user_id, ""


@app.callback(
    Output("admin-message", "children"),
    Output("modal-confirm-delete", "is_open", allow_duplicate=True),
    Input("confirm-delete-user", "n_clicks"),
    State("store-user-to-delete", "data"),
    State("store-user", "data"),
    prevent_initial_call=True
)
def perform_delete_user(confirm_clicks, user_id_to_delete, current_user):
    """Executa a exclusão do usuário."""
    if not confirm_clicks or not user_id_to_delete:
        return "", False
    
    if not current_user or not current_user.get('is_admin'):
        return dbc.Alert("⛔ Acesso negado. Apenas administradores podem deletar usuários.", color="danger", duration=4000), False
    
    # Não permite deletar a si mesmo
    if user_id_to_delete == current_user['id']:
        return dbc.Alert("⛔ Você não pode deletar sua própria conta.", color="warning", duration=4000), False
    
    try:
        # Busca informações do usuário antes de deletar
        users = get_all_users()
        user = next((u for u in users if u['id'] == user_id_to_delete), None)
        
        if not user:
            return dbc.Alert("❌ Usuário não encontrado.", color="warning", duration=4000), False
        
        username = user['username']
        
        # Deleta o usuário
        delete_user(user_id_to_delete)
        
        return dbc.Alert(f"✅ Usuário '{username}' (ID: {user_id_to_delete}) foi deletado com sucesso!", color="success", duration=5000), False
        
    except Exception as e:
        return dbc.Alert(f"❌ Erro ao deletar usuário: {str(e)}", color="danger", duration=5000), False
