import openai
import streamlit as st

# openai.api_key = st.secrets["OPENAI_API_KEY"]

def redigir_laudo_interface():
    if "laudo_gerado" not in st.session_state:
        st.warning("Nenhum pré-laudo foi gerado ainda. Volte e clique em 'Gerar Lote'.")
        st.stop()

    st.title("📝 Redigir Laudo de Auxílio-Doença")

    nome = st.session_state.get("nome_autor", "")
    processo = st.session_state.get("numero_processo", "")
    der = st.session_state.get("der", "")
    nb = st.session_state.get("nb", "")
    cpf = st.session_state.get("cpf", "")
    rg = st.session_state.get("rg", "")
    nascimento = st.session_state.get("data_nascimento", "")
    profissao = st.session_state.get("profissao", "")

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
    anamnese = st.text_area("Anamnese", value=st.session_state.get("anamnese", ""), height=150)
    exame = st.text_area("Exame Clínico", value=st.session_state.get("exame", ""), height=150)

    st.markdown("### Conclusão")
    conclusao = st.text_area("Conclusão da Perícia", value=st.session_state.get("conclusao", ""), height=100)

    if st.button("💾 Salvar Laudo"):
        st.success("Laudo salvo com sucesso! (simulação)")


# Função para gerar laudo automaticamente conforme padrões da 17ª Vara
def gerar_laudo_ad(texto_extraido, nome_parte):
    return f"""LAUDO MÉDICO PERICIAL - AUXÍLIO-DOENÇA

Autor: {nome_parte}

Resumo do processo:
{texto_extraido}

Anamnese:
[Preencher com dados da entrevista clínica]

Exame Físico:
[Preencher com achados do exame clínico]

Conclusão:
[Inserir conclusão pericial com base nos dados]

Este laudo foi gerado automaticamente com base nos padrões da 17ª Vara Federal.
"""

__all__ = ["gerar_laudo_ad", "redigir_laudo_interface"]
