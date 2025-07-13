import streamlit as st

def gerenciar_configuracoes():
    st.markdown("## ⚙️ Configurações do Sistema")
    st.markdown("Escolha uma categoria para gerenciar:")

    categoria = st.radio("", ["Modelos de Exame Clínico", "Modelos de Patologias"])

    if categoria == "Modelos de Exame Clínico":
        st.markdown("### 📝 Modelos de Exame Clínico")
        novo_modelo = st.text_area("Novo modelo de exame clínico")
        if st.button("Salvar modelo"):
            st.success("Modelo de exame clínico salvo com sucesso!")

    elif categoria == "Modelos de Patologias":
        st.markdown("### 🧬 Modelos de Patologias")
        nova_patologia = st.text_input("Nova patologia")
        if st.button("Salvar patologia"):
            st.success("Modelo de patologia salvo com sucesso!")