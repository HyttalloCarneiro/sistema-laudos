
# Meu Perito - Sistema de Gestão de Laudos
# Versão Corrigida: Remove uso de locale.setlocale() e traduz meses e dias manualmente
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import requests
import json
import base64
import calendar

# Dicionários de tradução
MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]
DIAS_SEMANA_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# --- 1. Firebase ---
def init_firebase():
    if not firebase_admin._apps:
        creds_base64 = st.secrets["FIREBASE_CREDENTIALS_BASE64"]
        creds_json_str = base64.b64decode(creds_base64).decode("utf-8")
        creds_dict = json.loads(creds_json_str)
        creds = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(creds)
    return firestore.client()

# --- 2. Autenticação ---
def sign_in(email, password):
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    try:
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return res.json()
    except:
        return None

def get_user_data(uid):
    db = init_firebase()
    user_doc_ref = db.collection('users').document(uid)
    user_doc = user_doc_ref.get()
    return user_doc.to_dict() if user_doc.exists else None

# --- 3. Layout do Calendário ---
def render_calendario():
    hoje = datetime.date.today()
    ano = st.session_state.get("ano", hoje.year)
    mes = st.session_state.get("mes", hoje.month)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️"):
            if mes == 1:
                st.session_state["mes"] = 12
                st.session_state["ano"] = ano - 1
            else:
                st.session_state["mes"] = mes - 1
    with col2:
        st.markdown(f"<h3 style='text-align: center'>{MESES_PT[mes-1].capitalize()} de {ano}</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("➡️"):
            if mes == 12:
                st.session_state["mes"] = 1
                st.session_state["ano"] = ano + 1
            else:
                st.session_state["mes"] = mes + 1

    db = init_firebase()
    agendamentos = db.collection("agendamentos").stream()
    datas_marcadas = set(doc.to_dict()["data"] for doc in agendamentos)

    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(ano, mes)

    st.markdown("<table style='width:100%; border-collapse: collapse;'>", unsafe_allow_html=True)
    st.markdown("<tr>" + "".join(f"<th style='border:1px solid #ccc'>{dia}</th>" for dia in DIAS_SEMANA_PT) + "</tr>", unsafe_allow_html=True)
    for semana in semanas:
        st.markdown("<tr>", unsafe_allow_html=True)
        for dia in semana:
            estilo = "border:1px solid #ccc; padding:6px; text-align:center;"
            data_str = dia.strftime("%Y-%m-%d")
            if dia.month != mes:
                st.markdown(f"<td style='{estilo} background-color:#f9f9f9'></td>", unsafe_allow_html=True)
            else:
                if data_str in datas_marcadas:
                    cor = "#d1e7dd" if dia >= hoje else "#f8d7da"
                    texto = f"<b>{dia.day}</b><br><small>{'✅' if dia < hoje else 'Agendado'}</small>"
                    st.markdown(f"<td style='{estilo} background-color:{cor}'>{texto}</td>", unsafe_allow_html=True)
                else:
                    link = f"?dia={data_str}"
                    st.markdown(f"<td style='{estilo}'><a href='{link}'>{dia.day}</a></td>", unsafe_allow_html=True)
        st.markdown("</tr>", unsafe_allow_html=True)
    st.markdown("</table>", unsafe_allow_html=True)

# --- 4. Tela Principal ---
def main_app():
    st.title("📅 Sistema de Gestão de Laudos")
    render_calendario()

# --- 5. Login ---
def login_screen():
    st.title("Login")
    with st.form("login"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            user = sign_in(email, senha)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["uid"] = user["localId"]
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

# --- 6. Roteador ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app()
else:
    login_screen()
