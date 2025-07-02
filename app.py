# Módulo 7: Modelos de Laudo (Padrão vs. 17ª Vara)
# Versão 2.3.1: Refatoração do código para corrigir erro de execução.
# Objetivo: Simplificar a estrutura interna do código para garantir a estabilidade
# na plataforma Streamlit Cloud, mantendo a funcionalidade de laudo sequencial.

import streamlit as st
import google.generativeai as genai
import PyPDF2
from io import BytesIO

# --- 2. Constantes e Textos Fixos ---
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
        st.error(f"Erro ao ler o ficheiro PDF: {e}")
        return None

# --- 4. Interface do Utilizador (Streamlit) ---
st.set_page_config(page_title="Gerador de Laudos Automatizado", layout="wide")
st.title("🤖 Assistente para Geração de Laudos Médicos v2.3")

# --- Coluna de Configuração (Esquerda) ---
with st.sidebar:
    st.header("1. Definição da Conclusão")
    resultado_conclusao = st.radio(
        "Resultado da Perícia:",
        ("Incapacidade Reconhecida", "Incapacidade Não Reconhecida"),
        key="resultado_conclusao"
    )

    natureza_incapacidade, duracao_meses, tipo_abrangencia, funcao_autor_parcial, restricao_autor, profissao_uniprofissional_manual = "", 0, None, "", "", ""
    if resultado_conclusao == "Incapacidade Reconhecida":
        natureza_incapacidade = st.radio("Natureza da Incapacidade:", ("Temporária", "Permanente"))
        if natureza_incapacidade == "Temporária":
            duracao_meses = st.number_input("Duração da incapacidade (meses):", min_value=1, value=6)
        
        tipo_abrangencia = st.radio(
            "Abrangência da incapacidade (Quesito 5 do Juiz):",
            ("Incapacidade Total (Omniprofissional)", "Incapacidade Parcial (Multiprofissional)", "Incapacidade Uniprofissional"),
            key="tipo_abrangencia"
        )
        if tipo_abrangencia == "Incapacidade Parcial (Multiprofissional)":
            funcao_autor_parcial = st.text_input("Função do autor:", placeholder="Ex: Agricultor(a)")
            restricao_autor = st.text_input("Restrição do autor:", placeholder="Ex: esforço físico")
        elif tipo_abrangencia == "Incapacidade Uniprofissional":
            profissao_uniprofissional_manual = st.text_input("Substituir profissão (opcional):", placeholder="Ex: Doméstica")

    st.divider()

    st.header("2. Respostas Padrão Adicionais")
    periciando_adulto = st.checkbox("Periciando é adulto (Quesito 4 do Juiz)?", value=True)
    if resultado_conclusao == "Incapacidade Reconhecida":
        assistencia_permanente = st.checkbox("Necessita de assistência permanente (Quesito 6 do Juiz)?", value=False)
    else:
        assistencia_permanente = False

    st.divider()
    
    st.header("3. Configurações e Upload")
    google_api_key = st.secrets.get("GOOGLE_API_KEY") or st.text_input("Insira a sua Chave de API do Google AI", type="password")
    uploaded_file = st.file_uploader("Faça o upload do documento (PDF)", type="pdf")

