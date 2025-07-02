# Meu Perito - Sistema de Gestão de Laudos
# Versão 7.2: Versão de depuração focada exclusivamente no login.
# Objetivo: Isolar e resolver o problema de autenticação com o Firebase.

import streamlit as st
import requests
import json

# --- LÓGICA DE AUTENTICAÇÃO ---

def sign_in(email, password):
    """Autentica um utilizador usando a API REST do Firebase."""
    try:
        api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    except KeyError:
        st.error("ERRO CRÍTICO: A chave 'FIREBASE_WEB_API_KEY' não foi encontrada nos seus Segredos. Por favor, configure-a no painel do Streamlit Cloud.")
        return None

    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    
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

# --- TELAS DA APLICAÇÃO ---

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
                st.session_state.id_token = user_info['idToken']
                st.session_state.email = user_info.get('email', 'Utilizador')
                # Simula a necessidade de mudar a senha para o utilizador de teste
                if password == "123456":
                    st.session_state.force_password_change = True
                else:
                    st.session_state.force_password_change = False
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
                    st.session_state.force_password_change = False
                    st.success("Senha alterada com sucesso! A redirecionar...")
                    st.rerun()
                else:
                    st.error("Não foi possível alterar a senha. Tente novamente.")
            else:
                st.error("As senhas não coincidem ou devem ter pelo menos 6 caracteres.")

def render_main_app():
    st.set_page_config(layout="wide")
    st.title("Login bem-sucedido!")
    st.success("Conseguimos! A autenticação está a funcionar.")
    st.write(f"Bem-vindo, **{st.session_state.email}**!")
    st.info("Agora que o login está resolvido, podemos reintroduzir as funcionalidades de gestão de laudos.")
    if st.button("Sair"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- PONTO DE ENTRADA PRINCIPAL ---

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_login_screen()
elif st.session_state.get('force_password_change', False):
    render_password_change_screen()
else:
    render_main_app()
