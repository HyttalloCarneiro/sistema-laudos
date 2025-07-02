# Sistema de Gestão de Laudos Periciais
# Versão DEBUG: Modo de Depuração para os Segredos do Firebase.
# Objetivo: Diagnosticar o erro de formatação da chave privada ao exibir
# o conteúdo exato que está a ser lido pelo aplicativo.

import streamlit as st
import firebase_admin
from firebase_admin import credentials

# --- Função de Depuração ---
def debug_firestore_secrets():
    """
    Esta função não inicializa o Firebase, mas sim exibe informações de depuração
    sobre as credenciais para identificar o erro de formatação.
    """
    st.title("👨‍⚕️ Modo de Depuração dos Segredos")
    st.info("Esta página vai ajudar-nos a diagnosticar o problema com as suas credenciais do Firebase.")
    st.write("---")

    try:
        # 1. Verificar se o segredo principal existe
        st.subheader("1. A verificar `[firebase_credentials]`")
        if "firebase_credentials" not in st.secrets:
            st.error("ERRO: O segredo `[firebase_credentials]` não foi encontrado no seu ficheiro secrets.toml online.")
            st.write("Por favor, verifique se copiou o cabeçalho `[firebase_credentials]` para a caixa de segredos no site do Streamlit.")
            st.stop()
        
        creds_dict = st.secrets["firebase_credentials"]
        st.success("✅ Segredo `[firebase_credentials]` encontrado!")
        st.write("---")

        # 2. Verificar se a chave privada existe dentro do segredo
        st.subheader("2. A verificar `private_key`")
        if "private_key" not in creds_dict:
            st.error("ERRO: A `private_key` não foi encontrada dentro de `[firebase_credentials]`.")
            st.write("Isto indica um problema no formato do texto que foi colado nos segredos.")
            st.stop()

        private_key_original = creds_dict["private_key"]
        st.success("✅ `private_key` encontrada!")
        st.write("---")

        # 3. Mostrar informações de depuração sobre a chave
        st.subheader("3. Análise da Chave Privada (Como o Streamlit a vê)")
        st.write(f"**Tipo de dados da chave:** `{type(private_key_original)}`")
        
        st.write("**Primeiros 150 caracteres da chave original:**")
        st.code(private_key_original[:150], language="text")
        
        st.write("☝️ **Análise:** Se você vir `\\n` no texto acima, significa que as quebras de linha não estão a ser processadas corretamente. O texto deveria aparecer em múltiplas linhas, como no ficheiro original.")
        st.write("---")

        # 4. Tentar a correção e mostrar o resultado
        st.subheader("4. Tentativa de Correção Automática")
        try:
            # Cria uma cópia para evitar o erro "item assignment"
            creds_copy = dict(creds_dict)
            creds_copy['private_key'] = creds_copy['private_key'].replace('\\n', '\n')
            private_key_corrigida = creds_copy['private_key']
            
            st.write("**Primeiros 150 caracteres da chave APÓS a correção:**")
            st.code(private_key_corrigida[:150], language="text")
            st.success("✅ A correção foi aplicada com sucesso no código.")
            st.write("Se o texto acima agora aparece em múltiplas linhas (sem `\\n`), o problema está resolvido no código.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao tentar corrigir a chave: {e}")

        st.write("---")
        st.info("Fim da depuração. Por favor, envie uma captura de ecrã completa desta página para que eu possa fazer o diagnóstico final.")

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante a depuração: {e}")
    
    # Para a execução da aplicação aqui
    st.stop()

# --- PONTO DE ENTRADA PRINCIPAL ---
# Chama diretamente a função de depuração
debug_firestore_secrets()
