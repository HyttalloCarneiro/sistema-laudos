# Meu Perito - Sistema de Gestão de Laudos
# Versão 7.1: Implementa autenticação real com Firebase e mudança de senha.
# Objetivo: Criar um sistema de login seguro que se conecta ao Firebase Authentication,
# força a mudança de senha no primeiro acesso e estabelece a base para a gestão de utilizadores.

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import requests
import json

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO ---

def init_firebase():
    """Inicializa o Firebase Admin SDK se ainda não foi inicializado."""
    if not firebase_admin._apps:
        try:
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
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    try:
        response = requests.post(rest_api_url, data=payload)
        response.raise_for_status() # Lança um erro para respostas 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError:
        st.error("Email ou senha inválidos. Por favor, tente novamente.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro de conexão: {e}")
        return None

def change_password(id_token, new_password):
    """Altera a senha de um utilizador usando a API REST."""
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"
    payload = json.dumps({
        "idToken": id_token,
        "password": new_password,
        "returnSecureToken": False
    })
    try:
        response = requests.post(rest_api_url, data=payload)
        response.raise_for_status()
        return True
    except Exception:
        return False

def get_user_data(uid):
    """Obtém os dados de um utilizador (perfil, etc.) do Firestore."""
    db = init_firestore()
    user_doc = db.collection('users').document(uid).get()
    if user_doc.exists:
        return user_doc.to_dict()
    
    # Se o documento não existir (ex: primeiro login do admin), cria-o
    user_record = auth.get_user(uid)
    user_data = {
        'email': user_record.email,
        'display_name': user_record.display_name or 'Administrador',
        'role': 'Administrador', # Assume que o primeiro utilizador é admin
        'first_login': True
    }
    db.collection('users').document(uid).set(user_data)
    return user_data

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
                st.session_state.user_name = user_data.get('display_name', 'Utilizador')
                st.session_state.user_role = user_data.get('role', 'Assistente')
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
            if new_password and new_password == confirm_password:
                if change_password(st.session_state.id_token, new_password):
                    db = init_firestore()
                    db.collection('users').document(st.session_state.uid).update({'first_login': False})
                    st.session_state.force_password_change = False
                    st.success("Senha alterada com sucesso! A redirecionar...")
                    st.rerun()
                else:
                    st.error("Não foi possível alterar a senha. Tente novamente.")
            else:
                st.error("As senhas não coincidem ou estão em branco.")

def render_main_app():
    st.set_page_config(layout="wide")
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
    st.info("Aplicação principal - Funcionalidades de gestão de perícias serão adicionadas aqui.")

# --- PONTO DE ENTRADA PRINCIPAL ---

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_login_screen()
elif st.session_state.get('force_password_change', False):
    render_password_change_screen()
else:
    render_main_app()
