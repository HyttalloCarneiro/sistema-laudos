# Módulo 7: Modelos de Laudo (Padrão vs. 17ª Vara)
# Versão 1.6: Lógica de conclusão controlada pelo usuário.
# Objetivo: Garantir que a conclusão do laudo seja gerada exclusivamente
# a partir das seleções do usuário, eliminando ambiguidades da IA.

import streamlit as st
import google.generativeai as genai
import PyPDF2
from io import BytesIO

# --- 2. Constantes e Textos Fixos ---
QUESITOS_JUIZO_17_VARA = """
1) A parte autora é portadora de alguma doença ou sequela? Qual a doença ou sequela e desde quando (data precisa ou pelo menos aproximada)?

2) Se positiva a resposta anterior, tal doença ou sequela o(a) incapacita para o exercício de atividade laborativa? Qual a data do início da incapacidade (data precisa ou pelo menos aproximada)?

3) Se positiva a resposta anterior, trata-se de incapacidade temporária ou definitiva? A doença incapacitante é reversível, levando em conta a idade e condições socioeconômicas do periciando?

4) Caso o(a) periciando(a) seja criança ou adolescente, até dezesseis anos de idade, há limitação do desempenho de atividade e restrição da participação social, compatível com a idade?

5) Havendo incapacidade, esclareça o Sr. Perito se a incapacidade para o trabalho abrange qualquer atividade laborativa.

6) Havendo incapacidade, a parte autora (pericianda) necessita da assistência permanente de outra pessoa?

7) Preste o Sr. Perito os esclarecimentos adicionais que considerar necessários.
"""

# RESPOSTAS PADRÃO PARA QUESITOS
RESPOSTA_PADRAO_QUESITO_4 = "Quesito prejudicado, tendo em vista que o(a) periciando(a) é maior de idade."
RESPOSTA_PADRAO_QUESITO_6_NAO = "Não foi constatada a necessidade de assistência permanente de outra pessoa."
RESPOSTA_PADRAO_QUESITO_6_SIM = "Sim, foi constatada a necessidade de assistência permanente de outra pessoa."
RESPOSTA_PADRAO_QUESITO_7 = "Demais esclarecimentos prestados no tópico discursivo e demais quesitos do presente laudo."
RESPOSTA_INCAPACIDADE_TOTAL = "Reconheço a incapacidade como omniprofissional."
RESPOSTA_INCAPACIDADE_INEXISTENTE = "Não reconheço a existência de incapacidade para o trabalho."
TEMPLATE_INCAPACIDADE_PARCIAL = "Reconheço a incapacidade como multiprofissional, abrangendo sua função, qual seja '{funcao}' e demais atividades que demandem '{restricao}'."

# --- 3. Funções Auxiliares ---
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
    except Exception as e:
        st.error(f"Erro ao ler o arquivo PDF: {e}")
        return None

# --- 4. Interface do Usuário (Streamlit) ---
st.set_page_config(page_title="Gerador de Laudos Automatizado", layout="wide")
st.title("🤖 Assistente para Geração de Laudos Médicos v1.6")

# --- Coluna de Configuração (Esquerda) ---
with st.sidebar:
    st.header("1. Definição da Conclusão")
    resultado_conclusao = st.radio(
        "Resultado da Perícia:",
        ("Incapacidade Reconhecida", "Incapacidade Não Reconhecida"),
        key="resultado_conclusao"
    )

    natureza_incapacidade = ""
    duracao_meses = 0
    if resultado_conclusao == "Incapacidade Reconhecida":
        natureza_incapacidade = st.radio("Natureza da Incapacidade:", ("Temporária", "Permanente"))
        if natureza_incapacidade == "Temporária":
            duracao_meses = st.number_input("Duração da incapacidade (meses):", min_value=1, value=6)

    st.divider()

    st.header("2. Respostas Padrão para Quesitos")
    periciando_adulto = st.checkbox("Periciando é adulto (Quesito 4)?", value=True)
    assistencia_permanente = st.checkbox("Necessita de assistência permanente (Quesito 6)?", value=False)
    
    tipo_abrangencia = st.radio(
        "Abrangência da incapacidade (Quesito 5):",
        ("Analisar do documento", "Incapacidade Inexistente", "Incapacidade Total", "Incapacidade Parcial"),
        key="tipo_abrangencia",
        help="Esta opção só será usada se a incapacidade for reconhecida na conclusão."
    )

    funcao_autor = ""
    restricao_autor = ""
    if tipo_abrangencia == "Incapacidade Parcial":
        funcao_autor = st.text_input("Função do autor:", placeholder="Ex: Agricultor(a)")
        restricao_autor = st.text_input("Restrição do autor:", placeholder="Ex: esforço físico")

    st.divider()
    
    st.header("3. Configurações do Sistema")
    google_api_key = None
    try:
        google_api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("Chave de API carregada com sucesso!", icon="✅")
    except (KeyError, FileNotFoundError):
        st.warning("Chave de API não encontrada nos segredos.")
        google_api_key = st.text_input("Insira sua Chave de API do Google AI", type="password")

    st.header("4. Arquivo do Processo")
    uploaded_file = st.file_uploader("Faça o upload do documento (PDF)", type="pdf")

