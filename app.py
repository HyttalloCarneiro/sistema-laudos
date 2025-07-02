# Meu Perito - Sistema de Gestão de Laudos
# Versão ajustada para evitar erros em campos de data ausentes

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import calendar
import json
import base64
import requests

# --- Configurações iniciais ---

def init_firebase():
    if not firebase_admin._apps:
        try:
            creds_base64 = st.secrets["FIREBASE_CREDENTIALS_BASE64"]
            creds_json_str = base64.b64decode(creds_base64).decode("utf-8")
            creds_dict = json.loads(creds_json_str)
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)
        except Exception as e:
            st.error(f"Erro ao iniciar Firebase: {e}")
            st.stop()
    return firestore.client()

# --- Autenticação ---

def sign_in(email, password):
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
        return r.json()
    except:
        return None

def get_user_data(uid):
    db = init_firebase()
    ref = db.collection("users").document(uid)
    doc = ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

# --- Meses e dias da semana em português ---

meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# --- Renderizar calendário ---

def render_calendar():
    hoje = datetime.date.today()
    ano = st.session_state.get("ano", hoje.year)
    mes = st.session_state.get("mes", hoje.month)

    st.markdown(f"## {meses[mes-1].capitalize()} de {ano}")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅ Mês anterior"):
            if mes == 1:
                st.session_state["mes"] = 12
                st.session_state["ano"] = ano - 1
            else:
                st.session_state["mes"] = mes - 1
            st.rerun()

    with col2:
        if st.button("➡ Próximo mês"):
            if mes == 12:
                st.session_state["mes"] = 1
                st.session_state["ano"] = ano + 1
            else:
                st.session_state["mes"] = mes + 1
            st.rerun()

    db = init_firebase()
    agendamentos_ref = db.collection("agendamentos").where("usuario_id", "==", st.session_state["uid"])
    docs = agendamentos_ref.stream()

    datas_agendadas = []
    for doc in docs:
        dados = doc.to_dict()
        if "data" in dados and hasattr(dados["data"], "date"):
            datas_agendadas.append(dados["data"].date())

    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(ano, mes)

    html = "<table border='1' style='width: 100%; text-align: center;'>"
    html += "<tr>" + "".join([f"<th>{d}</th>" for d in dias_semana]) + "</tr>"

    for semana in semanas:
        html += "<tr>"
        for dia in semana:
            if dia.month != mes:
                html += "<td style='background-color: #f0f0f0; color: #ccc;'></td>"
            else:
                marcado = ""
                estilo = ""
                if dia in datas_agendadas:
                    if dia < hoje:
                        estilo = "background-color: #f8d7da;"  # vermelho claro
                        marcado = "<br><span style='font-size: 0.8em;'>✅ Concluído</span>"
                    else:
                        estilo = "background-color: #d4edda;"  # verde claro
                        marcado = "<br><span style='font-size: 0.8em;'>🟢 Agendado</span>"
                link = f"?dia={dia.isoformat()}"
                html += f"<td style='{estilo}'><a href='{link}'>{dia.day}{marcado}</a></td>"
        html += "</tr>"
    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

# --- Tela de login ---

def render_login():
    st.title("Meu Perito - Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = sign_in(email, senha)
        if user:
            st.session_state["logged_in"] = True
            st.session_state["uid"] = user["localId"]
            st.rerun()
        else:
            st.error("Email ou senha inválidos.")

# --- Tela principal ---

def render_home():
    st.title("Sistema de Gestão de Laudos")
    render_calendar()

# --- Execução ---

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    render_home()
else:
    render_login()
