# Sistema de Gestão de Laudos Periciais
# Versão 5.3: Corrige o fluxo de upload de PDF, otimiza a seleção de horário e reintroduz funcionalidades de gestão.
# Objetivo: Implementar um fluxo de trabalho robusto com upload único de ficheiro
# que persiste entre as telas e melhora a interface de agendamento.

import streamlit as st
import google.generativeai as genai
import PyPDF2
from io import BytesIO
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json

# --- 1. CONSTANTES E TEXTOS FIXOS ---
# (As constantes de quesitos e respostas padrão permanecem as mesmas)
QUESITOS_JUIZ_17_VARA = """
1) A parte autora é portadora de alguma doença ou sequela? Qual a doença ou sequela e desde quando (data precisa ou pelo menos aproximada)?
2) Se positiva a resposta anterior, tal doença ou sequela o(a) incapacita para o exercício de atividade laborativa? Qual a data do início da incapacidade (data precisa ou pelo menos aproximada)?
3) Se positiva a resposta anterior, trata-se de incapacidade temporária ou definitiva? A doença incapacitante é reversível, levando em conta a idade e condições socioeconômicas do periciando?
4) Caso o(a) periciando(a) seja criança ou adolescente, até dezesseis anos de idade, há limitação do desempenho de atividade e restrição da participação social, compatível com a idade?
5) Havendo incapacidade, esclareça o Sr. Perito se a incapacidade para o trabalho abrange qualquer atividade laborativa.
6) Havendo incapacidade, a parte autora (pericianda) necessita da assistência permanente de outra pessoa?
7) Preste o Sr. Perito os esclarecimentos adicionais que considerar necessários.
"""
QUESITOS_REU_INSS = """
SOBRE A IDENTIFICAÇÃO DO PERICIANDO E DO PERITO:
1) Quais os documentos de identificação com foto (RG, Carteira de Motorista, Carteira Profissional etc.) que foram apresentados ao Sr. Perito, para se comprovar que de fato o autor da ação é aquele que se apresenta para a realização da Perícia Médica?
2) O Periciando possui algum grau de parentesco ou já foi atendido anteriormente pelo Sr. Perito? Se há grau de parentesco, qual?
SOBRE A EXISTÊNCIA DE EVENTUAL ENFERMIDADE (DOENÇA):
3) Quais os sintomas, os sinais e os exames realizados que comprovam o diagnóstico?
SOBRE A EXISTÊNCIA DE EVENTUAL INCAPACIDADE LABORATIVA:
4) Em caso de incapacidade, informe o Sr. Perito se ela é PERMANENTE ou TEMPORÁRIA. (...)
5) Em caso de incapacidade, ela é para qualquer atividade física e laborativa (INCAPACIDADE TOTAL) ou somente para algumas atividades laborais (INCAPACIDADE PARCIAL)? (...)
6) Na época da cessação/indeferimento (DCB/DER) do benefício na esfera administrativa, o autor apresentava o mesmo estado atual? (...)
7) Havendo incapacidade, o autor estaria apto a submeter-se a REABILITAÇÃO profissional para o exercício de outras atividades que lhe garantissem a subsistência? (...)
8) Há NEXO CAUSAL entre a enfermidade/lesão constatada e a atividade profissional do autor? (...)
9) Indique o expert judicial OUTRAS CONSIDERAÇÕES que entender necessárias e complementares ao caso em foco.
"""
RESPOSTA_PADRAO_JUIZ_4 = "Quesito prejudicado, tendo em vista que o(a) periciando(a) é maior de idade."
RESPOSTA_JUIZ_5_PREJUDICADO = "Prejudicado, não reconhecida incapacidade laboral da parte autora."
RESPOSTA_PADRAO_JUIZ_6_NAO = "Não foi constatada a necessidade de assistência permanente de outra pessoa."
RESPOSTA_PADRAO_JUIZ_6_SIM = "Sim, foi constatada a necessidade de assistência permanente de outra pessoa."
RESPOSTA_PADRAO_JUIZ_7 = "Demais esclarecimentos prestados no tópico discursivo e demais quesitos do presente laudo."
RESPOSTA_PADRAO_REU_1 = "Identificado por documento civil exposto na apresentação deste laudo."
RESPOSTA_PADRAO_REU_2 = "Não, para ambas indagações."
RESPOSTA_PADRAO_REU_9 = "Demais considerações prestadas no tópico discursivo e demais quesitos do presente laudo."
RESPOSTA_INCAPACIDADE_TOTAL = "Reconheço a incapacidade como omniprofissional."
RESPOSTA_INCAPACIDADE_UNIPROFISSIONAL = "Reconheço a incapacidade como uniprofissional, exclusivamente para o exercício de sua atividade habitual."
TEMPLATE_INCAPACIDADE_PARCIAL = "Reconheço a incapacidade como multiprofissional, abrangendo sua função, qual seja '{funcao}' e demais atividades que demandem '{restricao}'."

