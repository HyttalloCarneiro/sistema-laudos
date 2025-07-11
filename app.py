import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import json
import locale
import PyPDF2
import re
import io
import pdfplumber
import openai

# Configuração da página
st.set_page_config(
    page_title="Sistema de Laudos Periciais",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurar locale para português (se disponível)
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except:
        pass

# Nomes dos meses em português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Dias da semana em português
DIAS_SEMANA_PT = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

# Locais de atuação federais (fixos)
LOCAIS_FEDERAIS = [
    "15ª Vara Federal (Sousa)",
    "17ª Vara Federal (Juazeiro do Norte)",
    "20ª Vara Federal (Salgueiro)",
    "25ª Vara Federal (Iguatu)",
    "27ª Vara Federal (Ouricuri)"
]

# Tipos de perícia
TIPOS_PERICIA = [
    "Auxílio Doença (AD)",
    "Auxílio Acidente (AA)",
    "Benefício de Prestação Continuada (BPC)",
    "Seguro DPVAT (DPVAT)",
    "Fornecimento de medicação (MED)",
    "Imposto de renda (IR)",
    "Interdição (INT)",
    "Erro médico (ERRO)"
]

# Situações do processo
SITUACOES_PROCESSO = [
    "Pré-laudo",
    "Em produção",
    "Concluído"
]

# Permissões padrão para assistentes
PERMISSOES_ASSISTENTE = {
    "visualizar_calendario": True,
    "agendar_pericias": True,
    "editar_pericias": False,
    "deletar_pericias": False,
    "visualizar_todas_pericias": True,
    "filtrar_pericias": True,
    "alterar_propria_senha": True,
    "visualizar_locais": True,
    "gerenciar_usuarios": False,
    "acessar_configuracoes_avancadas": False,
    "gerenciar_locais_estaduais": False,
    "gerenciar_processos": True,
    "upload_processos": True
}

def extract_text_from_pdf(pdf_file):
    """Extrai texto de um arquivo PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        # Extrair texto de todas as páginas
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        st.error(f"❌ Erro ao extrair texto do PDF: {str(e)}")
        return None

def extract_process_data(text):
    """Extrai dados do processo a partir do texto do PDF"""
    if not text:
        return None
    
    # Padrões de regex para extrair informações
    patterns = {
        'numero_processo': [
            r'(?:Processo|PROCESSO|Nº|N°|Número)[\s\.:]*(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})',
            r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})',
            r'(?:Autos|AUTOS)[\s\.:]*(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})',
            r'(\d{4}\.\d{2}\.\d{2}\.\d{6}-\d)',
            r'(\d{4}\.\d{2}\.\d{2}\.\d{4}-\d{2})'
        ],
        'nome_parte': [
            r'(?:Autor|AUTOR|Requerente|REQUERENTE|Parte|PARTE)[\s\.:]*([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç\s]+)',
            r'(?:Nome|NOME)[\s\.:]*([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç\s]+)',
            r'(?:Periciando|PERICIANDO)[\s\.:]*([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç\s]+)'
        ]
    }
    
    extracted_data = {}
    
    # Extrair número do processo
    for pattern in patterns['numero_processo']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['numero_processo'] = match.group(1)
            break
    
    # Extrair nome da parte
    for pattern in patterns['nome_parte']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            # Limpar o nome (remover quebras de linha e espaços extras)
            nome = re.sub(r'\s+', ' ', nome)
            # Limitar o tamanho do nome
            if len(nome) > 50:
                nome = nome[:50] + "..."
            extracted_data['nome_parte'] = nome
            break
    
    # Tentar determinar o tipo de perícia baseado no conteúdo
    tipo_pericia = "Auxílio Doença (AD)"  # Padrão
    
    if re.search(r'auxílio.?acidente|acidente.?trabalho', text, re.IGNORECASE):
        tipo_pericia = "Auxílio Acidente (AA)"
    elif re.search(r'bpc|benefício.?prestação.?continuada|loas', text, re.IGNORECASE):
        tipo_pericia = "Benefício de Prestação Continuada (BPC)"
    elif re.search(r'dpvat|seguro.?obrigatório', text, re.IGNORECASE):
        tipo_pericia = "Seguro DPVAT (DPVAT)"
    elif re.search(r'medicação|medicamento|fornecimento', text, re.IGNORECASE):
        tipo_pericia = "Fornecimento de medicação (MED)"
    elif re.search(r'imposto.?renda|ir|dedução', text, re.IGNORECASE):
        tipo_pericia = "Imposto de renda (IR)"
    elif re.search(r'interdição|curatela|incapacidade', text, re.IGNORECASE):
        tipo_pericia = "Interdição (INT)"
    elif re.search(r'erro.?médico|responsabilidade.?médica|dano.?médico', text, re.IGNORECASE):
        tipo_pericia = "Erro médico (ERRO)"
    
    extracted_data['tipo_pericia'] = tipo_pericia
    
    return extracted_data

def format_date_br(date_str):
    """Converte data de YYYY-MM-DD para DD-MM-YYYY"""
    if isinstance(date_str, str) and len(date_str) == 10:
        year, month, day = date_str.split('-')
        return f"{day}-{month}-{year}"
    return date_str

def format_date_iso(date_str):
    """Converte data de DD-MM-YYYY para YYYY-MM-DD"""
    if isinstance(date_str, str) and len(date_str) == 10 and '-' in date_str:
        parts = date_str.split('-')
        if len(parts) == 3:
            if len(parts[0]) == 2:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
            else:
                return date_str
    return date_str

def init_session_data():
    """Inicializa dados na sessão do Streamlit"""
    if 'users' not in st.session_state:
        st.session_state.users = {
            "admin": {
                "password": "admin123",
                "role": "administrador",
                "name": "Dr. Hyttallo",
                "permissoes": {}
            }
        }
    
    if 'pericias' not in st.session_state:
        st.session_state.pericias = {}
    
    if 'processos' not in st.session_state:
        st.session_state.processos = {}
    
    if 'locais_estaduais' not in st.session_state:
        st.session_state.locais_estaduais = []
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None
    
    if 'show_user_management' not in st.session_state:
        st.session_state.show_user_management = False
    
    if 'show_change_password' not in st.session_state:
        st.session_state.show_change_password = False
    
    if 'current_local_filter' not in st.session_state:
        st.session_state.current_local_filter = None
    
    if 'show_estaduais_management' not in st.session_state:
        st.session_state.show_estaduais_management = False
    
    if 'selected_date_local' not in st.session_state:
        st.session_state.selected_date_local = None

def authenticate_user(username, password):
    """Autentica usuário"""
    if username in st.session_state.users:
        if st.session_state.users[username]["password"] == password:
            return st.session_state.users[username]
    return None

def has_permission(user_info, permission):
    """Verifica se o usuário tem uma permissão específica"""
    if user_info['role'] == 'administrador':
        return True
    
    user_permissions = user_info.get('permissoes', PERMISSOES_ASSISTENTE)
    return user_permissions.get(permission, False)

def get_all_locais():
    """Retorna todos os locais (federais + estaduais) em ordem alfabética"""
    estaduais_ordenados = sorted(st.session_state.locais_estaduais)
    return LOCAIS_FEDERAIS + estaduais_ordenados

def create_calendar_view(year, month):
    """Cria visualização do calendário em português"""
    cal = calendar.monthcalendar(year, month)
    month_name = MESES_PT[month]
    
    st.subheader(f"📅 {month_name} {year}")
    
    # Cabeçalho dos dias da semana em português
    cols = st.columns(7)
    for i, day in enumerate(DIAS_SEMANA_PT):
        cols[i].markdown(f"**{day}**")
    
    # Dias do mês
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                
                # Verificar se há perícias neste dia
                pericias_do_dia = []
                for chave, info in st.session_state.pericias.items():
                    if '_' in chave:
                        data_chave = chave.split('_')[0]
                    else:
                        data_chave = chave
                    
                    if data_chave == date_str:
                        pericias_do_dia.append(info['local'])
                
                if pericias_do_dia:
                    # Mostrar quantas perícias há no dia
                    num_pericias = len(pericias_do_dia)
                    if num_pericias == 1:
                        local_short = pericias_do_dia[0].split('(')[0].strip()[:10]
                        cols[i].button(
                            f"**{day}**\n📍 {local_short}",
                            key=f"day_{date_str}",
                            help=f"Perícia em: {pericias_do_dia[0]}",
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        cols[i].button(
                            f"**{day}**\n📍 {num_pericias} locais",
                            key=f"day_{date_str}",
                            help=f"Perícias em: {', '.join(pericias_do_dia)}",
                            type="primary",
                            use_container_width=True
                        )
                else:
                    if cols[i].button(f"{day}", key=f"day_{date_str}", use_container_width=True):
                        st.session_state.selected_date = date_str

def show_local_specific_view(local_name):
    """Mostra visualização específica de um local"""
    st.markdown(f"## 📍 {local_name}")
    st.markdown("---")
    
    # Filtrar perícias deste local
    pericias_local = []
    for chave, info in st.session_state.pericias.items():
        if info['local'] == local_name:
            if '_' in chave:
                data_chave = chave.split('_')[0]
            else:
                data_chave = chave
            
            pericias_local.append({
                'Data': format_date_br(data_chave),
                'Local': info['local'],
                'Observações': info.get('observacoes', ''),
                'Criado por': info.get('criado_por', 'N/A'),
                'Data_Sort': data_chave,
                'Data_ISO': data_chave
            })
    
    if pericias_local:
        # Separar por futuras e passadas
        hoje = datetime.now().date()
        
        futuras = []
        passadas = []
        
        for pericia in pericias_local:
            data_pericia = datetime.strptime(pericia['Data_Sort'], '%Y-%m-%d').date()
            if data_pericia >= hoje:
                futuras.append(pericia)
            else:
                passadas.append(pericia)
        
        # Mostrar perícias futuras com datas clicáveis
        if futuras:
            st.markdown("### 📅 Perícias Agendadas")
            
            for pericia in sorted(futuras, key=lambda x: x['Data_Sort']):
                col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
                
                with col1:
                    # Data clicável
                    if st.button(f"📅 {pericia['Data']}", key=f"date_click_{pericia['Data_ISO']}_{local_name}"):
                        st.session_state.selected_date_local = f"{pericia['Data_ISO']}_{local_name}"
                        st.rerun()
                
                with col2:
                    st.write(f"**Local:** {local_name}")
                
                with col3:
                    st.write(f"**Obs:** {pericia['Observações']}")
                
                with col4:
                    # Contar processos para esta data/local
                    key_processos = f"{pericia['Data_ISO']}_{local_name}"
                    num_processos = len(st.session_state.processos.get(key_processos, []))
                    st.write(f"**Processos:** {num_processos}")
        
        # Mostrar perícias passadas
        if passadas:
            st.markdown("### 📋 Histórico de Perícias")
            df_passadas = pd.DataFrame(passadas)
            df_passadas = df_passadas.sort_values('Data_Sort', ascending=False)
            df_passadas = df_passadas.drop(['Data_Sort', 'Data_ISO'], axis=1)
            st.dataframe(df_passadas, use_container_width=True)
    else:
        st.info(f"📭 Nenhuma perícia agendada para {local_name}")
    
    # Estatísticas do local
    st.markdown("### 📊 Estatísticas")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_pericias = len(pericias_local)
        st.metric("Total de Perícias", total_pericias)
    
    with col2:
        hoje = datetime.now().date()
        futuras_count = len([p for p in pericias_local if datetime.strptime(p['Data_Sort'], '%Y-%m-%d').date() >= hoje])
        st.metric("Perícias Futuras", futuras_count)
    
    with col3:
        passadas_count = len([p for p in pericias_local if datetime.strptime(p['Data_Sort'], '%Y-%m-%d').date() < hoje])
        st.metric("Perícias Realizadas", passadas_count)

def show_processos_view(data_iso, local_name):
    """Mostra a tela de gerenciamento de processos para uma data/local específico"""
    data_br = format_date_br(data_iso)
    st.markdown(f"## 📋 Processos - {data_br}")
    st.markdown(f"**Local:** {local_name}")
    
    # Botão para voltar
    if st.button("← Voltar para " + local_name):
        st.session_state.selected_date_local = None
        st.rerun()
    
    st.markdown("---")
    
    # Chave para identificar os processos desta data/local
    key_processos = f"{data_iso}_{local_name}"
    
    # Inicializar lista de processos se não existir
    if key_processos not in st.session_state.processos:
        st.session_state.processos[key_processos] = []
    
    # Seção de Upload de PDF
    if has_permission(st.session_state.user_info, 'upload_processos'):
        with st.expander("📄 Upload de Processo (PDF)", expanded=True):
            st.markdown("**Faça o upload do arquivo PDF do processo para extrair automaticamente os dados principais.**")
            
            uploaded_file = st.file_uploader(
                "Selecione o arquivo PDF do processo",
                type=['pdf'],
                key=f"upload_{key_processos}"
            )
            
            if uploaded_file is not None:
                # Extrair texto do PDF
                with st.spinner("🔍 Analisando o arquivo PDF..."):
                    text = extract_text_from_pdf(uploaded_file)
                
                if text:
                    # Extrair dados do processo
                    extracted_data = extract_process_data(text)
                    
                    if extracted_data:
                        st.success("✅ Dados extraídos com sucesso!")
                        
                        # Mostrar dados extraídos em um formulário editável
                        with st.form(f"process_from_pdf_{key_processos}"):
                            st.markdown("#### 📝 Dados Extraídos - Confirme ou Edite")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                numero_processo = st.text_input(
                                    "Número do Processo",
                                    value=extracted_data.get('numero_processo', ''),
                                    help="Número extraído automaticamente do PDF"
                                )
                                nome_parte = st.text_input(
                                    "Nome da Parte",
                                    value=extracted_data.get('nome_parte', ''),
                                    help="Nome extraído automaticamente do PDF"
                                )
                                horario = st.time_input("Horário", value=datetime.strptime("09:00", "%H:%M").time())
                            
                            with col2:
                                tipo_pericia = st.selectbox(
                                    "Tipo",
                                    TIPOS_PERICIA,
                                    index=TIPOS_PERICIA.index(extracted_data.get('tipo_pericia', 'Auxílio Doença (AD)')),
                                    help="Tipo identificado automaticamente baseado no conteúdo"
                                )
                                situacao = st.selectbox("Situação", SITUACOES_PROCESSO)
                            
                            # Mostrar prévia do texto extraído
                            with st.expander("📄 Prévia do Texto Extraído"):
                                st.text_area(
                                    "Texto extraído do PDF (primeiras 1000 caracteres):",
                                    value=text[:1000] + "..." if len(text) > 1000 else text,
                                    height=200,
                                    disabled=True
                                )
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.form_submit_button("✅ Adicionar Processo", type="primary"):
                                    if numero_processo and nome_parte:
                                        novo_processo = {
                                            "numero_processo": numero_processo,
                                            "nome_parte": nome_parte,
                                            "horario": horario.strftime("%H:%M"),
                                            "tipo": tipo_pericia,
                                            "situacao": situacao,
                                            "criado_por": st.session_state.username,
                                            "criado_em": datetime.now().isoformat(),
                                            "origem": "upload_pdf",
                                            "arquivo_original": uploaded_file.name
                                        }
                                        
                                        st.session_state.processos[key_processos].append(novo_processo)
                                        st.success("✅ Processo adicionado com sucesso via upload de PDF!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Número do processo e nome da parte são obrigatórios!")
                            
                            with col2:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.rerun()
                    else:
                        st.warning("⚠️ Não foi possível extrair dados suficientes do PDF. Use o formulário manual abaixo.")
                        
                        # Mostrar prévia do texto para debug
                        with st.expander("📄 Texto Extraído (para análise)"):
                            st.text_area(
                                "Texto extraído:",
                                value=text[:2000] + "..." if len(text) > 2000 else text,
                                height=300,
                                disabled=True
                            )
                else:
                    st.error("❌ Não foi possível extrair texto do PDF. Verifique se o arquivo não está protegido ou corrompido.")
    
    # Formulário manual para adicionar novo processo
    with st.expander("➕ Adicionar Processo Manualmente"):
        with st.form("add_processo_manual"):
            col1, col2 = st.columns(2)
            
            with col1:
                numero_processo = st.text_input("Número do Processo")
                nome_parte = st.text_input("Nome da Parte")
                horario = st.time_input("Horário", value=datetime.strptime("09:00", "%H:%M").time())
            
            with col2:
                tipo_pericia = st.selectbox("Tipo", TIPOS_PERICIA)
                situacao = st.selectbox("Situação", SITUACOES_PROCESSO)
            
            if st.form_submit_button("✅ Adicionar Processo"):
                if numero_processo and nome_parte:
                    novo_processo = {
                        "numero_processo": numero_processo,
                        "nome_parte": nome_parte,
                        "horario": horario.strftime("%H:%M"),
                        "tipo": tipo_pericia,
                        "situacao": situacao,
                        "criado_por": st.session_state.username,
                        "criado_em": datetime.now().isoformat(),
                        "origem": "manual"
                    }
                    
                    st.session_state.processos[key_processos].append(novo_processo)
                    st.success("✅ Processo adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Número do processo e nome da parte são obrigatórios!")
    
    # Listar processos existentes
    processos_lista = st.session_state.processos.get(key_processos, [])
    
    if processos_lista:
        st.markdown("### 📋 Processos Cadastrados")
        
        # Ordenar por horário
        processos_ordenados = sorted(processos_lista, key=lambda x: x['horario'])
        
        # Criar DataFrame para exibição
        df_processos = []
        for i, processo in enumerate(processos_ordenados):
            origem_icon = "📄" if processo.get('origem') == 'upload_pdf' else "✏️"
            df_processos.append({
                'Origem': origem_icon,
                'Horário': processo['horario'],
                'Número do Processo': processo['numero_processo'],
                'Nome da Parte': processo['nome_parte'],
                'Tipo': processo['tipo'],
                'Situação': processo['situacao']
            })
        
        df = pd.DataFrame(df_processos)
        st.dataframe(df, use_container_width=True)
        
        # Legenda para os ícones
        st.markdown("**Legenda:** 📄 = Extraído de PDF | ✏️ = Inserido manualmente")
        
        # Opções de edição/exclusão
        if has_permission(st.session_state.user_info, 'editar_pericias'):
            st.markdown("### ✏️ Editar/Excluir Processo")
            
            # Seletor de processo para editar
            opcoes_processos = [f"{p['horario']} - {p['numero_processo']} - {p['nome_parte']}" for p in processos_ordenados]
            
            if opcoes_processos:
                processo_selecionado = st.selectbox("Selecione o processo:", [""] + opcoes_processos)
                
                if processo_selecionado:
                    # Encontrar índice do processo
                    indice_processo = opcoes_processos.index(processo_selecionado)
                    processo_atual = processos_ordenados[indice_processo]
                    
                    # Mostrar informações sobre a origem do processo
                    if processo_atual.get('origem') == 'upload_pdf':
                        st.info(f"📄 Este processo foi extraído do arquivo: {processo_atual.get('arquivo_original', 'N/A')}")
                    
                    # Formulário de edição
                    with st.form("edit_processo"):
                        st.markdown("#### Editar Processo")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            novo_numero = st.text_input("Número do Processo", value=processo_atual['numero_processo'])
                            novo_nome = st.text_input("Nome da Parte", value=processo_atual['nome_parte'])
                            novo_horario = st.time_input("Horário", value=datetime.strptime(processo_atual['horario'], "%H:%M").time())
                        
                        with col2:
                            novo_tipo = st.selectbox("Tipo", TIPOS_PERICIA, index=TIPOS_PERICIA.index(processo_atual['tipo']))
                            nova_situacao = st.selectbox("Situação", SITUACOES_PROCESSO, index=SITUACOES_PROCESSO.index(processo_atual['situacao']))
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.form_submit_button("✅ Salvar Alterações", type="primary"):
                                # Encontrar o processo original na lista
                                for i, p in enumerate(st.session_state.processos[key_processos]):
                                    if (p['numero_processo'] == processo_atual['numero_processo'] and 
                                        p['nome_parte'] == processo_atual['nome_parte'] and
                                        p['horario'] == processo_atual['horario']):
                                        
                                        # Manter informações de origem
                                        processo_atualizado = {
                                            "numero_processo": novo_numero,
                                            "nome_parte": novo_nome,
                                            "horario": novo_horario.strftime("%H:%M"),
                                            "tipo": novo_tipo,
                                            "situacao": nova_situacao,
                                            "criado_por": processo_atual['criado_por'],
                                            "criado_em": processo_atual['criado_em'],
                                            "editado_por": st.session_state.username,
                                            "editado_em": datetime.now().isoformat(),
                                            "origem": processo_atual.get('origem', 'manual')
                                        }
                                        
                                        # Manter arquivo original se existir
                                        if 'arquivo_original' in processo_atual:
                                            processo_atualizado['arquivo_original'] = processo_atual['arquivo_original']
                                        
                                        st.session_state.processos[key_processos][i] = processo_atualizado
                                        break
                                
                                st.success("✅ Processo atualizado com sucesso!")
                                st.rerun()
                        
                        with col2:
                            if st.form_submit_button("🗑️ Excluir Processo", type="secondary"):
                                # Remover processo da lista
                                st.session_state.processos[key_processos] = [
                                    p for p in st.session_state.processos[key_processos]
                                    if not (p['numero_processo'] == processo_atual['numero_processo'] and 
                                           p['nome_parte'] == processo_atual['nome_parte'] and
                                           p['horario'] == processo_atual['horario'])
                                ]
                                st.success("✅ Processo excluído com sucesso!")
                                st.rerun()
        
        # Estatísticas dos processos
        st.markdown("### 📊 Estatísticas dos Processos")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Processos", len(processos_lista))
        
        with col2:
            concluidos = len([p for p in processos_lista if p['situacao'] == 'Concluído'])
            st.metric("Concluídos", concluidos)
        
        with col3:
            em_andamento = len([p for p in processos_lista if p['situacao'] in ['Pré-laudo', 'Em produção']])
            st.metric("Em Andamento", em_andamento)
        
        with col4:
            via_pdf = len([p for p in processos_lista if p.get('origem') == 'upload_pdf'])
            st.metric("Via PDF", via_pdf)
        
    else:
        st.info("📭 Nenhum processo cadastrado para esta data/local ainda.")

def main():
    """Função principal do aplicativo"""
    
    # Inicializar dados da sessão
    init_session_data()

    # Tela de login
    if not st.session_state.authenticated:
        st.title("🔐 Sistema de Laudos Periciais")
        st.markdown("### Acesso Restrito")
        
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("#### Faça seu login")
                username = st.text_input("👤 Usuário")
                password = st.text_input("🔑 Senha", type="password")
                login_button = st.form_submit_button("Entrar", use_container_width=True)
                
                if login_button:
                    user_info = authenticate_user(username, password)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
        
    else:
        # Interface principal após login
        user_info = st.session_state.user_info
        
        # Cabeçalho
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("⚖️ Sistema de Laudos Periciais")
            st.markdown(f"**Bem-vindo, {user_info['name']}** | *{user_info['role'].title()}*")
        
        with col2:
            if st.button("🚪 Sair", type="secondary"):
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.session_state.show_user_management = False
                st.session_state.show_change_password = False
                st.session_state.current_local_filter = None
                st.session_state.show_estaduais_management = False
                st.session_state.selected_date_local = None
                st.rerun()
        
        st.markdown("---")
        
        # Sidebar melhorada
        with st.sidebar:
            st.markdown("### ⚙️ Configurações")
            
            # Opção para mudar senha (disponível para todos)
            if has_permission(user_info, 'alterar_propria_senha'):
                if st.button("🔑 Mudar Senha"):
                    st.session_state.show_change_password = not st.session_state.show_change_password
                    st.session_state.current_local_filter = None
                    st.session_state.selected_date_local = None
            
            # Botão para voltar ao calendário principal
            if st.session_state.current_local_filter or st.session_state.selected_date_local:
                if st.button("🏠 Voltar ao Calendário Principal"):
                    st.session_state.current_local_filter = None
                    st.session_state.selected_date_local = None
                    st.rerun()
                st.markdown("---")
            
            # Locais de Atuação
            st.markdown("### 🏛️ Locais de Atuação")
            
            # Locais Federais
            st.markdown("#### ⚖️ Federais")
            for local in LOCAIS_FEDERAIS:
                if st.button(f"📍 {local.split('(')[0].strip()}", key=f"sidebar_{local}", use_container_width=True):
                    st.session_state.current_local_filter = local
                    st.session_state.show_user_management = False
                    st.session_state.show_change_password = False
                    st.session_state.show_estaduais_management = False
                    st.session_state.selected_date_local = None
                    st.rerun()
            
            # Locais Estaduais
            st.markdown("#### 🏛️ Estaduais")
            
            # Botão para gerenciar locais estaduais (apenas admin)
            if user_info['role'] == 'administrador':
                if st.button("⚙️ Gerenciar Locais Estaduais", use_container_width=True):
                    st.session_state.show_estaduais_management = not st.session_state.show_estaduais_management
                    st.session_state.current_local_filter = None
                    st.session_state.show_user_management = False
                    st.session_state.show_change_password = False
                    st.session_state.selected_date_local = None
                    st.rerun()
            
            # Listar locais estaduais em ordem alfabética
            locais_estaduais_ordenados = sorted(st.session_state.locais_estaduais)
            if locais_estaduais_ordenados:
                for local in locais_estaduais_ordenados:
                    if st.button(f"📍 {local}", key=f"sidebar_estadual_{local}", use_container_width=True):
                        st.session_state.current_local_filter = local
                        st.session_state.show_user_management = False
                        st.session_state.show_change_password = False
                        st.session_state.show_estaduais_management = False
                        st.session_state.selected_date_local = None
                        st.rerun()
            else:
                st.info("Nenhum local estadual cadastrado")
            
            # Administração (apenas admin)
            if user_info['role'] == 'administrador':
                st.markdown("---")
                st.markdown("### 🛠️ Administração")
                
                # Toggle para gerenciamento de usuários
                if st.button("👥 Gerenciar Usuários"):
                    st.session_state.show_user_management = not st.session_state.show_user_management
                    st.session_state.current_local_filter = None
                    st.session_state.show_estaduais_management = False
                    st.session_state.selected_date_local = None
        
        # Verificar qual tela mostrar
        if st.session_state.selected_date_local:
            # CORREÇÃO DO ERRO: Verificar se a string contém underscore antes de fazer split
            try:
                if '_' in st.session_state.selected_date_local:
                    parts = st.session_state.selected_date_local.split('_')
                    if len(parts) >= 2:
                        data_iso = parts[0]
                        local_name = '_'.join(parts[1:])  # Reconstroi o nome do local caso tenha underscores
                        show_processos_view(data_iso, local_name)
                    else:
                        st.error("❌ Erro na identificação da data/local. Retornando ao calendário.")
                        st.session_state.selected_date_local = None
                        st.rerun()
                else:
                    st.error("❌ Formato inválido para data/local. Retornando ao calendário.")
                    st.session_state.selected_date_local = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao processar data/local: {str(e)}")
                st.session_state.selected_date_local = None
                st.rerun()
        
        elif st.session_state.show_estaduais_management and user_info['role'] == 'administrador':
            # Gerenciamento de locais estaduais
            st.markdown("### 🏛️ Gerenciar Locais Estaduais")
            
            # Adicionar novo local estadual
            with st.form("add_local_estadual"):
                st.markdown("#### ➕ Adicionar Novo Local Estadual")
                novo_local = st.text_input("Nome do Local")
                
                if st.form_submit_button("Adicionar Local"):
                    if novo_local and novo_local not in st.session_state.locais_estaduais:
                        st.session_state.locais_estaduais.append(novo_local)
                        # Manter ordem alfabética
                        st.session_state.locais_estaduais.sort()
                        st.success(f"✅ Local '{novo_local}' adicionado com sucesso!")
                        st.rerun()
                    elif novo_local in st.session_state.locais_estaduais:
                        st.error("❌ Este local já existe!")
                    else:
                        st.error("❌ Por favor, insira um nome para o local!")
            
            # Listar e gerenciar locais existentes
            locais_estaduais_ordenados = sorted(st.session_state.locais_estaduais)
            if locais_estaduais_ordenados:
                st.markdown("#### 📋 Locais Estaduais Cadastrados")
                for local in locais_estaduais_ordenados:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"📍 {local}")
                    with col2:
                        if st.button("🗑️", key=f"del_estadual_{local}"):
                            st.session_state.locais_estaduais.remove(local)
                            st.success(f"Local '{local}' removido!")
                            st.rerun()
            else:
                st.info("📭 Nenhum local estadual cadastrado ainda.")
            
            st.markdown("---")
        
        elif st.session_state.show_change_password:
            # Formulário para mudar senha
            st.markdown("### 🔑 Alterar Senha")
            
            with st.form("change_password"):
                col1, col2 = st.columns(2)
                with col1:
                    current_password = st.text_input("Senha Atual", type="password")
                    new_password = st.text_input("Nova Senha", type="password")
                with col2:
                    confirm_password = st.text_input("Confirmar Nova Senha", type="password")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Alterar Senha", type="primary"):
                        if current_password == st.session_state.users[st.session_state.username]["password"]:
                            if new_password == confirm_password:
                                if len(new_password) >= 6:
                                    st.session_state.users[st.session_state.username]["password"] = new_password
                                    st.success("✅ Senha alterada com sucesso!")
                                    st.session_state.show_change_password = False
                                    st.rerun()
                                else:
                                    st.error("❌ A nova senha deve ter pelo menos 6 caracteres!")
                            else:
                                st.error("❌ As senhas não coincidem!")
                        else:
                            st.error("❌ Senha atual incorreta!")
                
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        st.session_state.show_change_password = False
                        st.rerun()
            
            st.markdown("---")
        
        elif user_info['role'] == 'administrador' and st.session_state.show_user_management:
            # Gerenciamento de usuários
            st.markdown("### 👥 Gerenciamento de Usuários")
            
            # Criar novo usuário
            with st.expander("➕ Criar Novo Usuário"):
                with st.form("create_user"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_username = st.text_input("Nome de usuário")
                        new_password = st.text_input("Senha", type="password")
                    with col2:
                        new_name = st.text_input("Nome completo")
                        new_role = st.selectbox("Perfil", ["assistente", "administrador"])
                    
                    # Configuração de permissões para assistentes
                    if new_role == "assistente":
                        st.markdown("#### 🔒 Configurar Permissões do Assistente")
                        st.markdown("*Configure quais funcionalidades este assistente poderá acessar:*")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**📅 Calendário e Perícias**")
                            perm_visualizar_calendario = st.checkbox("Visualizar calendário", value=True)
                            perm_agendar_pericias = st.checkbox("Agendar perícias", value=True)
                            perm_editar_pericias = st.checkbox("Editar perícias", value=False)
                            perm_deletar_pericias = st.checkbox("Deletar perícias", value=False)
                            perm_gerenciar_processos = st.checkbox("Gerenciar processos", value=True)
                            perm_upload_processos = st.checkbox("Upload de processos PDF", value=True)
                            
                        with col2:
                            st.markdown("**📊 Visualização e Filtros**")
                            perm_visualizar_todas_pericias = st.checkbox("Ver todas as perícias", value=True)
                            perm_filtrar_pericias = st.checkbox("Usar filtros", value=True)
                            perm_visualizar_locais = st.checkbox("Ver locais de atuação", value=True)
                            perm_alterar_propria_senha = st.checkbox("Alterar própria senha", value=True)
                            perm_gerenciar_locais_estaduais = st.checkbox("Gerenciar locais estaduais", value=False)
                    
                    if st.form_submit_button("Criar Usuário"):
                        if new_username not in st.session_state.users:
                            if len(new_password) >= 6:
                                # Configurar permissões baseadas no perfil
                                if new_role == "assistente":
                                    permissoes = {
                                        "visualizar_calendario": perm_visualizar_calendario,
                                        "agendar_pericias": perm_agendar_pericias,
                                        "editar_pericias": perm_editar_pericias,
                                        "deletar_pericias": perm_deletar_pericias,
                                        "visualizar_todas_pericias": perm_visualizar_todas_pericias,
                                        "filtrar_pericias": perm_filtrar_pericias,
                                        "alterar_propria_senha": perm_alterar_propria_senha,
                                        "visualizar_locais": perm_visualizar_locais,
                                        "gerenciar_usuarios": False,
                                        "acessar_configuracoes_avancadas": False,
                                        "gerenciar_locais_estaduais": perm_gerenciar_locais_estaduais,
                                        "gerenciar_processos": perm_gerenciar_processos,
                                        "upload_processos": perm_upload_processos
                                    }
                                else:
                                    permissoes = {}  # Admin tem todas as permissões
                                
                                st.session_state.users[new_username] = {
                                    "password": new_password,
                                    "role": new_role,
                                    "name": new_name,
                                    "permissoes": permissoes
                                }
                                st.success(f"✅ Usuário {new_username} criado com sucesso!")
                            else:
                                st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                        else:
                            st.error("❌ Usuário já existe!")
            
            # Lista de usuários existentes
            st.markdown("#### 📋 Usuários Cadastrados")
            for username, info in st.session_state.users.items():
                with st.expander(f"👤 {info['name']} ({username}) - {info['role'].title()}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Nome:** {info['name']}")
                        st.write(f"**Usuário:** {username}")
                        st.write(f"**Perfil:** {info['role'].title()}")
                        
                        # Mostrar permissões para assistentes
                        if info['role'] == 'assistente':
                            st.markdown("**Permissões ativas:**")
                            permissoes = info.get('permissoes', PERMISSOES_ASSISTENTE)
                            permissoes_ativas = [k for k, v in permissoes.items() if v]
                            if permissoes_ativas:
                                for perm in permissoes_ativas:
                                    st.write(f"• {perm.replace('_', ' ').title()}")
                            else:
                                st.write("• Nenhuma permissão ativa")
                    
                    with col2:
                        if username != st.session_state.username:
                            if st.button("🗑️ Remover", key=f"del_{username}", type="secondary"):
                                del st.session_state.users[username]
                                st.success(f"Usuário {username} removido!")
                                st.rerun()
                        else:
                            st.info("Você não pode remover seu próprio usuário")
            
            st.markdown("---")
        
        elif st.session_state.current_local_filter:
            # Visualização específica do local
            show_local_specific_view(st.session_state.current_local_filter)
        
        else:
            # Interface principal - calendário
            tab1, tab2 = st.tabs(["📅 Calendário e Perícias", "📋 Gerenciar Perícias"])
            
            with tab1:
                # Verificar permissão para visualizar calendário
                if not has_permission(user_info, 'visualizar_calendario'):
                    st.error("❌ Você não tem permissão para visualizar o calendário.")
                    return
                
                # Calendário
                col1, col2 = st.columns([2, 1])
                
                with col2:
                    st.markdown("### 🗓️ Navegação")
                    today = datetime.now()
                    selected_month = st.selectbox(
                        "Mês",
                        range(1, 13),
                        index=today.month - 1,
                        format_func=lambda x: MESES_PT[x]
                    )
                    selected_year = st.selectbox(
                        "Ano",
                        range(today.year - 1, today.year + 3),
                        index=1
                    )
                
                with col1:
                    create_calendar_view(selected_year, selected_month)
                
                # Formulário para adicionar perícia na data selecionada
                if st.session_state.selected_date and has_permission(user_info, 'agendar_pericias'):
                    st.markdown("---")
                    date_formatted = format_date_br(st.session_state.selected_date)
                    st.markdown(f"### 📝 Agendar Perícia - {date_formatted}")
                    
                    # Verificar se já há perícias nesta data
                    pericias_existentes = []
                    for chave, info in st.session_state.pericias.items():
                        if '_' in chave:
                            data_chave = chave.split('_')[0]
                        else:
                            data_chave = chave
                        
                        if data_chave == st.session_state.selected_date:
                            pericias_existentes.append(info['local'])
                    
                    if pericias_existentes:
                        st.info(f"📍 Já há perícias agendadas nesta data em: {', '.join(pericias_existentes)}")
                    
                    with st.form("add_pericia"):
                        # Apenas local e observações, sem horário
                        local_pericia = st.selectbox("Local da Perícia", get_all_locais())
                        observacoes = st.text_area("Observações (opcional)")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ Confirmar Perícia", type="primary"):
                                # Verificar se já existe perícia neste local/data
                                ja_existe = False
                                for chave, info in st.session_state.pericias.items():
                                    if '_' in chave:
                                        data_chave = chave.split('_')[0]
                                    else:
                                        data_chave = chave
                                    
                                    if data_chave == st.session_state.selected_date and info['local'] == local_pericia:
                                        ja_existe = True
                                        break
                                
                                if not ja_existe:
                                    # Criar chave única para cada perícia
                                    chave_pericia = f"{st.session_state.selected_date}_{local_pericia}"
                                    st.session_state.pericias[chave_pericia] = {
                                        "local": local_pericia,
                                        "observacoes": observacoes,
                                        "criado_por": st.session_state.username,
                                        "criado_em": datetime.now().isoformat()
                                    }
                                    st.success("✅ Perícia agendada com sucesso!")
                                    st.session_state.selected_date = None
                                    st.rerun()
                                else:
                                    st.error(f"❌ Já existe uma perícia agendada para {local_pericia} nesta data!")
                        
                        with col2:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state.selected_date = None
                                st.rerun()
                
                # Locais de atuação (mantido para compatibilidade)
                if has_permission(user_info, 'visualizar_locais'):
                    st.markdown("---")
                    st.markdown("### 🏛️ Acesso Rápido aos Locais")
                    
                    # Federais
                    st.markdown("#### ⚖️ Federais")
                    cols = st.columns(3)
                    for i, local in enumerate(LOCAIS_FEDERAIS):
                        with cols[i % 3]:
                            if st.button(f"📍 {local.split('(')[0].strip()}", key=f"quick_{local}", use_container_width=True):
                                st.session_state.current_local_filter = local
                                st.rerun()
                    
                    # Estaduais
                    locais_estaduais_ordenados = sorted(st.session_state.locais_estaduais)
                    if locais_estaduais_ordenados:
                        st.markdown("#### 🏛️ Estaduais")
                        cols = st.columns(3)
                        for i, local in enumerate(locais_estaduais_ordenados):
                            with cols[i % 3]:
                                if st.button(f"📍 {local}", key=f"quick_estadual_{local}", use_container_width=True):
                                    st.session_state.current_local_filter = local
                                    st.rerun()
            
            with tab2:
                # Verificar permissão para visualizar todas as perícias
                if not has_permission(user_info, 'visualizar_todas_pericias'):
                    st.error("❌ Você não tem permissão para visualizar todas as perícias.")
                    return
                
                st.markdown("### 📋 Gerenciar Todas as Perícias")
                
                if st.session_state.pericias:
                    # Converter para DataFrame
                    pericias_list = []
                    for chave, info in st.session_state.pericias.items():
                        # Extrair data da chave
                        if '_' in chave:
                            data = chave.split('_')[0]
                        else:
                            data = chave
                        
                        pericias_list.append({
                            'Data': format_date_br(data),
                            'Local': info['local'],
                            'Observações': info.get('observacoes', ''),
                            'Criado por': info.get('criado_por', 'N/A')
                        })
                    
                    df = pd.DataFrame(pericias_list)
                    # Ordenar por data
                    df['Data_Sort'] = df['Data'].apply(format_date_iso)
                    df = df.sort_values('Data_Sort', ascending=False).drop('Data_Sort', axis=1)
                    
                    # Filtros (se permitido)
                    if has_permission(user_info, 'filtrar_pericias'):
                        col1, col2 = st.columns(2)
                        with col1:
                            filtro_local_geral = st.selectbox(
                                "Filtrar por local",
                                ["Todos"] + get_all_locais(),
                                key="filtro_geral"
                            )
                        
                        with col2:
                            filtro_data = st.date_input("Filtrar a partir da data")
                        
                        # Aplicar filtros
                        df_filtrado = df.copy()
                        if filtro_local_geral != "Todos":
                            df_filtrado = df_filtrado[df_filtrado['Local'] == filtro_local_geral]
                        
                        if filtro_data:
                            filtro_data_str = filtro_data.strftime("%d-%m-%Y")
                            df_filtrado['Data_Compare'] = df_filtrado['Data'].apply(format_date_iso)
                            filtro_data_iso = format_date_iso(filtro_data_str)
                            df_filtrado = df_filtrado[df_filtrado['Data_Compare'] >= filtro_data_iso]
                            df_filtrado = df_filtrado.drop('Data_Compare', axis=1)
                        
                        st.dataframe(df_filtrado, use_container_width=True)
                    else:
                        st.dataframe(df, use_container_width=True)
                    
                    # Opção para deletar perícias (apenas se permitido)
                    if has_permission(user_info, 'deletar_pericias'):
                        st.markdown("#### 🗑️ Remover Perícia")
                        
                        # Criar lista de opções com datas formatadas
                        opcoes_remover = [""]
                        for chave in st.session_state.pericias.keys():
                            if '_' in chave:
                                data = chave.split('_')[0]
                            else:
                                data = chave
                            
                            data_br = format_date_br(data)
                            local = st.session_state.pericias[chave]['local']
                            opcoes_remover.append(f"{data_br} - {local}")
                        
                        data_remover_display = st.selectbox(
                            "Selecione a perícia para remover",
                            opcoes_remover
                        )
                        
                        if data_remover_display and st.button("🗑️ Confirmar Remoção", type="secondary"):
                            # Extrair a data e local da opção selecionada
                            data_br, local = data_remover_display.split(' - ', 1)
                            data_iso = format_date_iso(data_br)
                            
                            # Encontrar a chave correta
                            chave_para_remover = None
                            for chave, info in st.session_state.pericias.items():
                                if '_' in chave:
                                    data_chave = chave.split('_')[0]
                                else:
                                    data_chave = chave
                                
                                if data_chave == data_iso and info['local'] == local:
                                    chave_para_remover = chave
                                    break
                            
                            if chave_para_remover:
                                del st.session_state.pericias[chave_para_remover]
                                # Também remover processos associados se existirem
                                key_processos = f"{data_iso}_{local}"
                                if key_processos in st.session_state.processos:
                                    del st.session_state.processos[key_processos]
                                st.success("✅ Perícia removida com sucesso!")
                                st.rerun()
                else:
                    st.info("📭 Nenhuma perícia agendada ainda.")

            # --- NOVO EXPANDER: Anexar Processos em Lote ---
            import uuid
            with st.expander("📤 Anexar Processos em Lote"):
                # Inicializa dicionário de dados se não existir
                if "dados" not in st.session_state:
                    st.session_state.dados = {}
                arquivos = st.file_uploader("Selecionar arquivos PDF", type="pdf", accept_multiple_files=True, key="lote")

                if arquivos:
                    for arquivo in arquivos:
                        with pdfplumber.open(arquivo) as pdf:
                            texto = ""
                            for pagina in pdf.pages:
                                pagina_texto = pagina.extract_text()
                                if pagina_texto:
                                    texto += pagina_texto + "\n"

                        st.session_state.dados[str(uuid.uuid4())] = {
                            "nome": f"Autor {len(st.session_state.dados)+1}",
                            "numero": f"Nº {len(st.session_state.dados)+1}",
                            "tipo": st.selectbox("Tipo", ["AD", "BPC", "DPVAT"], key=arquivo.name),
                            "horario": "09:00",
                            "conteudo": texto,
                            "situacao": "Pré-laudo"
                        }
                    st.success("Processos em lote anexados com sucesso!")


# --- FINAL DO ARQUIVO: Geração de Pré-Laudos em Lote ---
if "dados" not in st.session_state:
    st.session_state.dados = {}

if st.button("🧠 Gerar Pré-Laudos em Lote"):
    st.session_state.prelaudos = []
    for proc_id, proc in list(st.session_state.dados.items()):
        mensagens = []
        if proc["tipo"] == "AD":
            prompt = "Você é um perito médico federal. Com base no processo abaixo, elabore um pré-laudo no formato de Auxílio-Doença:"
        elif proc["tipo"] == "BPC":
            prompt = "Você é um perito médico federal. Com base no processo abaixo, elabore um pré-laudo no formato de BPC:"
        elif proc["tipo"] == "DPVAT":
            prompt = "Você é um perito médico federal. Com base no processo abaixo, elabore um pré-laudo no formato de DPVAT:"
        else:
            prompt = "Elabore um pré-laudo com base no processo abaixo:"
        
        mensagens.append({"role": "system", "content": prompt})
        mensagens.append({"role": "user", "content": proc["conteudo"]})

        try:
            resposta = openai.ChatCompletion.create(
                model="gpt-4",
                messages=mensagens
            )
            prelaudo = resposta.choices[0].message.content
            st.session_state.prelaudos.append({
                "tipo": proc["tipo"],
                "numero": proc["numero"],
                "nome": proc["nome"],
                "conteudo": prelaudo
            })
            del st.session_state.dados[proc_id]
        except Exception as e:
            st.error(f"Erro ao gerar pré-laudo: {e}")

if "prelaudos" in st.session_state and st.session_state.prelaudos:
    st.header("📑 Pré-Laudos Gerados")
    for i, pl in enumerate(st.session_state.prelaudos):
        with st.expander(f"{pl['numero']} - {pl['nome']} ({pl['tipo']})"):
            st.code(pl["conteudo"])

if __name__ == "__main__":
    main()