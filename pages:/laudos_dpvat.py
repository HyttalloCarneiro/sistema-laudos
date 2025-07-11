import openai
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]
import streamlit as st

def redigir_laudo_interface(dados):
    st.title("📝 Redigir Laudo de DPVAT")

    nome = dados.get("nome_autor", "")
    processo = dados.get("numero_processo", "")
    der = dados.get("der", "")
    nb = dados.get("nb", "")
    cpf = dados.get("cpf", "")
    rg = dados.get("rg", "")
    nascimento = dados.get("nascimento", "")
    profissao = dados.get("profissao", "")

    st.markdown("### Dados do Processo")
    st.text_input("Nome do Autor", value=nome, disabled=True)
    st.text_input("Número do Processo", value=processo, disabled=True)
    st.text_input("DER", value=der, disabled=True)
    st.text_input("NB", value=nb, disabled=True)
    st.text_input("CPF", value=cpf, disabled=True)
    st.text_input("RG", value=rg, disabled=True)
    st.text_input("Data de Nascimento", value=nascimento, disabled=True)
    st.text_input("Profissão", value=profissao, disabled=True)

    st.markdown("### Anamnese e Exame Clínico")
    anamnese = st.text_area("Anamnese", height=150)
    exame = st.text_area("Exame Clínico", height=150)

    st.markdown("### Conclusão")
    conclusao = st.text_area("Conclusão da Perícia", height=100)

    if st.button("💾 Salvar Laudo"):
        st.success("Laudo salvo com sucesso! (simulação)")