# --- 2. FUNÇÕES E CONFIGURAÇÕES GLOBAIS ---
def init_firestore():
    if not firebase_admin._apps:
        try:
            creds_dict = dict(st.secrets["firebase_credentials"])
            creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)
        except Exception as e:
            st.error(f"Erro fatal ao inicializar o Firebase: {e}")
            st.stop()
    return firestore.client()

def extrair_texto_de_pdf(arquivo_pdf_bytes):
    try:
        arquivo_em_memoria = BytesIO(arquivo_pdf_bytes)
        leitor_pdf = PyPDF2.PdfReader(arquivo_em_memoria)
        return "".join(page.extract_text() for page in leitor_pdf.pages if page.extract_text())
    except Exception:
        return None

def gerar_horarios():
    """Gera uma lista de horários de 15 em 15 minutos, das 08:00 às 16:45."""
    horarios = []
    for hora in range(8, 17):
        for minuto in range(0, 60, 15):
            if hora == 16 and minuto > 45:
                break
            horarios.append(f"{hora:02d}:{minuto:02d}")
    return horarios

# --- 3. TELAS DA APLICAÇÃO ---

def render_home():
    st.title("Sistema de Gestão de Laudos Periciais")
    st.header("Selecione o Local da Perícia")
    locais = {
        "17ª Vara Federal - Juazeiro": "17a_vara_juazeiro",
        "25ª Vara Federal - Crato": "25a_vara_crato",
        "Vara do Trabalho - Juazeiro": "vt_juazeiro"
    }
    for nome, id in locais.items():
        if st.button(nome, use_container_width=True):
            st.session_state.view = 'date_selection'
            st.session_state.location_id = id
            st.session_state.location_name = nome
            st.rerun()

def render_date_selection():
    st.title(st.session_state.location_name)
    selected_date = st.date_input("Selecione a data das perícias:", datetime.date.today(), format="DD/MM/YYYY")
    if st.button("Confirmar Data e Ver Processos", use_container_width=True):
        st.session_state.view = 'process_list'
        st.session_state.selected_date = selected_date.strftime("%Y-%m-%d")
        st.rerun()
    if st.button("Voltar", use_container_width=True):
        st.session_state.view = 'home'
        st.rerun()

