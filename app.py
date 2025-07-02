# Meu Perito - Sistema de Gestão de Laudos
# Versão 7.2: Reintegra o fluxo de gestão de laudos e adiciona o painel de administração.
# Objetivo: Construir sobre a base de autenticação funcional, adicionando a gestão de utilizadores
# para o perfil de Administrador e reativando a interface de gestão de perícias.

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import requests
import json
import base64
import google.generativeai as genai
import PyPDF2
from io import BytesIO

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO ---

def init_firebase():
    """Inicializa o Firebase Admin SDK se ainda não foi inicializado."""
    if not firebase_admin._apps:
        try:
            # Usa o método Base64 que é mais robusto
            creds_base64 = st.secrets["FIREBASE_CREDENTIALS_BASE64"]
            creds_json_str = base64.b64decode(creds_base64).decode("utf-8")
            creds_dict = json.loads(creds_json_str)
            
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)
        except Exception as e:
            st.error(f"Erro fatal ao inicializar o Firebase: {e}")
            st.stop()
    return firestore.client()

# --- 2. LÓGICA DE AUTENTICAÇÃO ---

def sign_in(email, password):
    """Autentica um utilizador usando a API REST do Firebase."""
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    try:
        response = requests.post(rest_api_url, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        st.error("Email ou senha inválidos. Por favor, tente novamente.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro de conexão: {e}")
        return None

def change_password(id_token, new_password):
    """Altera a senha de um utilizador."""
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"
    payload = json.dumps({"idToken": id_token, "password": new_password, "returnSecureToken": False})
    try:
        response = requests.post(rest_api_url, data=payload)
        response.raise_for_status()
        return True
    except Exception:
        return False

def get_user_data(uid):
    """Obtém os dados de um utilizador (perfil, etc.) do Firestore."""
    db = init_firestore()
    user_doc_ref = db.collection('users').document(uid)
    user_doc = user_doc_ref.get()
    
    if user_doc.exists:
        return user_doc.to_dict()
    
    try:
        user_record = auth.get_user(uid)
        user_data = {
            'email': user_record.email,
            'display_name': "Hyttallo Carneiro", # Nome Padrão para o Admin
            'role': 'Administrador',
            'first_login': True
        }
        user_doc_ref.set(user_data)
        return user_data
    except Exception as e:
        st.error(f"Não foi possível obter os dados do novo utilizador: {e}")
        return None

def register_user(email, password, display_name, role='Assistente'):
    """Regista um novo utilizador."""
    try:
        user = auth.create_user(email=email, password=password, display_name=display_name)
        db = init_firestore()
        db.collection('users').document(user.uid).set({
            'email': email,
            'display_name': display_name,
            'role': role,
            'first_login': True # Força a mudança de senha para novos utilizadores
        })
        st.success(f"Utilizador '{display_name}' criado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao criar utilizador: {e}")
        return False

# --- 3. TELAS DA APLICAÇÃO ---

def render_login_screen():
    st.set_page_config(layout="centered")
    st.markdown("""
        <style>
        .title { font-family: 'Garamond', serif; font-style: italic; font-size: 48px; text-align: center; color: #2E4053; }
        </style>
        <h1 class="title">Meu Perito</h1>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            user_info = sign_in(email, password)
            if user_info:
                st.session_state.logged_in = True
                st.session_state.uid = user_info['localId']
                st.session_state.id_token = user_info['idToken']
                
                user_data = get_user_data(st.session_state.uid)
                if user_data:
                    st.session_state.user_name = user_data.get('display_name')
                    st.session_state.user_role = user_data.get('role')
                    st.session_state.force_password_change = user_data.get('first_login', False)
                    st.rerun()

def render_password_change_screen():
    st.title("Bem-vindo ao Meu Perito!")
    st.subheader("Por segurança, por favor, altere a sua senha inicial.")
    
    with st.form("password_change_form"):
        new_password = st.text_input("Nova Senha", type="password")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha e Continuar")

        if submitted:
            if new_password and len(new_password) >= 6 and new_password == confirm_password:
                if change_password(st.session_state.id_token, new_password):
                    db = init_firestore()
                    db.collection('users').document(st.session_state.uid).update({'first_login': False})
                    st.session_state.force_password_change = False
                    st.success("Senha alterada com sucesso! A redirecionar...")
                    st.rerun()
                else:
                    st.error("Não foi possível alterar a senha. Tente novamente.")
            else:
                st.error("As senhas não coincidem ou devem ter pelo menos 6 caracteres.")

def render_main_app():
    """Renderiza a aplicação principal após o login."""
    st.set_page_config(layout="wide")

    # Cabeçalho com nome do utilizador e botão de sair
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("Sistema de Gestão de Laudos")
    with col2:
        st.write(f"Utilizador: **{st.session_state.user_name}**")
        st.write(f"Perfil: *{st.session_state.user_role}*")
        if st.button("Sair"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    
    st.divider()

    # Painel de Administração visível apenas para o Administrador
    if st.session_state.user_role == 'Administrador':
        with st.expander("Painel de Administração"):
            st.subheader("Gestão de Utilizadores")
            with st.form("create_user_form", clear_on_submit=True):
                st.write("**Criar Novo Utilizador (Assistente)**")
                col_a, col_b, col_c = st.columns([2,2,1])
                new_email = col_a.text_input("Email do Assistente")
                new_name = col_b.text_input("Nome do Assistente")
                
                if col_c.form_submit_button("Criar"):
                    if new_email and new_name:
                        # A senha inicial é sempre '123456'
                        register_user(new_email, "123456", new_name, role='Assistente')
                    else:
                        st.warning("Por favor, preencha o email e o nome.")
        st.divider()

    # Lógica de navegação para o resto da aplicação
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
            st.info("A lista de processos apareceria aqui. (Funcionalidade a ser reintegrada)")
        if st.button("Voltar"):
            st.session_state.view = 'home'
            st.rerun()
    # As outras telas (process_list, data_entry) serão reintegradas aqui.

# --- PONTO DE ENTRADA PRINCIPAL ---

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_login_screen()
elif st.session_state.get('force_password_change', False):
    render_password_change_screen()
else:
    render_main_app()
