# Meu Perito - Sistema de Gestão de Laudos
# Versão 7.6: Tela unificada com filtro por local e/ou data + formato DD-MM-AAAA

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import requests
import json
import base64
import pandas as pd

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO ---

def init_firebase():
    if not firebase_admin._apps:
        try:
            creds_base64 = st.secrets["FIREBASE_CREDENTIALS_BASE64"]
            creds_json_str = base64.b64decode(creds_base64).decode("utf-8")
            creds_dict = json.loads(creds_json_str)
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {e}")
            st.stop()
    return firestore.client()

# --- 2. AUTENTICAÇÃO ---

def sign_in(email, password):
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    try:
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError:
        st.error("Email ou senha inválidos.")
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def change_password(id_token, new_password):
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"
    payload = json.dumps({"idToken": id_token, "password": new_password, "returnSecureToken": False})
    try:
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return True
    except Exception:
        return False

def get_user_data(uid):
    db = init_firebase()
    doc_ref = db.collection('users').document(uid)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    try:
        user = auth.get_user(uid)
        data = {
            'email': user.email,
            'display_name': "Hyttallo Carneiro",
            'role': 'Administrador',
            'first_login': True
        }
        doc_ref.set(data)
        return data
    except Exception as e:
        st.error(f"Erro ao obter dados do usuário: {e}")
        return None

def register_user(email, password, display_name, role='Assistente'):
    try:
        user = auth.create_user(email=email, password=password, display_name=display_name)
        db = init_firebase()
        db.collection('users').document(user.uid).set({
            'email': email,
            'display_name': display_name,
            'role': role,
            'first_login': True
        })
        st.success(f"Usuário '{display_name}' criado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao criar usuário: {e}")
        return False

# --- 3. AGENDAMENTO ---

def salvar_agendamento(uid, local, data):
    try:
        db = init_firebase()
        agendamento = {
            "usuario_id": uid,
            "local": local,
            "data": data.strftime("%Y-%m-%d"),
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        db.collection("agendamentos").add(agendamento)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar agendamento: {e}")
        return False

def carregar_agendamentos(uid):
    try:
        db = init_firebase()
        agendamentos_ref = db.collection("agendamentos").where("usuario_id", "==", uid).order_by("data")
        docs = agendamentos_ref.stream()
        dados = []
        for doc in docs:
            d = doc.to_dict()
            dados.append({
                "Data da Perícia": d.get("data"),
                "Local": d.get("local"),
            })
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar agendamentos: {e}")
        return []

# --- 4. TELAS ---

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
    st.title("Alterar Senha Inicial")
    with st.form("password_change_form"):
        new_password = st.text_input("Nova Senha", type="password")
        confirm = st.text_input("Confirmar Nova Senha", type="password")
        if st.form_submit_button("Alterar Senha e Continuar"):
            if new_password == confirm and len(new_password) >= 6:
                if change_password(st.session_state.id_token, new_password):
                    db = init_firebase()
                    db.collection('users').document(st.session_state.uid).update({'first_login': False})
                    st.session_state.force_password_change = False
                    st.success("Senha alterada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao alterar senha.")
            else:
                st.error("Senhas devem coincidir e ter pelo menos 6 caracteres.")

def render_main_app():
    st.set_page_config(layout="wide")

    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("Sistema de Gestão de Laudos")
    with col2:
        st.write(f"Usuário: **{st.session_state.user_name}**")
        st.write(f"Perfil: *{st.session_state.user_role}*")
        if st.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.divider()

    st.header("📅 Agendamento e Consulta")

    locais = ["17ª Vara Federal - Juazeiro", "Interior (designar)", "Sede da Justiça Federal"]
    local_escolhido = st.selectbox("Local da Perícia:", locais)
    data_escolhida = st.date_input("Data da Perícia:", datetime.date.today(), format="DD-MM-YYYY")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirmar Agendamento"):
            if salvar_agendamento(st.session_state.uid, local_escolhido, data_escolhida):
                st.success(f"Agendamento salvo para {data_escolhida.strftime('%d-%m-%Y')} no local: {local_escolhido}")

    with col2:
        if st.button("🔍 Consultar Agendamentos"):
            dados = carregar_agendamentos(st.session_state.uid)
            resultados = []
            for d in dados:
                if (
                    (not local_escolhido or d['Local'] == local_escolhido)
                    and (not data_escolhida or d['Data da Perícia'] == data_escolhida.strftime('%Y-%m-%d'))
                ):
                    d_formatado = {
                        "Data da Perícia": datetime.datetime.strptime(d["Data da Perícia"], "%Y-%m-%d").strftime("%d-%m-%Y"),
                        "Local": d["Local"]
                    }
                    resultados.append(d_formatado)
            if resultados:
                st.subheader("📋 Resultados Encontrados:")
                st.table(resultados)
            else:
                st.info("Nenhum agendamento encontrado com os critérios selecionados.")

    st.divider()
    st.subheader("📌 Todos os Agendamentos")
    todos = carregar_agendamentos(st.session_state.uid)
    if todos:
        for d in todos:
            try:
                d["Data da Perícia"] = datetime.datetime.strptime(d["Data da Perícia"], "%Y-%m-%d").strftime("%d-%m-%Y")
            except:
                pass
        df = pd.DataFrame(todos)
        df = df.sort_values(by="Data da Perícia")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum agendamento registrado.")

# --- INÍCIO ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_login_screen()
elif st.session_state.get('force_password_change', False):
    render_password_change_screen()
else:
    render_main_app()
