
import streamlit as st
import json
import os
import uuid

# Inicialização
if "dados" not in st.session_state:
    st.session_state.dados = {}

st.title("📋 Sistema de Laudos Periciais")

# Layout principal
st.markdown("## ➕ Adicionar Processo")

with st.form("adicionar_processo"):
    nome = st.text_input("Nome do periciando")
    numero = st.text_input("Número do Processo")
    tipo = st.selectbox("Tipo", ["AD", "BPC", "DPVAT"])
    horario = st.time_input("Horário", value=None)
    st.markdown("---")
    submitted = st.form_submit_button("✅ Adicionar Processo")

    if submitted and nome and numero:
        novo_id = str(uuid.uuid4())
        st.session_state.dados[novo_id] = {
            "nome": nome,
            "numero": numero,
            "tipo": tipo,
            "horario": horario.strftime("%H:%M") if horario else "09:00",
            "situacao": "Pré-laudo"
        }
        st.success("Processo adicionado com sucesso!")

# Lista de processos cadastrados
st.markdown("## 📋 Processos Cadastrados")
if not st.session_state.dados:
    st.info("Nenhum processo cadastrado.")
else:
    for processo_id, processo in st.session_state.dados.items():
        with st.container():
            cols = st.columns([2, 2, 2, 1, 2])
            cols[0].markdown(f"**🕒 Horário:** {processo['horario']}")
            cols[1].markdown(f"**📄 Processo:** {processo['numero']}")
            cols[2].markdown(f"**👤 Nome:** {processo['nome']}")
            cols[3].markdown(f"**🩺 Tipo:** {processo['tipo']}")
            with cols[4]:
                if st.button("✍️ Redigir Laudo", key=f"redigir_{processo_id}"):
                    if processo["tipo"] == "AD":
                        st.switch_page("laudos_ad.py")
                    elif processo["tipo"] == "BPC":
                        st.switch_page("laudos_bpc.py")
                    elif processo["tipo"] == "DPVAT":
                        st.switch_page("laudos_dpvat.py")
                    else:
                        st.warning("Tipo de processo não reconhecido.")
