import streamlit as st
import os
import json
import base64
import pandas as pd
import pdfplumber
import re
from datetime import datetime, timedelta

# -------------- Funções de apoio ----------------

def extrair_nome_autor(texto):
    match = re.search(r"(?:AUTOR|REQUERENTE)[\s:]*([\w\sÀ-ÿ]+?)\s+(?:RÉU|REQUERIDO|REQUERENTE)", texto, re.IGNORECASE)
    if match:
        nome = match.group(1).strip()
        return nome
    return "Não identificado"

def identificar_tipo_processo(texto):
    texto = texto.upper()
    if "LOAS" in texto or "BPC" in texto or "DEFICIENTE" in texto:
        return "BPC"
    elif "AUXÍLIO-DOENÇA" in texto or "AUXILIO-DOENÇA" in texto or "AUXÍLIO DOENÇA" in texto or "NB" in texto:
        return "AD"
    return "Não identificado"

def carregar_dados():
    if os.path.exists("dados_processos.json"):
        with open("dados_processos.json", "r") as f:
            return json.load(f)
    return {}

def salvar_dados(dados):
    with open("dados_processos.json", "w") as f:
        json.dump(dados, f, indent=2)

def horario_disponivel(data_iso, horario):
    dados = carregar_dados()
    if data_iso not in dados:
        return True
    return not any(proc["horario"] == horario for proc in dados[data_iso])

def gerar_opcoes_horario():
    horarios = []
    hora = 8
    minuto = 0
    while hora < 17 or (hora == 16 and minuto <= 45):
        horarios.append(f"{hora:02d}:{minuto:02d}")
        minuto += 15
        if minuto == 60:
            minuto = 0
            hora += 1
    return horarios

# -------------- Interface ----------------

st.set_page_config(layout="wide")
st.title("📂 Processos")

# Sessão principal
if "data_selecionada" not in st.session_state or "local_selecionado" not in st.session_state:
    st.error("Por favor, selecione uma data e um local no menu principal.")
    st.stop()

data_iso = st.session_state.data_selecionada
local_nome = st.session_state.local_selecionado

st.markdown(f"**Local:** {local_nome}")
st.markdown(f"**Data:** {datetime.strptime(data_iso, '%Y-%m-%d').strftime('%d-%m-%Y')}")

dados = carregar_dados()
if data_iso not in dados:
    dados[data_iso] = []

# Upload de processo PDF
uploaded_pdf = st.file_uploader("📄 Upload Processo (PDF)", type=["pdf"])
if uploaded_pdf:
    with pdfplumber.open(uploaded_pdf) as pdf:
        texto = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    nome_autor = extrair_nome_autor(texto)
    tipo = identificar_tipo_processo(texto)
    numero = re.search(r"\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}", texto)
    numero = numero.group() if numero else "Número não identificado"
    horarios_disponiveis = [h for h in gerar_opcoes_horario() if horario_disponivel(data_iso, h)]
    horario = st.selectbox("Horário", horarios_disponiveis)
    if st.button("✅ Adicionar Processo do PDF"):
        if horario_disponivel(data_iso, horario):
            dados[data_iso].append({
                "numero": numero,
                "nome": nome_autor,
                "tipo": tipo,
                "situacao": "Pré-laudo",
                "horario": horario,
                "origem": "pdf"
            })
            salvar_dados(dados)
            st.success("Processo adicionado!")
        else:
            st.warning("Horário já ocupado. Escolha outro.")

# Adição manual
with st.expander("➕ Adicionar Novo Processo Manualmente"):
    numero_manual = st.text_input("Número do Processo")
    nome_manual = st.text_input("Nome do Autor")
    tipo_manual = st.selectbox("Tipo", ["AD", "BPC"])
    horario_manual = st.selectbox("Horário disponível", [h for h in gerar_opcoes_horario() if horario_disponivel(data_iso, h)])
    if st.button("✅ Confirmar Inclusão Manual"):
        if horario_disponivel(data_iso, horario_manual):
            dados[data_iso].append({
                "numero": numero_manual,
                "nome": nome_manual,
                "tipo": tipo_manual,
                "situacao": "Pré-laudo",
                "horario": horario_manual,
                "origem": "manual"
            })
            salvar_dados(dados)
            st.success("Processo adicionado!")
        else:
            st.warning("Horário já ocupado. Escolha outro.")

# Exibição dos processos cadastrados
st.markdown("### 📋 Processos Cadastrados")

dados[data_iso].sort(key=lambda x: x["horario"])

df = pd.DataFrame(dados[data_iso])
if not df.empty:
    for processo in dados[data_iso]:
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2.5, 3, 2, 2, 3])
        col1.write(processo["horario"])
        col2.write(processo["numero"])
        col3.write(processo["nome"])
        col4.write(processo["tipo"])
        col5.write(processo["situacao"])
        with col6:
            if st.button("📝 Redigir laudo", key=f"laudo_{processo['numero']}"):
                st.info(f"⚠️ (Simulação) Redigindo laudo para {processo['numero']}...")

            if st.button("❌ Ausente", key=f"ausente_{processo['numero']}"):
                if st.confirm(f"Confirmar ausência de {processo['nome']}?"):
                    processo["situacao"] = "Ausente"
                    salvar_dados(dados)
                    st.success("Ausência confirmada.")

            if st.button("🗑️ Excluir", key=f"excluir_{processo['numero']}"):
                if st.confirm(f"Tem certeza que deseja excluir o processo {processo['numero']}?"):
                    dados[data_iso].remove(processo)
                    salvar_dados(dados)
                    st.success("Processo excluído.")
                    st.experimental_rerun()
else:
    st.info("Nenhum processo cadastrado para esta data.")