def render_process_list():
    db = init_firestore()
    display_date = datetime.datetime.strptime(st.session_state.selected_date, "%Y-%m-%d").strftime("%d-%m-%Y")
    st.title(f"Processos para {display_date}")
    st.subheader(f"Local: {st.session_state.location_name}")
    
    with st.expander("Adicionar Novo Processo por IA", expanded=True):
        col1, col2 = st.columns(2)
        uploaded_pdf = col1.file_uploader("1. Carregue o PDF do Processo", type="pdf", key="main_uploader")
        pericia_time = col2.selectbox("2. Selecione o Horário da Perícia", options=gerar_horarios())
        
        if st.button("3. Extrair Dados e Adicionar à Lista", use_container_width=True):
            if uploaded_pdf:
                with st.spinner("A IA está a ler o processo..."):
                    pdf_bytes = uploaded_pdf.getvalue()
                    texto_documento = extrair_texto_de_pdf(pdf_bytes)
                    if texto_documento:
                        google_api_key = st.secrets.get("GOOGLE_API_KEY")
                        genai.configure(api_key=google_api_key)
                        model = genai.GenerativeModel('gemini-1.5-pro-latest')
                        prompt = f"""Analise o texto e extraia em formato JSON: "numero_processo", "nome_autor", "tipo_processo" (AD, BPC, AA, DPVAT, IR, MED, ou Outro).\n\nTexto: {texto_documento[:10000]}"""
                        response = model.generate_content(prompt)
                        try:
                            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
                            dados_extraidos = json.loads(cleaned_response)
                            process_data = {
                                "number": dados_extraidos.get("numero_processo", "Não encontrado"),
                                "author": dados_extraidos.get("nome_autor", "Não encontrado"),
                                "time": pericia_time,
                                "type": dados_extraidos.get("tipo_processo", "Outro"),
                                "status": "Aguardando"
                            }
                            doc_ref = db.collection("locations").document(st.session_state.location_id).collection("schedules").document(st.session_state.selected_date).collection("processes").document()
                            doc_ref.set(process_data)
                            # Guarda o PDF na sessão para uso posterior
                            st.session_state[f"pdf_{doc_ref.id}"] = pdf_bytes
                            st.success(f"Processo de {process_data['author']} adicionado!")
                        except Exception as e:
                            st.error(f"A IA não conseguiu extrair os dados: {e}")
                    else:
                        st.error("Não foi possível extrair texto do PDF.")
            else:
                st.warning("Por favor, carregue um ficheiro PDF.")

    st.divider()
    st.header("Lista de Perícias Agendadas")
    
    processes_ref = db.collection("locations").document(st.session_state.location_id).collection("schedules").document(st.session_state.selected_date).collection("processes").order_by("time").stream()
    processes = list(processes_ref)
    
    if not processes:
        st.info("Nenhum processo agendado para esta data.")
    else:
        if 'delete_list' not in st.session_state: st.session_state.delete_list = []

        cols = st.columns([0.5, 2.5, 3, 1, 1, 1.5, 1.5])
        headers = ["", "Processo", "Parte", "Hora", "Tipo", "Situação", "Anexos"]
        for col, header in zip(cols, headers): col.write(f"**{header}**")

        for proc in processes:
            proc_data = proc.to_dict()
            cols = st.columns([0.5, 2.5, 3, 1, 1, 1.5, 1.5])
            
            if cols[0].checkbox("", key=f"del_{proc.id}"):
                if proc.id not in st.session_state.delete_list: st.session_state.delete_list.append(proc.id)
            else:
                if proc.id in st.session_state.delete_list: st.session_state.delete_list.remove(proc.id)
            
            if cols[1].button(proc_data.get("number", "N/A"), key=f"laudo_{proc.id}"):
                st.session_state.view = 'data_entry'
                st.session_state.selected_process_id = proc.id
                st.session_state.selected_process_data = proc_data
                st.rerun()

            cols[2].write(proc_data.get("author", "N/A"))
            cols[3].write(proc_data.get("time", "N/A"))
            cols[4].write(proc_data.get("type", "N/A"))
            cols[5].write(proc_data.get("status", "N/A"))
            
            if cols[6].button("Imagens", key=f"anexo_{proc.id}"):
                st.session_state.view = 'anexo_upload'
                st.session_state.selected_process_id = proc.id
                st.session_state.selected_process_data = proc_data
                st.rerun()

    if st.session_state.get('delete_list'):
        st.divider()
        if st.button("Excluir Processos Selecionados", type="primary"):
            for proc_id in st.session_state.delete_list:
                db.collection("locations").document(st.session_state.location_id).collection("schedules").document(st.session_state.selected_date).collection("processes").document(proc_id).delete()
            st.session_state.delete_list = []
            st.success("Processos selecionados foram excluídos.")
            st.rerun()

    if st.button("Voltar para o Calendário"):
        st.session_state.view = 'date_selection'
        st.rerun()

