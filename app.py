
import streamlit as st
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin
from datetime import datetime, date, timedelta
import calendar

# Inicializa o Firebase se ainda não estiver inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": "sistema-laudos-ad930",
        "private_key_id": "SUA_CHAVE",
        "private_key": "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk@EMAIL",
        "client_id": "SEU_ID",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "URL_CERTIFICADO"
    })
    initialize_app(cred)

db = firestore.client()

def render_calendar():
    st.title("Sistema de Gestão de Laudos")

    if "mes_atual" not in st.session_state:
        hoje = date.today()
        st.session_state["mes_atual"] = hoje.month
        st.session_state["ano_atual"] = hoje.year

    mes = st.session_state["mes_atual"]
    ano = st.session_state["ano_atual"]

    meses = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]

    st.subheader(f"{meses[mes-1].capitalize()} de {ano}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Mês anterior"):
            if mes == 1:
                st.session_state["mes_atual"] = 12
                st.session_state["ano_atual"] -= 1
            else:
                st.session_state["mes_atual"] -= 1
    with col2:
        if st.button("➡️ Próximo mês"):
            if mes == 12:
                st.session_state["mes_atual"] = 1
                st.session_state["ano_atual"] += 1
            else:
                st.session_state["mes_atual"] += 1

    dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    cal = calendar.Calendar(firstweekday=6)
    dias_mes = cal.monthdatescalendar(ano, mes)

    # Buscar todas as datas agendadas
    docs = db.collection("agendamentos").stream()
    datas_agendadas = []
    for doc in docs:
        data_doc = doc.to_dict().get("data")
        if isinstance(data_doc, datetime):
            datas_agendadas.append(data_doc.date())

    tabela = "<table style='border-collapse: collapse; width: 100%; text-align: center;'>"
    tabela += "<tr>" + "".join([f"<th style='border: 1px solid #ccc; padding: 6px;'>{d}</th>" for d in dias_semana]) + "</tr>"

    for semana in dias_mes:
        tabela += "<tr>"
        for dia in semana:
            marcado = ""
            if dia in datas_agendadas:
                marcado = "📌"
            if dia.month == mes:
                data_str = dia.strftime("%Y-%m-%d")
                tabela += f"<td style='border: 1px solid #ccc; padding: 6px;'><a href='?dia={data_str}'>{dia.day} {marcado}</a></td>"
            else:
                tabela += "<td></td>"
        tabela += "</tr>"
    tabela += "</table>"

    st.markdown(tabela, unsafe_allow_html=True)

# Chamada da função principal
render_calendar()
