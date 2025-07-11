
import streamlit as st
from datetime import datetime
from streamlit_extras.switch_page_button import switch_page
from streamlit.source_util import get_pages

# Função para inicializar variáveis de sessão
def inicializar_sessao():
    if "processos" not in st.session_state:
        st.session_state.processos = []
    if "editar" not in st.session_state:
        st.session_state.editar = None

# Função para adicionar processo
def adicionar_processo(nome, numero, tipo, horario):
    st.session_state.processos.append({
        "nome": nome,
        "numero": numero,
        "tipo": tipo,
        "horario": horario,
        "status": "Pré-laudo"
    })

# Função principal da interface
def main():
    st.title("🗂️ Sistema de Laudos Periciais")

    inicializar_sessao()

    st.header("➕ Adicionar Processo")
    with st.form("form_processo"):
        nome = st.text_input("Nome do periciando")
        numero = st.text_input("Número do Processo")
        tipo = st.selectbox("Tipo", ["AD", "BPC", "DPVAT"])
        horario = st.time_input("Horário", value=datetime.strptime("09:00", "%H:%M").time())
        submitted = st.form_submit_button("Adicionar Processo")
        if submitted and nome and numero:
            adicionar_processo(nome, numero, tipo, horario)

    st.header("📋 Processos Cadastrados")
    if st.session_state.processos:
        for i, proc in enumerate(st.session_state.processos):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            col1.markdown(f"🕘 **Horário:** {proc['horario'].strftime('%H:%M')}")
            col2.markdown(f"📁 **Processo:** {proc['numero']}")
            col3.markdown(f"👤 **Nome:** {proc['nome']}")
            col4.markdown(f"⚖️ **Tipo:** {proc['tipo']}")
            if col5.button("✍️ Redigir Laudo", key=f"editar_{i}"):
                st.session_state.editar = i
                tipo = proc["tipo"]
                nome_da_pagina = {
                    "AD": "laudos_ad",
                    "BPC": "laudos_bpc",
                    "DPVAT": "laudos_dpvat"
                }.get(tipo)
                paginas = get_pages("app.py")
                for chave, pagina in paginas.items():
                    if nome_da_pagina in pagina["page_name"]:
                        switch_page(pagina["page_name"])
                        break
    else:
        st.info("Nenhum processo cadastrado.")

if __name__ == "__main__":
    main()