def render_data_entry_screen():
    st.title("Análise Pericial Detalhada")
    proc_data = st.session_state.selected_process_data
    st.subheader(f"Processo: {proc_data.get('number')}")

    # Busca o PDF guardado na sessão.
    pdf_bytes = st.session_state.get(f"pdf_{st.session_state.selected_process_id}")

    if not pdf_bytes:
        st.error("O ficheiro PDF para este processo não foi encontrado na sessão. Por favor, volte à lista e adicione o processo novamente.")
        if st.button("Voltar para a Lista de Processos"):
            st.session_state.view = 'process_list'
            st.rerun()
        st.stop()

    if 'extracted_data' not in st.session_state or st.session_state.extracted_data.get('proc_id') != st.session_state.selected_process_id:
        with st.spinner("A IA está a extrair os dados do processo..."):
            texto_documento = extrair_texto_de_pdf(pdf_bytes)
            if texto_documento:
                google_api_key = st.secrets.get("GOOGLE_API_KEY")
                genai.configure(api_key=google_api_key)
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                prompt = f"""Analise o texto e extraia em formato JSON: "nome", "nascimento", "idade", "rg", "cpf", "der", "patologias".\n\nTexto: {texto_documento[:15000]}"""
                response = model.generate_content(prompt)
                try:
                    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
                    st.session_state.extracted_data = json.loads(cleaned_response)
                    st.session_state.extracted_data['proc_id'] = st.session_state.selected_process_id
                except Exception:
                    st.error("A IA não conseguiu extrair os dados.")
                    st.session_state.extracted_data = {}
            st.rerun()

    ia_data = st.session_state.get('extracted_data', {})
    
    st.header("1. Dados Pessoais e do Processo")
    col1, col2, col3 = st.columns(3)
    col1.text_input("Autor(a):", value=ia_data.get("nome", proc_data.get("author")))
    col2.text_input("Data de Nascimento:", value=ia_data.get("nascimento"))
    col3.text_input("Idade:", value=ia_data.get("idade"))
    col1, col2, col3 = st.columns(3)
    col1.text_input("RG:", value=ia_data.get("rg"))
    col2.text_input("CPF:", value=ia_data.get("cpf"))
    col3.text_input("DER:", value=ia_data.get("der"))
    st.text_input("Profissão referida:", value="Rurícola")
    st.text_input("Histórico laboral prévio:", value="Sempre laborou na função")
    st.subheader("Escolaridade")
    edu_cols = st.columns(3)
    edu_options = ["Analfabeto", "Fundamental incompleto", "Fundamental completo", "Só assina o nome", "Médio incompleto", "Médio completo", "Não sabe informar", "Superior incompleto", "Superior completo"]
    for i, option in enumerate(edu_options): edu_cols[i % 3].checkbox(option)

    st.divider()
    st.header("2. Análise Clínica")
    st.text_area("Anamnese:", height=150)
    st.text_area("Exame Clínico:", height=150)

    st.divider()
    st.header("3. Diagnóstico e Patologias")
    st.text_area("Patologias Identificadas (CID)", value=ia_data.get("patologias", ""), height=100)
    
    st.divider()
    if st.button("Voltar para a Lista de Processos", use_container_width=True):
        st.session_state.view = 'process_list'
        if 'extracted_data' in st.session_state: del st.session_state['extracted_data']
        st.rerun()

def render_anexo_upload():
    st.title("Anexar Imagens")
    proc_data = st.session_state.selected_process_data
    st.subheader(f"Processo: {proc_data.get('number')} - {proc_data.get('author')}")
    st.file_uploader("Carregue uma ou mais imagens", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if st.button("Voltar para a Lista de Processos"):
        st.session_state.view = 'process_list'
        st.rerun()

# --- PONTO DE ENTRADA PRINCIPAL ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if st.session_state.view == 'home': render_home()
elif st.session_state.view == 'date_selection': render_date_selection()
elif st.session_state.view == 'process_list': render_process_list()
elif st.session_state.view == 'data_entry': render_data_entry_screen()
elif st.session_state.view == 'anexo_upload': render_anexo_upload()
else:
    st.session_state.view = 'home'
    st.rerun()
