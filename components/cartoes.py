"""
Componente para gerenciamento de cartões de crédito
"""
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
from app import app
from db import get_cartoes, create_cartao, update_cartao, delete_cartao

# =========  Layout  =========== #
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("💳 Meus Cartões de Crédito", className="mb-4"),
            html.P("Gerencie seus cartões de crédito. As faturas serão geradas automaticamente.", className="text-muted")
        ])
    ]),
    
    # Botão adicionar cartão
    dbc.Row([
        dbc.Col([
            dbc.Button("+ Novo Cartão", id="btn-novo-cartao", color="primary", className="mb-3")
        ])
    ]),
    
    # Lista de cartões
    dbc.Row([
        dbc.Col([
            html.Div(id="lista-cartoes")
        ])
    ]),
    
    # Modal para adicionar/editar cartão
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Novo Cartão de Crédito")),
        dbc.ModalBody([
            dbc.Label("Nome do Cartão"),
            dbc.Input(id="input-nome-cartao", placeholder="Ex: Nubank, Inter, C6...", className="mb-3"),
            
            dbc.Label("Limite (opcional)"),
            dbc.Input(id="input-limite-cartao", type="number", placeholder="0.00", value=0, className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Dia do Fechamento"),
                    dbc.Input(id="input-dia-fechamento", type="number", min=1, max=28, value=5)
                ], md=6),
                dbc.Col([
                    dbc.Label("Dia do Vencimento"),
                    dbc.Input(id="input-dia-vencimento", type="number", min=1, max=28, value=10)
                ], md=6)
            ]),
            
            html.Div(id="feedback-cartao", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-cartao", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="btn-salvar-cartao", color="primary")
        ])
    ], id="modal-cartao", is_open=False),
    
    # Store para ID do cartão em edição
    dcc.Store(id="store-cartao-edit", data=None)
    
], fluid=True, className="p-4")


# =========  Callbacks  =========== #

@app.callback(
    Output("lista-cartoes", "children"),
    Input("store-user", "data")
)
def listar_cartoes(user):
    if not user or 'id' not in user:
        return dbc.Alert("Faça login para gerenciar seus cartões", color="warning")
    
    try:
        cartoes = get_cartoes(user['id'])
    except Exception as e:
        print(f"[CARTOES] Erro ao buscar cartões: {e}")
        return dbc.Alert([
            html.H5("Erro ao carregar cartões", className="alert-heading"),
            html.P(f"Ocorreu um erro: {str(e)}"),
            html.P("Certifique-se de que o banco de dados foi migrado corretamente.", className="text-muted")
        ], color="danger")
    
    if not cartoes:
        return dbc.Alert([
            html.H5("Nenhum cartão cadastrado", className="alert-heading"),
            html.P("Clique em 'Novo Cartão' para adicionar seu primeiro cartão de crédito.")
        ], color="info")
    
    cards = []
    for cartao in cartoes:
        if not cartao.get('ativo', 1):
            continue
            
        card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"💳 {cartao['nome']}", className="mb-2"),
                        html.P([
                            html.Strong("Limite: "),
                            f"R$ {cartao.get('limite', 0):.2f}"
                        ], className="mb-1"),
                        html.P([
                            html.Strong("Fechamento: "),
                            f"Dia {cartao.get('dia_fechamento', 5)}"
                        ], className="mb-1"),
                        html.P([
                            html.Strong("Vencimento: "),
                            f"Dia {cartao.get('dia_vencimento', 10)}"
                        ], className="mb-0")
                    ], md=9),
                    dbc.Col([
                        dbc.Button("✏️", id={"type": "btn-edit-cartao", "index": cartao['id']}, 
                                 color="warning", size="sm", className="me-2"),
                        dbc.Button("🗑️", id={"type": "btn-delete-cartao", "index": cartao['id']}, 
                                 color="danger", size="sm")
                    ], md=3, className="text-end")
                ], align="center")
            ])
        ], className="mb-3")
        
        cards.append(card)
    
    return cards


@app.callback(
    Output("modal-cartao", "is_open"),
    [Input("btn-novo-cartao", "n_clicks"),
     Input("btn-cancelar-cartao", "n_clicks"),
     Input("btn-salvar-cartao", "n_clicks")],
    [State("modal-cartao", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(n_novo, n_cancelar, n_salvar, is_open):
    return not is_open


@app.callback(
    [Output("feedback-cartao", "children"),
     Output("store-cartao-edit", "data", allow_duplicate=True)],
    Input("btn-salvar-cartao", "n_clicks"),
    [State("input-nome-cartao", "value"),
     State("input-limite-cartao", "value"),
     State("input-dia-fechamento", "value"),
     State("input-dia-vencimento", "value"),
     State("store-user", "data"),
     State("store-cartao-edit", "data")],
    prevent_initial_call=True
)
def salvar_cartao(n_clicks, nome, limite, dia_fechamento, dia_vencimento, user, cartao_id):
    if not n_clicks or not user or 'id' not in user:
        raise PreventUpdate
    
    if not nome or not nome.strip():
        return dbc.Alert("Por favor, informe o nome do cartão", color="danger"), None
    
    try:
        limite = float(limite) if limite else 0
        dia_fechamento = int(dia_fechamento) if dia_fechamento else 5
        dia_vencimento = int(dia_vencimento) if dia_vencimento else 10
        
        if cartao_id:
            # Editar cartão existente
            update_cartao(cartao_id, nome=nome, limite=limite, 
                        dia_fechamento=dia_fechamento, dia_vencimento=dia_vencimento)
            mensagem = "Cartão atualizado com sucesso!"
        else:
            # Criar novo cartão
            create_cartao(nome, user['id'], limite, dia_vencimento, dia_fechamento)
            mensagem = "Cartão criado com sucesso!"
        
        return dbc.Alert(mensagem, color="success"), None
        
    except Exception as e:
        return dbc.Alert(f"Erro ao salvar cartão: {str(e)}", color="danger"), None


@app.callback(
    Output("store-cartao-edit", "data"),
    Input({"type": "btn-delete-cartao", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True
)
def deletar_cartao_callback(n_clicks):
    """Marca cartão como inativo (soft delete)"""
    from dash import ctx
    
    if not any(n_clicks):
        raise PreventUpdate
    
    # Pegar ID do cartão que foi clicado
    button_id = ctx.triggered_id
    if button_id and 'index' in button_id:
        cartao_id = button_id['index']
        delete_cartao(cartao_id)
    
    raise PreventUpdate
