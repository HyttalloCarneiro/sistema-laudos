# Sistema de Gestão de Laudos Periciais
# Versão 3.0.2: Reverte a manipulação da chave privada para confiar no formato TOML.
# Objetivo: Corrigir o erro "Invalid certificate argument" de forma definitiva.

import streamlit as st
import google.generativeai as genai
import PyPDF2
from io import BytesIO
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIGURAÇÃO DO FIREBASE ---
def init_firestore():
    """Inicializa e retorna o cliente do Firestore."""
    if not firebase_admin._apps:
        try:
            # A linha que manipulava a chave foi removida.
            # Agora confiamos 100% no formato dos Segredos do Streamlit.
            creds_dict = st.secrets["firebase_credentials"]
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)
        except Exception as e:
            st.error(f"Erro ao inicializar o Firebase. Verifique suas credenciais nos Segredos do Streamlit: {e}")
            return None
    return firestore.client()

# --- 2. FUNÇÕES AUXILIARES ---
def extrair_texto_de_pdf(arquivo_pdf_bytes):
    try:
        arquivo_em_memoria = BytesIO(arquivo_pdf_bytes)
        leitor_pdf = PyPDF2.PdfReader(arquivo_em_memoria)
        texto_completo = ""
        for pagina in leitor_pdf.pages:
            texto_extraido = pagina.extract_text()
            if texto_extraido:
                texto_completo += texto_extraido + "\n"
        return texto_completo
    except Exception:
        return None

# --- 3. LÓGICA DE NAVEGAÇÃO (TELAS) ---
def render_home():
    st.title("Sistema de Gestão de Laudos Periciais")
    st.header("Selecione o Local da Perícia")
    if st.button("17ª Vara Federal - Juazeiro", use_container_width=True):
        st.session_state.view = 'date_selection'
        st.session_state.location_id = '17a_vara_juazeiro'
        st.session_state.location_name = '17ª Vara Federal - Juazeiro'
        st.rerun()

def render_date_selection():
    st.title(st.session_state.location_name)
    selected_date = st.date_input("Selecione a data das perícias:", datetime.date.today(), format="DD/MM/YYYY")
    col1, col2 = st.columns([1, 0.2])
    with col1:
        if st.button("Confirmar Data e Ver Processos", use_container_width=True):
            st.session_state.view = 'process_list'
            st.session_state.selected_date = selected_date.strftime("%Y-%m-%d")
            st.rerun()
    with col2:
        if st.button("Voltar", use_container_width=True):
            st.session_state.view = 'home'
            st.rerun()

def render_process_list():
    db = init_firestore()
    if not db: return

    st.title(f"Processos para {st.session_state.selected_date}")
    st.subheader(f"Local: {st.session_state.location_name}")
    
    with st.form("add_process_form", clear_on_submit=True):
        st.write("**Adicionar Novo Processo**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            process_number = st.text_input("Número do Processo")
        with col2:
            author_name = st.text_input("Nome da Parte Autora")
        with col3:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Adicionar")
    
    if submitted and process_number and author_name:
        process_data = {"number": process_number, "author": author_name, "status": "Pendente", "pdf_uploaded": False}
        db.collection("locations").document(st.session_state.location_id).collection("schedules").document(st.session_state.selected_date).collection("processes").add(process_data)
        st.success(f"Processo de {author_name} adicionado com sucesso!")

    st.divider()

    st.header("Lista de Perícias Agendadas")
    processes_ref = db.collection("locations").document(st.session_state.location_id).collection("schedules").document(st.session_state.selected_date).collection("processes").stream()
    processes = [proc for proc in processes_ref]

    if not processes:
        st.info("Nenhum processo agendado para esta data. Adicione um processo acima.")
    else:
        for proc in processes:
            proc_data = proc.to_dict()
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**Autor(a):** {proc_data.get('author')}")
                    st.write(f"**Processo:** {proc_data.get('number')}")
                with col2:
                    uploaded_file = st.file_uploader("Carregar PDF", type="pdf", key=f"uploader_{proc.id}")
                    if uploaded_file:
                        st.success(f"PDF '{uploaded_file.name}' carregado!")
                with col3:
                    if st.button("Gerar Laudo", key=f"laudo_{proc.id}", use_container_width=True):
                        st.session_state.view = 'laudo_generation'
                        st.session_state.selected_process_id = proc.id
                        st.session_state.selected_process_data = proc_data
                        st.rerun()

    if st.button("Voltar para o Calendário"):
        st.session_state.view = 'date_selection'
        st.rerun()

def render_laudo_generation():
    st.title("Geração de Laudo")
    proc_data = st.session_state.selected_process_data
    st.subheader(f"Analisando: {proc_data.get('author')} - Proc. {proc_data.get('number')}")
    st.info("A interface de geração de laudo que você já conhece aparecerá aqui.")
    if st.button("Voltar para a Lista de Processos"):
        st.session_state.view = 'process_list'
        st.rerun()

# --- PONTO DE ENTRADA PRINCIPAL ---
if 'view' not in st.session_state:
    st.session_state.view = 'home'

if st.session_state.view == 'home':
    render_home()
elif st.session_state.view == 'date_selection':
    render_date_selection()
elif st.session_state.view == 'process_list':
    render_process_list()
elif st.session_state.view == 'laudo_generation':
    render_laudo_generation()
else:
    st.session_state.view = 'home'
    st.rerun()
