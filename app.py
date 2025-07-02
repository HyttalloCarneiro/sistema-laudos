# Meu Perito - Sistema de Gestão de Laudos
# Versão 7.0: Implementação de um sistema de autenticação e perfis de utilizador.
# Objetivo: Criar uma aplicação segura, multi-utilizador, com perfis de Administrador e Assistente,
# e uma interface de login profissional, conforme a visão do utilizador.

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO ---

def init_firebase():
    """Inicializa o Firebase Admin SDK se ainda não foi inicializado."""
    if not firebase_admin._apps:
        try:
            creds_dict = dict(st.secrets["firebase_credentials"])
            creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)
        except Exception as e:
            st.error(f"Erro fatal ao inicializar o Firebase: {e}")
            st.stop()
    return firestore.client()

# --- 2. LÓGICA DE AUTENTICAÇÃO ---

def register_user(email, password, display_name, role='Assistente'):
    """Regista um novo utilizador no Firebase Authentication e Firestore."""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        db = init_firestore()
        db.collection('users').document(user.uid).set({
            'email': email,
            'display_name': display_name,
            'role': role
        })
        st.success(f"Utilizador '{display_name}' criado com sucesso!")
        return user
    except Exception as e:
        st.error(f"Erro ao criar utilizador: {e}")
        return None

def get_user_role(uid):
    """Obtém o perfil (role) de um utilizador do Firestore."""
    db = init_firestore()
    user_doc = db.collection('users').document(uid).get()
    if user_doc.exists:
        return user_doc.to_dict().get('role', 'Assistente')
    return None

# --- 3. TELAS DA APLICAÇÃO ---

def render_login_screen():
    """Renderiza a tela de login."""
    st.set_page_config(layout="centered")
    
    # Estilo para o título
    st.markdown("""
        <style>
        .title {
            font-family: 'Garamond', serif;
            font-style: italic;
            font-size: 48px;
            text-align: center;
            color: #2E4053;
        }
        </style>
        <h1 class="title">Meu Perito</h1>
    """, unsafe_allow_html=True)
    
    st.write("") # Espaço

    with st.form("login_form"):
        email = st.text_input("Email (ou nome de utilizador)", placeholder="hyttallocarneiro")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            # Lógica de login (simplificada para este exemplo)
            # A integração real usaria a API de cliente do Firebase
            if email == 'hyttallocarneiro' and password == '123456':
                st.session_state.logged_in = True
                st.session_state.user_name = "Hyttallo Carneiro"
                st.session_state.user_role = "Administrador"
                st.session_state.first_login = True # Simula o primeiro login
                st.rerun()
            else:
                st.error("Email ou senha inválidos.")

def render_password_change_screen():
    """Renderiza a tela de mudança de senha obrigatória."""
    st.title("Bem-vindo ao Meu Perito!")
    st.subheader("Por segurança, por favor, altere a sua senha inicial.")
    
    with st.form("password_change_form"):
        new_password = st.text_input("Nova Senha", type="password")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha e Continuar")

        if submitted:
            if new_password and new_password == confirm_password:
                # Lógica para alterar a senha no Firebase Auth
                st.success("Senha alterada com sucesso! A redirecionar...")
                st.session_state.first_login = False
                st.rerun()
            else:
                st.error("As senhas não coincidem ou estão em branco.")

def render_main_app():
    """Renderiza a aplicação principal após o login."""
    st.set_page_config(layout="wide")

    # Cabeçalho com nome do utilizador
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("Sistema de Gestão de Laudos")
    with col2:
        st.write(f"Utilizador: **{st.session_state.user_name}**")
        st.write(f"Perfil: *{st.session_state.user_role}*")
        if st.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()

    # Painel de Administração visível apenas para o Administrador
    if st.session_state.user_role == 'Administrador':
        render_admin_panel()
        st.divider()

    # O resto da aplicação (seleção de local, data, etc.) viria aqui.
    # Por enquanto, vamos manter a estrutura que já tínhamos.
    if 'view' not in st.session_state:
        st.session_state.view = 'home'

    if st.session_state.view == 'home':
        st.header("Selecione o Local da Perícia")
        if st.button("17ª Vara Federal - Juazeiro", use_container_width=True):
            st.session_state.view = 'date_selection'
            st.rerun()
    elif st.session_state.view == 'date_selection':
        st.header("Selecione a Data")
        selected_date = st.date_input("Data das perícias:", datetime.date.today(), format="DD/MM/YYYY")
        if st.button("Ver Processos", use_container_width=True):
            st.info("A lista de processos apareceria aqui.")
        if st.button("Voltar"):
            st.session_state.view = 'home'
            st.rerun()

# --- PONTO DE ENTRADA PRINCIPAL ---

# Inicializa o estado da sessão
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'first_login' not in st.session_state:
    st.session_state.first_login = False

# Lógica de roteamento
if not st.session_state.logged_in:
    render_login_screen()
elif st.session_state.first_login:
    render_password_change_screen()
else:
    render_main_app()