# --- Área Principal (Direita) ---
st.header("Quesitos para Análise")
quesitos_input = st.text_area("Quesitos Padrão (17ª Vara):", value=QUESITOS_JUIZO_17_VARA, height=350)

if st.button("Gerar Laudo Completo"):
    if not google_api_key or not uploaded_file:
        st.warning("Por favor, insira a chave de API e faça o upload de um arquivo PDF.")
    else:
        with st.spinner("Gerando laudo com base nas suas definições..."):
            try:
                # --- PASSO 1: Construir o parágrafo de conclusão com base nas seleções ---
                conclusao_texto = ""
                if resultado_conclusao == "Incapacidade Não Reconhecida":
                    conclusao_texto = "Diante do exposto na análise pericial, não foi constatada a existência de incapacidade laboral para a parte autora."
                else: # Incapacidade Reconhecida
                    if natureza_incapacidade == "Permanente":
                        conclusao_texto = "Diante do exposto na análise pericial, foi constatada a existência de incapacidade laboral de natureza permanente para a parte autora."
                    else: # Temporária
                        conclusao_texto = f"Diante do exposto na análise pericial, foi constatada a existência de incapacidade laboral de natureza temporária, com prazo de recuperação estimado em {duracao_meses} meses."

                # --- PASSO 2: Preparar as instruções para os quesitos ---
                genai.configure(api_key=google_api_key)
                texto_documento = extrair_texto_de_pdf(uploaded_file.getvalue())
                
                if texto_documento:
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    
                    instrucoes_quesitos = [
                        f"Para o quesito 7, use exclusivamente a seguinte resposta: '{RESPOSTA_PADRAO_QUESITO_7}'."
                    ]
                    quesitos_a_ignorar = ["7"]

                    if periciando_adulto:
                        instrucoes_quesitos.append(f"Para o quesito 4, use a resposta: '{RESPOSTA_PADRAO_QUESITO_4}'.")
                        quesitos_a_ignorar.append("4")
                    
                    if assistencia_permanente:
                        instrucoes_quesitos.append(f"Para o quesito 6, use a resposta: '{RESPOSTA_PADRAO_QUESITO_6_SIM}'.")
                    else:
                        instrucoes_quesitos.append(f"Para o quesito 6, use a resposta: '{RESPOSTA_PADRAO_QUESITO_6_NAO}'.")
                    quesitos_a_ignorar.append("6")

                    if tipo_abrangencia != "Analisar do documento":
                        quesitos_a_ignorar.append("5")
                        if tipo_abrangencia == "Incapacidade Inexistente":
                            instrucoes_quesitos.append(f"Para o quesito 5, use a resposta: '{RESPOSTA_INCAPACIDADE_INEXISTENTE}'.")
                        elif tipo_abrangencia == "Incapacidade Total":
                            instrucoes_quesitos.append(f"Para o quesito 5, use a resposta: '{RESPOSTA_INCAPACIDADE_TOTAL}'.")
                        elif tipo_abrangencia == "Incapacidade Parcial":
                            if funcao_autor and restricao_autor:
                                resposta_parcial = TEMPLATE_INCAPACIDADE_PARCIAL.format(funcao=funcao_autor, restricao=restricao_autor)
                                instrucoes_quesitos.append(f"Para o quesito 5, use a resposta: '{resposta_parcial}'.")
                            else:
                                st.warning("Para incapacidade parcial, preencha os campos 'Função' e 'Restrição'.")
                                st.stop()
                    
                    # --- PASSO 3: Montar o prompt final para a IA ---
                    prompt_final = f"""
                    Você é um assistente especialista em laudos periciais. Sua tarefa é estruturar um laudo completo em duas partes, seguindo as instruções rigorosamente.

                    ### TAREFA 1: CONCLUSÃO
                    Apresente o seguinte parágrafo como a conclusão do laudo. Não modifique ou adicione nada a este texto.
                    ---
                    {conclusao_texto}
                    ---

                    ### TAREFA 2: RESPOSTA AOS QUESITOS
                    Abaixo da conclusão, responda aos quesitos listados, numerando cada resposta.
                    
                    **Instruções Especiais para os Quesitos:**
                    {chr(10).join(f'- {inst}' for inst in instrucoes_quesitos)}
                    - Para os demais quesitos (que não sejam {', '.join(sorted(list(set(quesitos_a_ignorar))))}), baseie-se exclusivamente no documento de referência para formular suas respostas.

                    **Documento de Referência:**
                    ---
                    {texto_documento}
                    ---
                    **Quesitos:**
                    ---
                    {quesitos_input}
                    ---
                    """

                    response = model.generate_content(prompt_final)
                    
                    st.success("Laudo gerado com sucesso!")
                    st.markdown("---")
                    st.header("Resultado da Análise")
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"Ocorreu um erro durante a geração do laudo: {e}")

st.info("Lembre-se: Este é um rascunho gerado por IA. Sempre revise e valide as informações cuidadosamente antes de qualquer uso oficial.", icon="⚠️")
