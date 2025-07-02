# Meu Perito - Sistema de Gestão de Laudos
# Versão 8.0: Calendário otimizado com datas em português, autenticação reativada e desempenho melhorado.

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import requests
import json
import base64
import locale
import calendar

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO ---

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')  # Exibe meses e dias em português

if not firebase_admin._apps:
    creds_base64 = st.secrets["FIREBASE_CREDENTIALS_BASE64"]
    creds_json_str = base64.b64decode(creds_base64).decode("utf-8")
    creds_dict = json.loads(creds_json_str)
    creds = credentials.Certificate(creds_dict)
    firebase_admin.initialize_app(creds)

db = firestore.client()

# --- 2. AUTENTICAÇÃO SIMPLES COM FIREBASE ---

def sign_in(email, password):
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]
    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    response = requests.post(rest_api_url, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# --- 3. CALENDÁRIO E AGENDAMENTOS ---

def exibir_calendario():
    hoje = datetime.date.today()
    ano = st.session_state.get("ano", hoje.year)
    mes = st.session_state.get("mes", hoje.month)

    st.markdown(f"## 📅 {calendar.month_name[mes].capitalize()} de {ano}")

    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("⬅️"):
            if mes == 1:
                mes = 12
                ano -= 1
            else:
                mes -= 1
            st.session_state.mes = mes
            st.session_state.ano = ano
            st.rerun()

    with col3:
        if st.button("➡️"):
            if mes == 12:
                mes = 1
                ano += 1
            else:
                mes += 1
            st.session_state.mes = mes
            st.session_state.ano = ano
            st.rerun()

    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    cal = calendar.Calendar(firstweekday=0)
    agendamentos_ref = db.collection("agendamentos").stream()
    datas_marcadas = {a.to_dict()["data"] for a in agendamentos_ref}

    st.markdown("<style>table, th, td { border: 1px solid lightgray; padding: 6px; text-align: center; }</style>", unsafe_allow_html=True)
    tabela = "<table><tr>" + "".join([f"<th>{dia}</th>" for dia in dias_semana]) + "</tr>"

    for semana in cal.monthdatescalendar(ano, mes):
        tabela += "<tr>"
        for dia in semana:
            if dia.month != mes:
                tabela += "<td style='color:lightgray'>-</td>"
            else:
                data_str = dia.strftime("%Y-%m-%d")
                marcado = "🔵" if data_str in datas_marcadas else ""
                link = f"?dia={data_str}"
                tabela += f'<td><a href="{link}">{dia.day} {marcado}</a></td>'
        tabela += "</tr>"

    tabela += "</table>"
    st.markdown(tabela, unsafe_allow_html=True)

# --- 4. AGENDAMENTO POR DIA ---

def agendar_para_dia(data_escolhida):
    st.markdown(f"### 📌 Agendar para {data_escolhida.strftime('%d/%m/%Y')}")
    local = st.selectbox("Local da Perícia:", ["17ª Vara Federal - Juazeiro"])
    if st.button("✅ Confirmar Agendamento"):
        db.collection("agendamentos").add({
            "data": data_escolhida.strftime("%Y-%m-%d"),
            "local": local,
            "usuario_id": st.session_state.uid,
            "timestamp": datetime.datetime.now()
        })
        st.success("Agendamento realizado com sucesso!")

# --- 5. VISUALIZAÇÃO POR LOCAL ---

def visualizar_local(local):
    st.markdown(f"### 📍 Agendamentos para {local}")
    ags = db.collection("agendamentos").where("local", "==", local).stream()
    registros = []
    for a in ags:
        d = a.to_dict()
        d["id"] = a.id
        registros.append(d)
    registros.sort(key=lambda x: x["data"])
    for r in registros:
        data_formatada = datetime.datetime.strptime(r["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
        concluido = "✅ Concluído" if datetime.datetime.strptime(r["data"], "%Y-%m-%d").date() < datetime.date.today() else ""
        col1, col2, col3 = st.columns([3, 4, 2])
        col1.write(data_formatada)
        col2.write(r["local"])
        col3.button("🗑️ Excluir", key=r["id"], on_click=lambda doc_id=r["id"]: db.collection("agendamentos").document(doc_id).delete())

# --- 6. TELA DE LOGIN ---

def login():
    st.title("🔐 Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        if submit:
            user = sign_in(email, senha)
            if user:
                st.session_state.logged_in = True
                st.session_state.uid = user["localId"]
                st.rerun()
            else:
                st.error("Email ou senha inválidos.")

# --- 7. PÁGINA PRINCIPAL ---

def main_app():
    st.title("Sistema de Gestão de Laudos")
    exibir_calendario()

    st.markdown("---")
    st.subheader("🏛️ Locais de Perícia")
    if st.button("🔍 Ver agendamentos da 17ª Vara Federal - Juazeiro"):
        visualizar_local("17ª Vara Federal - Juazeiro")

    # Caso tenha clicado em uma data do calendário
    query_params = st.experimental_get_query_params()
    if "dia" in query_params:
        data_str = query_params["dia"][0]
        try:
            data_dt = datetime.datetime.strptime(data_str, "%Y-%m-%d")
            agendar_para_dia(data_dt)
        except:
            st.warning("Data inválida na URL.")

# --- 8. PONTO DE ENTRADA ---

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    main_app()