# --- Lógica Principal ---
def gerar_laudo_completo():
    try:
        with st.spinner("A processar o laudo... Por favor, aguarde."):
            # --- Etapa 1: Configuração e Extração de Texto ---
            genai.configure(api_key=google_api_key)
            texto_documento = extrair_texto_de_pdf(uploaded_file.getvalue())
            if not texto_documento:
                st.error("Não foi possível extrair texto do PDF.")
                return

            model = genai.GenerativeModel('gemini-1.5-pro-latest')

            # --- Etapa 2: Extrair Quesitos do Autor ---
            prompt_extracao_autor = f"Analise o texto completo do processo a seguir. Localize a seção de 'Quesitos da Parte Autora'. Se encontrar quesitos e não houver indicação de que foram indeferidos, extraia e liste APENAS os quesitos, numerados. Se não houver quesitos da parte autora ou se foram indeferidos, responda APENAS com a palavra 'NENHUM'.\n\nTEXTO:\n{texto_documento}"
            response_autor = model.generate_content(prompt_extracao_autor)
            quesitos_autor_extraidos = response_autor.text.strip()

            # --- Etapa 3: Construir Conclusão e Instruções ---
            if resultado_conclusao == "Incapacidade Não Reconhecida":
                conclusao_texto = "Diante do exposto na análise pericial, não foi constatada a existência de incapacidade laboral para a parte autora."
            else:
                conclusao_texto = f"Diante do exposto na análise pericial, foi constatada a existência de incapacidade laboral de natureza {natureza_incapacidade.lower()}"
                conclusao_texto += f", com prazo de recuperação estimado em {duracao_meses} meses." if natureza_incapacidade == "Temporária" else "."

            instrucoes_juiz = [f"Para o quesito 7, use a resposta: '{RESPOSTA_PADRAO_JUIZ_7}'."]
            if periciando_adulto:
                instrucoes_juiz.append(f"Para o quesito 4, use a resposta: '{RESPOSTA_PADRAO_JUIZ_4}'.")
            
            if resultado_conclusao == "Incapacidade Não Reconhecida":
                instrucoes_juiz.append(f"Para o quesito 5, use a resposta: '{RESPOSTA_JUIZ_5_PREJUDICADO}'.")
                instrucoes_juiz.append(f"Para o quesito 6, use a resposta: '{RESPOSTA_JUIZ_5_PREJUDICADO}'.")
            else:
                instrucoes_juiz.append(f"Para o quesito 6, use a resposta: '{RESPOSTA_PADRAO_JUIZ_6_SIM if assistencia_permanente else RESPOSTA_PADRAO_JUIZ_6_NAO}'.")
                if tipo_abrangencia == "Incapacidade Total (Omniprofissional)":
                    instrucoes_juiz.append(f"Para o quesito 5, use a resposta: '{RESPOSTA_INCAPACIDADE_TOTAL}'.")
                elif tipo_abrangencia == "Incapacidade Uniprofissional":
                    instrucoes_juiz.append(f"Para o quesito 5, use a resposta: '{RESPOSTA_INCAPACIDADE_UNIPROFISSIONAL}'.")
                elif tipo_abrangencia == "Incapacidade Parcial (Multiprofissional)":
                    resposta_parcial = TEMPLATE_INCAPACIDADE_PARCIAL.format(funcao=funcao_autor_parcial, restricao=restricao_autor)
                    instrucoes_juiz.append(f"Para o quesito 5, use a resposta: '{resposta_parcial}'.")

            instrucoes_reu = [
                f"Para o quesito 1, use a resposta: '{RESPOSTA_PADRAO_REU_1}'.",
                f"Para o quesito 2, use a resposta: '{RESPOSTA_PADRAO_REU_2}'.",
                f"Para o quesito 9, use a resposta: '{RESPOSTA_PADRAO_REU_9}'."
            ]

            secao_autor = "### RESPOSTA AOS QUESITOS DA PARTE AUTORA\n\nNão foram apresentados quesitos pela parte autora ou os mesmos foram indeferidos."
            if quesitos_autor_extraidos.upper() != 'NENHUM':
                secao_autor = f"### RESPOSTA AOS QUESITOS DA PARTE AUTORA\nResponda aos seguintes quesitos da parte autora, que foram extraídos do documento, baseando-se no mesmo documento de referência.\n\nQuesitos do Autor:\n---\n{quesitos_autor_extraidos}\n---"

            # --- Etapa 4: Montar o Prompt Final e Gerar ---
            prompt_final = f"""
            Você é um assistente especialista em laudos periciais. A sua tarefa é estruturar um laudo completo com as seções abaixo, seguindo as instruções rigorosamente.

            ### CONCLUSÃO
            {conclusao_texto}

            ### RESPOSTA AOS QUESITOS DO JUÍZO
            Responda aos quesitos do juízo abaixo.
            **Instruções Especiais para os Quesitos do Juízo:**
            {chr(10).join(f'- {inst}' for inst in instrucoes_juiz)}
            - Para os demais quesitos, baseie-se no documento de referência.
            **Quesitos do Juízo:**
            ---
            {QUESITOS_JUIZ_17_VARA}
            ---

            {secao_autor}

            ### RESPOSTA AOS QUESITOS DO RÉU
            Responda aos quesitos do réu abaixo.
            **Instruções Especiais para os Quesitos do Réu:**
            {chr(10).join(f'- {inst}' for inst in instrucoes_reu)}
            - Para os demais quesitos, baseie-se no documento de referência.
            **Quesitos do Réu:**
            ---
            {QUESITOS_REU_INSS}
            ---

            **Documento de Referência para Análise:**
            ---
            {texto_documento}
            ---
            """
            response = model.generate_content(prompt_final)
            
            st.success("Laudo gerado com sucesso!")
            st.markdown("---")
            st.header("Resultado da Análise")
            st.markdown(response.text)

    except Exception as e:
        st.error(f"Ocorreu um erro durante a geração do laudo: {e}")

if st.button("Gerar Laudo Completo"):
    if not google_api_key or not uploaded_file:
        st.warning("Por favor, insira a chave de API e faça o upload de um ficheiro PDF.")
    else:
        gerar_laudo_completo()
