# Meu Perito - Sistema de Gestão de Laudos
# Versão 8.0: Novo calendário visual com navegação entre meses, estilo em tabela, cabeçalho com mês/ano, dias da semana e lista de locais logo abaixo.

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import requests
import json
import base64
import calendar
import pandas as pd
from io import BytesIO

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

# --- 2. FUNÇÕES AUXILIARES ---

def carregar_agendamentos():
    db = init_firebase()
    ag_ref = db.collection("agendamentos")
    docs = ag_ref.stream()
    dados = []
    for doc in docs:
        dados.append(doc.to_dict() | {"id": doc.id})
    return dados

def salvar_agendamento(data, local):
    db = init_firebase()
    db.collection("agendamentos").add({
        "data": data.strftime("%Y-%m-%d"),
        "local": local
    })

def excluir_agendamento(doc_id):
    db = init_firebase()
    db.collection("agendamentos").document(doc_id).delete()

# --- 3. CALENDÁRIO VISUAL ---

def render_calendario():
    hoje = datetime.date.today()

    if 'mes_atual' not in st.session_state:
        st.session_state.mes_atual = hoje.month
        st.session_state.ano_atual = hoje.year

    def avancar_mes():
        if st.session_state.mes_atual == 12:
            st.session_state.mes_atual = 1
            st.session_state.ano_atual += 1
        else:
            st.session_state.mes_atual += 1

    def voltar_mes():
        if st.session_state.mes_atual == 1:
            st.session_state.mes_atual = 12
            st.session_state.ano_atual -= 1
        else:
            st.session_state.mes_atual -= 1

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.button("⬅️", on_click=voltar_mes)
    with col2:
        st.markdown(f"### 📆 {calendar.month_name[st.session_state.mes_atual]} de {st.session_state.ano_atual}", unsafe_allow_html=True)
    with col3:
        st.button("➡️", on_click=avancar_mes)

    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    st.markdown("""
    <style>
        .calendar-table {border-collapse: collapse; width: 100%;}
        .calendar-table th, .calendar-table td {
            border: 1px solid #ddd; text-align: center; padding: 8px;
        }
        .calendar-table td:hover {background-color: #f2f2f2; cursor: pointer;}
    </style>
    """, unsafe_allow_html=True)

    agendamentos = carregar_agendamentos()
    datas_agendadas = set([a['data'] for a in agendamentos])

    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(st.session_state.ano_atual, st.session_state.mes_atual)

    tabela = "<table class='calendar-table'>"
    tabela += "<tr>" + "".join(f"<th>{d}</th>" for d in dias_semana) + "</tr>"
    for semana in semanas:
        tabela += "<tr>"
        for dia in semana:
            if dia.month != st.session_state.mes_atual:
                tabela += f"<td style='color:#ccc'>{dia.day}</td>"
            else:
                data_str = dia.strftime("%Y-%m-%d")
                marcado = "🔵" if data_str in datas_agendadas else ""
                tabela += f'<td><button onclick="window.location.href=\'?dia={data_str}\'">{dia.day} {marcado}</button></td>'
        tabela += "</tr>"
    tabela += "</table>"
    st.markdown(tabela, unsafe_allow_html=True)

# --- 4. TELA PRINCIPAL ---

def main():
    st.set_page_config(page_title="Meu Perito", layout="wide")
    st.title("Sistema de Gestão de Laudos")
    render_calendario()

    st.divider()
    st.subheader("📍 Locais de Perícia")
    locais = ["17ª Vara Federal - Juazeiro"]
    for local in locais:
        with st.expander(f"📌 {local}"):
            dados = [a for a in carregar_agendamentos() if a['local'] == local]
            if dados:
                df = pd.DataFrame(dados)
                df['data'] = pd.to_datetime(df['data']).dt.strftime("%d-%m-%Y")
                for i, row in df.iterrows():
                    col1, col2, col3 = st.columns([2,2,1])
                    col1.write(f"📅 {row['data']}")
                    col2.write(f"📍 {row['local']}")
                    if col3.button("🗑️ Excluir", key=f"del_{row['id']}"):
                        excluir_agendamento(row['id'])
                        st.success("Agendamento excluído!")
                        st.rerun()
            else:
                st.info("Nenhum agendamento para este local ainda.")

# --- PONTO DE ENTRADA ---

if __name__ == "__main__":
    main()
