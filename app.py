import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))
import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import calendar
from datetime import datetime, date
import json
import locale

# Ajuste dos imports dos módulos das páginas

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
    "gerenciar_processos": True
}

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
    if 'pericias_por_dia' not in st.session_state:
        st.session_state.pericias_por_dia = {}
    
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
    if 'selected_date_multilocais' not in st.session_state:
        st.session_state.selected_date_multilocais = None

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
                pericias_do_dia = st.session_state.pericias_por_dia.get(date_str, [])

                if pericias_do_dia:
                    num_pericias = len(pericias_do_dia)
                    if num_pericias == 1:
                        local_short = pericias_do_dia[0].split('(')[0].strip()[:10]
                        if cols[i].button(
                            f"**{day}**\n📍 {local_short}",
                            key=f"day_{date_str}",
                            help=f"Perícia em: {pericias_do_dia[0]}",
                            type="primary",
                            use_container_width=True
                        ):
                            st.session_state.selected_date_local = {"data": date_str, "local": pericias_do_dia[0]}
                            st.rerun()
                    else:
                        if cols[i].button(
                            f"**{day}**\n📍 {num_pericias} locais",
                            key=f"day_{date_str}",
                            help=f"Perícias em: {', '.join(pericias_do_dia)}",
                            type="primary",
                            use_container_width=True
                        ):
                            # Salva a lista de locais para esse dia em selected_date_multilocais
                            st.session_state.selected_date_multilocais = {
                                "date": date_str,
                                "locais": pericias_do_dia
                            }
                            st.session_state.selected_date = None
                            st.rerun()
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
                        st.session_state.selected_date_local = {"data": pericia['Data_ISO'], "local": local_name}
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
    # Novo: mostrar apenas "Total de Dias com Perícias"
    datas_unicas = set()
    for p in pericias_local:
        datas_unicas.add(p['Data_Sort'])
    st.metric("Total de Dias com Perícias", len(datas_unicas))

def extrair_texto_pdf(uploaded_file):
    texto = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto


def show_processos_view(data_iso, local_name):
    """Mostra a tela de gerenciamento de processos para uma data/local específico"""
    data_br = format_date_br(data_iso)
    st.markdown(f"## 📋 Processos - {data_br}")
    st.markdown(f"**Local:** {local_name}")

    # Bloco: botões para voltar e vincular outro local
    col1, col2 = st.columns([2, 2])
    with col1:
        if st.button(f"← Voltar para {local_name}"):
            st.session_state.selected_date_local = None
            st.rerun()
    with col2:
        if st.button("🔗 Vincular outro local nesta data"):
            st.session_state.show_vincular_local = True

    # Formulário de vinculação de local em data
    if st.session_state.get("show_vincular_local", False):
        st.markdown("#### 🔗 Escolher outro local para vincular nesta data")
        locais_disponiveis = [loc for loc in get_all_locais() if loc != local_name]
        novo_local = st.selectbox("Selecione o local", locais_disponiveis, key="select_novo_local")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Confirmar Vinculação"):
                # Atualiza pericias_por_dia corretamente para múltiplos locais
                if data_iso not in st.session_state.pericias_por_dia:
                    st.session_state.pericias_por_dia[data_iso] = [novo_local]
                elif novo_local not in st.session_state.pericias_por_dia[data_iso]:
                    st.session_state.pericias_por_dia[data_iso].append(novo_local)

                # Criar a nova chave da perícia vinculada e adicioná-la
                chave = f"{data_iso}_{novo_local}"
                if chave not in st.session_state.pericias:
                    st.session_state.pericias[chave] = {
                        "local": novo_local,
                        "observacoes": "",
                        "criado_por": st.session_state.username,
                        "criado_em": datetime.now().isoformat()
                    }

                st.session_state.selected_date_local = {"data": data_iso, "local": novo_local}
                st.session_state.show_vincular_local = False
                st.rerun()
        with col_v2:
            if st.button("❌ Cancelar"):
                st.session_state.show_vincular_local = False
                st.rerun()

    st.markdown("---")
    
    # Chave para identificar os processos desta data/local
    key_processos = f"{data_iso}_{local_name}"
    
    # Inicializar lista de processos se não existir
    if key_processos not in st.session_state.processos:
        st.session_state.processos[key_processos] = []
    
    # Formulário para adicionar novo processo
    with st.expander("➕ Adicionar Novo Processo"):
        with st.form("add_processo"):
            col1, col2 = st.columns(2)

            with col1:
                numero_processo = st.text_input("Número do Processo")
                nome_parte = st.text_input("Nome da Parte")
                horario = st.time_input(
                    "Horário",
                    value=datetime.strptime("09:00", "%H:%M").time()
                )

            with col2:
                tipo_pericia = st.selectbox("Tipo", TIPOS_PERICIA)
                situacao = st.selectbox("Situação", SITUACOES_PROCESSO)

            # Novo campo de upload de PDF
            uploaded_pdf = st.file_uploader("Selecionar arquivo do processo (PDF)", type=["pdf"], key="upload_pdf")

            # Verificação do intervalo permitido para o horário
            hora_min = datetime.strptime("08:00", "%H:%M").time()
            hora_max = datetime.strptime("16:45", "%H:%M").time()

            if horario < hora_min or horario > hora_max:
                st.error("❌ O horário deve estar entre 08:00 e 16:45.")

            if st.form_submit_button("✅ Adicionar Processo"):
                if numero_processo and nome_parte:
                    # Verificar se já existe processo com o mesmo horário nesta data/local
                    existe_horario = any(
                        p['horario'] == horario.strftime("%H:%M") for p in st.session_state.processos[key_processos]
                    )
                    if existe_horario:
                        st.error("❌ Já existe um processo cadastrado neste horário!")
                    elif horario < hora_min or horario > hora_max:
                        st.error("❌ O horário deve estar entre 08:00 e 16:45.")
                    else:
                        novo_processo = {
                            "numero_processo": numero_processo,
                            "nome_parte": nome_parte,
                            "horario": horario.strftime("%H:%M"),
                            "tipo": tipo_pericia,
                            "situacao": situacao,
                            "criado_por": st.session_state.username,
                            "criado_em": datetime.now().isoformat(),
                            "pdf": uploaded_pdf.read() if uploaded_pdf is not None else None,
                        }
                        st.session_state.processos[key_processos].append(novo_processo)
                        st.success("✅ Processo adicionado com sucesso!")
                        st.session_state.view = "processos"
                        st.rerun()
                        return
                else:
                    st.error("❌ Número do processo e nome da parte são obrigatórios!")
    
    # Listar processos existentes
    processos_lista = st.session_state.processos.get(key_processos, [])

    if processos_lista:
        # Tela de confirmação de ação
        if "confirm_action" in st.session_state:
            acao, chave, proc = st.session_state.confirm_action
            st.warning(f"⚠️ Deseja realmente confirmar esta ação: {acao.upper()} para o processo {proc['numero_processo']} de {proc['nome_parte']} às {proc['horario']}?")
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("✅ Sim"):
                    if acao == "ausencia":
                        # Atualizar a situação do processo para "Ausente"
                        for i, p in enumerate(st.session_state.processos[chave]):
                            if (p['numero_processo'] == proc['numero_processo'] and
                                p['nome_parte'] == proc['nome_parte'] and
                                p['horario'] == proc['horario']):
                                st.session_state.processos[chave][i]['situacao'] = 'Ausente'
                                break
                        st.success("✅ Ausência registrada com sucesso.")
                    elif acao == "excluir":
                        st.session_state.processos[chave] = [
                            p for p in st.session_state.processos[chave]
                            if not (p['numero_processo'] == proc['numero_processo'] and
                                    p['nome_parte'] == proc['nome_parte'] and
                                    p['horario'] == proc['horario'])
                        ]
                        st.success("✅ Processo excluído com sucesso!")
                    del st.session_state.confirm_action
                    st.session_state.selected_date_local = {"data": chave.split('_')[0], "local": chave.split('_')[1]}
                    st.rerun()
            with col_nao:
                if st.button("❌ Não"):
                    del st.session_state.confirm_action
                    st.rerun()
            return

        st.markdown("### 📋 Processos Cadastrados")

        # Ordenar por horário
        processos_ordenados = sorted(processos_lista, key=lambda x: x['horario'])

        # Novo cabeçalho das colunas
        header_cols = st.columns([2, 2, 3, 3, 1.5, 2, 2])
        header_cols[0].markdown("**Anexar Processo**")
        header_cols[1].markdown("**Horário**")
        header_cols[2].markdown("**Número do Processo**")
        header_cols[3].markdown("**Nome do periciando**")
        header_cols[4].markdown("**Tipo**")
        header_cols[5].markdown("**Situação**")
        header_cols[6].markdown("**Ação**")

        for idx, processo in enumerate(processos_ordenados):
            row_cols = st.columns([2, 2, 3, 3, 1.5, 2, 2])
            # BLOCO DE UPLOAD/ANEXO
            with row_cols[0]:
                # NOVA LÓGICA DE EXIBIÇÃO DO STATUS DE ANEXO (ATUALIZADO)
                if processo.get("anexo_status") == "Pronto":
                    st.write("✅ Pronto")
                elif processo.get("anexo_status") == "Aguardando":
                    st.write("⏳ Aguardando")
                elif processo.get("pdf") is not None:
                    st.write("⏳ Aguardando")
                else:
                    st.write("📎 Anexar")
            row_cols[1].write(processo['horario'])
            row_cols[2].write(processo['numero_processo'])
            row_cols[3].write(processo['nome_parte'])
            row_cols[4].write(processo['tipo'].split('(')[-1].replace(')', ''))
            row_cols[5].write(processo['situacao'])
            # Novo bloco unificado de botões de ação
            with row_cols[6]:
                col_a, col_b, col_c = st.columns([1, 1, 1])

                # Botão de redigir laudo
                with col_a:
                    if st.button("📝", key=f"redigir_{key_processos}_{idx}"):
                        # Redirecionar para a tela de edição de laudo, salvando o processo em edição
                        st.session_state.view = "editar_laudo"
                        st.session_state.processo_em_edicao = processo
                        st.rerun()

                with col_b:
                    if st.button("🚫", key=f"ausente_{key_processos}_{idx}"):
                        st.session_state.confirm_action = ("ausencia", key_processos, processo)
                        st.rerun()

                with col_c:
                    if st.button("🗑️", key=f"excluir_{key_processos}_{idx}"):
                        st.session_state.confirm_action = ("excluir", key_processos, processo)
                        st.rerun()

        # Interface de edição do laudo Auxílio-Doença (apenas se page == "editar_laudo_ad")
        if st.session_state.get("page") == "editar_laudo_ad":
            proc_info = st.session_state.get("processo_editando")
            if proc_info and proc_info["key_processos"] == key_processos:
                idx = proc_info["idx"]
                processo = processos_ordenados[idx]
                if processo.get("anexo_status") == "Pronto" and (processo.get("tipo") == "AD" or processo.get("tipo") == "Auxílio Doença (AD)"):
                    st.markdown("## ✍️ Edição do Laudo Auxílio-Doença")

                    col1_, col2_ = st.columns(2)
                    with col1_:
                        nome = st.text_input("Nome do Periciando", value=processo.get("nome", processo.get("nome_parte", "")), key=f"nome_{key_processos}_{idx}")
                        data_nascimento = st.date_input("Data de nascimento", key=f"data_nasc_{key_processos}_{idx}")

                    with col2_:
                        profissao = st.text_input("Profissão", value=processo.get("profissao", ""), key=f"profissao_{key_processos}_{idx}")
                        cid = st.text_input("CID(s) relacionado(s)", value=processo.get("cid", ""), key=f"cid_{key_processos}_{idx}")

                    st.markdown("### 🩺 Anamnese")
                    anamnese = st.text_area("Descreva os dados clínicos e históricos relevantes", value=processo.get("anamnese", ""), key=f"anamnese_{key_processos}_{idx}")

                    st.markdown("### 🧪 Exame Físico")
                    exame_fisico = st.text_area("Resultado do exame físico realizado", value=processo.get("exame_fisico", ""), key=f"exame_fisico_{key_processos}_{idx}")

                    st.markdown("### 📁 Documentos Apresentados")
                    documentos = st.text_area("Laudos, exames e atestados apresentados", value=processo.get("documentos", ""), key=f"documentos_{key_processos}_{idx}")

                    st.markdown("### 📆 Incapacidade")
                    incapacidade = st.selectbox("Houve incapacidade laboral?", ["Sim", "Não", "Parcial", "Permanente"], key=f"incapacidade_{key_processos}_{idx}", index=["Sim", "Não", "Parcial", "Permanente"].index(processo.get("incapacidade", "Sim")) if processo.get("incapacidade") in ["Sim", "Não", "Parcial", "Permanente"] else 0)
                    data_inicio = st.date_input("Data de início da incapacidade (se houver)", key=f"data_inicio_{key_processos}_{idx}")
                    data_fim = st.date_input("Data provável de término (se houver)", key=f"data_fim_{key_processos}_{idx}")

                    st.markdown("### ✉️ Resposta aos Quesitos")
                    quesitos = st.text_area("Transcreva ou cole aqui as respostas aos quesitos", value=processo.get("quesitos", ""), key=f"quesitos_{key_processos}_{idx}")

                    st.markdown("### 📝 Conclusão")
                    conclusao = st.text_area("Conclusão do perito com base nos dados acima", value=processo.get("conclusao", ""), key=f"conclusao_{key_processos}_{idx}")

                    if st.button("💾 Salvar Laudo", key=f"salvar_laudo_{key_processos}_{idx}"):
                        processo["nome"] = nome
                        processo["profissao"] = profissao
                        processo["cid"] = cid
                        processo["anamnese"] = anamnese
                        processo["exame_fisico"] = exame_fisico
                        processo["documentos"] = documentos
                        processo["incapacidade"] = incapacidade
                        processo["data_inicio"] = str(data_inicio)
                        processo["data_fim"] = str(data_fim)
                        processo["quesitos"] = quesitos
                        processo["conclusao"] = conclusao
                        st.success("Laudo salvo com sucesso.")

        # Opções de edição (mantido se necessário)
        if has_permission(st.session_state.user_info, 'editar_pericias'):
            st.markdown("### ✏️ Editar Processo")
            opcoes_processos = [f"{p['horario']} - {p['numero_processo']} - {p['nome_parte']}" for p in processos_ordenados]
            if opcoes_processos:
                processo_selecionado = st.selectbox("Selecione o processo para editar:", [""] + opcoes_processos)
                if processo_selecionado:
                    indice_processo = opcoes_processos.index(processo_selecionado)
                    processo_atual = processos_ordenados[indice_processo]
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
                                        st.session_state.processos[key_processos][i] = {
                                            "numero_processo": novo_numero,
                                            "nome_parte": novo_nome,
                                            "horario": novo_horario.strftime("%H:%M"),
                                            "tipo": novo_tipo,
                                            "situacao": nova_situacao,
                                            "criado_por": processo_atual['criado_por'],
                                            "criado_em": processo_atual['criado_em'],
                                            "editado_por": st.session_state.username,
                                            "editado_em": datetime.now().isoformat()
                                        }
                                        break
                                st.success("✅ Processo atualizado com sucesso!")
                                st.experimental_rerun()
                        with col2:
                            # Exclusão já disponível acima, pode omitir
                            pass

        # Estatísticas dos processos (ajustado)
        st.markdown("### 📊 Estatísticas de Perícias do Dia")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_a_realizar = len([p for p in processos_lista if p['situacao'] in ['Pré-laudo', 'Em produção']])
            st.metric("Total de Perícias a Realizar", total_a_realizar)
        with col2:
            total_realizadas = len([p for p in processos_lista if p['situacao'] == 'Concluído'])
            st.metric("Total de Perícias Realizadas", total_realizadas)
        with col3:
            total_ausentes = len([p for p in processos_lista if p['situacao'] == 'Ausente'])
            st.metric("Total de Ausentes", total_ausentes)

        # Bloco: Ações em Lote
        st.markdown("### 🧾 Ações em Lote")
        if st.button("🛠️ Gerar Lote de Pré-Laudos"):
            for processo in processos_ordenados:
                tipo = processo.get("tipo", "").upper()
                if tipo == "AD":
                    gerar_laudo_ad(processo=processo)
                # futuro: elif tipo == "BPC":
                #     gerar_laudo_bpc(processo=processo)
                
                processo["anexo_status"] = "Pronto"
                
                if "arquivo_path" in processo and os.path.exists(processo["arquivo_path"]):
                    os.remove(processo["arquivo_path"])
                    processo["arquivo_path"] = ""
            st.success("✅ Lote de pré-laudos gerado com sucesso!")
            st.rerun()

    else:
        st.info("📭 Nenhum processo cadastrado para esta data/local ainda.")
def main():
    """Função principal do aplicativo"""
    
    # Inicializar dados da sessão
    init_session_data()

    # Tela de login
    if st.session_state.get("pagina") == "redigir_laudo":
        if st.session_state.get("modo_redacao") == "AD":
            from laudos_ad import redigir_laudo_ad
            redigir_laudo_ad()
        elif st.session_state.get("modo_redacao") == "BPC":
            from laudos_bpc import redigir_laudo_bpc
            redigir_laudo_bpc(st.session_state.get("processo_atual"))
        return

    # Novo bloco: tela de edição de laudo
    if st.session_state.get("view") == "editar_laudo":
        editar_laudo_ad(st.session_state.processo_em_edicao)
        return

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

                # Botão para Configurações
                if st.button("⚙️ Configurações"):
                    st.session_state.pagina = "configuracoes"
        
        # Verificar qual tela mostrar
        if st.session_state.selected_date_local:
            if isinstance(st.session_state.selected_date_local, dict):
                data_iso = st.session_state.selected_date_local["data"]
                local_name = st.session_state.selected_date_local["local"]
                show_processos_view(data_iso, local_name)

        elif hasattr(st.session_state, "pagina") and st.session_state.pagina == "configuracoes":
            st.subheader("⚙️ Configurações do Sistema")

            aba = st.radio("Escolha uma categoria para gerenciar:", ["Modelos de Exame Clínico", "Modelos de Patologias"])

            if aba == "Modelos de Exame Clínico":
                st.markdown("### Modelos de Exame Clínico")
                with st.form("form_exame_clinico"):
                    novo_modelo = st.text_area("Novo modelo de exame clínico")
                    submitted = st.form_submit_button("Salvar modelo")
                    if submitted and novo_modelo.strip():
                        if "modelos_exame_clinico" not in st.session_state:
                            st.session_state.modelos_exame_clinico = []
                        st.session_state.modelos_exame_clinico.append(novo_modelo.strip())
                        st.success("Modelo salvo com sucesso!")

                if "modelos_exame_clinico" in st.session_state and st.session_state.modelos_exame_clinico:
                    st.markdown("#### Modelos Salvos")
                    for i, modelo in enumerate(st.session_state.modelos_exame_clinico):
                        st.markdown(f"**{i+1}.** {modelo}")
                        if st.button(f"Excluir modelo {i+1}", key=f"excluir_modelo_{i}"):
                            st.session_state.modelos_exame_clinico.pop(i)
                            st.experimental_rerun()

            elif aba == "Modelos de Patologias":
                st.markdown("### Modelos de Patologias")
                with st.form("form_patologias"):
                    nova_patologia = st.text_input("Nova patologia comum")
                    submitted_pat = st.form_submit_button("Salvar patologia")
                    if submitted_pat and nova_patologia.strip():
                        if "modelos_patologias" not in st.session_state:
                            st.session_state.modelos_patologias = []
                        st.session_state.modelos_patologias.append(nova_patologia.strip())
                        st.success("Patologia salva com sucesso!")

                if "modelos_patologias" in st.session_state and st.session_state.modelos_patologias:
                    st.markdown("#### Patologias Salvas")
                    for i, pat in enumerate(st.session_state.modelos_patologias):
                        st.markdown(f"**{i+1}.** {pat}")
                        if st.button(f"Excluir patologia {i+1}", key=f"excluir_patologia_{i}"):
                            st.session_state.modelos_patologias.pop(i)
                            st.experimental_rerun()

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
                                        "gerenciar_processos": perm_gerenciar_processos
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
        
        elif "⚙️ Configurações" in menu_selecionado:
            gerenciar_configuracoes()
        else:
            st.session_state['pagina'] = 'calendario'
            st.experimental_rerun()

def editar_laudo_ad(processo):
    """Renderiza a tela de redação do laudo AD em duas colunas, com informações do periciando à esquerda."""
    st.set_page_config(
        page_title="Redigir Laudo AD",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    # Preparar variáveis
    nome_parte = processo.get("nome", processo.get("nome_parte", ""))
    data_nascimento = processo.get("data_nascimento", None)
    idade = processo.get("idade", None)
    tipo = processo.get("tipo", "AD")
    historico_beneficios = processo.get("historico_beneficios", [])
    # Garantir que a chave 'der' exista, mesmo que None por padrão
    if "der" not in processo:
        processo["der"] = None
    data_str = processo.get("data", processo.get("data_pericia", None))
    hora = processo.get("horario", "")
    # data_str pode estar em vários campos, tentar obter da chave do processo se necessário
    if not data_str:
        if "key_processos" in processo:
            data_str = processo["key_processos"].split("_")[0]
    # Converter data para objeto date
    data = None
    if isinstance(data_str, date):
        data = data_str
    elif isinstance(data_str, str):
        try:
            data = datetime.strptime(data_str, "%Y-%m-%d").date()
        except Exception:
            try:
                data = datetime.strptime(data_str, "%d-%m-%Y").date()
            except Exception:
                data = None
    # Calcular idade se não fornecida
    if idade is None and data_nascimento and data:
        if isinstance(data_nascimento, str):
            try:
                if '-' in data_nascimento:
                    dt_nasc = datetime.strptime(data_nascimento, "%Y-%m-%d").date() if data_nascimento[4] == '-' else datetime.strptime(data_nascimento, "%d-%m-%Y").date()
                else:
                    dt_nasc = datetime.strptime(data_nascimento, "%d/%m/%Y").date()
            except Exception:
                dt_nasc = None
        elif isinstance(data_nascimento, date):
            dt_nasc = data_nascimento
        else:
            dt_nasc = None
        if dt_nasc:
            idade = data.year - dt_nasc.year - ((data.month, data.day) < (dt_nasc.month, dt_nasc.day))
    # Converter data_nascimento para objeto date se necessário
    if isinstance(data_nascimento, str):
        try:
            if '-' in data_nascimento:
                data_nascimento_dt = datetime.strptime(data_nascimento, "%Y-%m-%d").date() if data_nascimento[4] == '-' else datetime.strptime(data_nascimento, "%d-%m-%Y").date()
            else:
                data_nascimento_dt = datetime.strptime(data_nascimento, "%d/%m/%Y").date()
        except Exception:
            data_nascimento_dt = None
    elif isinstance(data_nascimento, date):
        data_nascimento_dt = data_nascimento
    else:
        data_nascimento_dt = None
    # Cabeçalho principal
    if data:
        st.markdown(f"## 📝 {tipo} - {data.strftime('%d-%m-%Y')} - {hora}")
    else:
        st.markdown(f"## 📝 {tipo} - {hora}")
    st.markdown("---")
    # Botão para voltar
    if st.button("⬅️ Voltar para Processos do Dia"):
        st.session_state.view = "processos"
        st.rerun()
    # Layout em duas colunas
    col_esq, col_dir = st.columns([1, 3])
    with col_esq:
        st.markdown("### ℹ️ Periciando(a)")
        st.markdown(f"**Periciando(a):** {nome_parte}")
        if data_nascimento_dt:
            st.markdown(f"**Data de nascimento:** {data_nascimento_dt.strftime('%d-%m-%Y')}")
        else:
            st.markdown("**Data de nascimento:** -")
        st.markdown(f"**Idade:** {idade if idade is not None else '-'} anos")
        st.markdown(f"**Tipo:** {tipo}")
        # DER (Data de Entrada do Requerimento)
        der_data = processo.get("der")
        if der_data:
            try:
                der_formatada = datetime.strptime(der_data, "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                der_formatada = der_data
        else:
            der_formatada = "-"
        st.markdown(f"**DER:** {der_formatada}")
        st.markdown("**Histórico de benefícios:**")
        if historico_beneficios:
            for item in historico_beneficios:
                st.markdown(f"- {item}")
        else:
            st.markdown("- Nenhum benefício anterior informado")
        st.divider()
        # Renderizar as caixas de upload lado a lado, reduzidas, usando st.columns([1, 1])
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("📸 **Foto 3x4**")
            st.file_uploader(
                "Foto 3x4 do periciando",
                type=["jpg", "jpeg", "png"],
                key="foto_3x4",
                label_visibility="collapsed"
            )
        with col2:
            st.markdown("📑 **Docs médicos**")
            st.file_uploader(
                "Documentos médicos apresentados",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="docs_medicos",
                label_visibility="collapsed"
            )
    with col_dir:
        # Campos principais do laudo (mantendo campos editáveis)
        profissao = processo.get("profissao", "")
        cid = processo.get("cid", "")
        anamnese = processo.get("anamnese", "")
        exame_fisico = processo.get("exame_fisico", "")
        documentos_texto = processo.get("documentos", "")
        incapacidade = processo.get("incapacidade", "Sim")
        data_inicio = processo.get("data_inicio", None)
        data_fim = processo.get("data_fim", None)
        quesitos = processo.get("quesitos", "")
        conclusao = processo.get("conclusao", "")

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Profissão", profissao or "", key="profissao")
        with col2:
            st.text_input("Histórico laboral", cid or "", key="cid")

        # ====== CAMPO ESCOLARIDADE ADICIONADO AQUI ======
        escolaridade = col2.selectbox(
            "Escolaridade",
            [
                "Analfabeto",
                "Apenas assina o nome",
                "Ensino fundamental incompleto",
                "Ensino fundamental completo",
                "Ensino médio incompleto",
                "Ensino médio completo",
                "Ensino superior incompleto",
                "Ensino superior completo"
            ],
            index=None,
            placeholder="Selecione a escolaridade"
        )
        # ====== FIM DO CAMPO ESCOLARIDADE ======

        st.markdown("### 🩺 Anamnese")
        st.text_area(
            "Descreva os dados clínicos e históricos relevantes",
            anamnese or "", height=120, key="anamnese"
        )

        # ============================ INÍCIO SEÇÃO EXAME FÍSICO REORGANIZADA ============================
        st.markdown("### 🧪 Exame Físico")
        # 1. Campo de texto "Resultado do exame físico realizado"
        st.text_area(
            "Resultado do exame físico realizado",
            key="resultado_exame_fisico",
            height=150
        )
        # 2. Selectbox de modelos logo abaixo (sem o subtítulo "Escolha um modelo")
        modelos_exame_clinico = {
            "Dor lombar (Lombalgia)": "Paciente apresenta dor à palpação em região lombossacral, com rigidez matinal e leve limitação à flexão lombar. Teste de Lasègue negativo. Marcha preservada.",
            "Transtorno depressivo (Depressão)": "Paciente relata humor deprimido, anedonia, distúrbios de sono e apetite. Apresenta-se orientado, mas com lentificação psicomotora e olhar cabisbaixo. Não há sinais psicóticos.",
            "Artrose de joelho": "Paciente deambula com claudicação leve. Dor à palpação em interlinha articular medial de joelho direito, com crepitação e limitação na extensão. Sem sinais flogísticos."
        }
        opcoes_modelos = [*modelos_exame_clinico.keys(), "+Novo modelo"]
        indice_modelo = 0  # Padrão: primeiro modelo
        # Se já selecionado, manter seleção
        if "modelo_exame_fisico" in st.session_state and st.session_state.modelo_exame_fisico in opcoes_modelos:
            indice_modelo = opcoes_modelos.index(st.session_state.modelo_exame_fisico)
        modelo_selecionado = st.selectbox(
            "Escolha um modelo",
            opcoes_modelos,
            index=indice_modelo,
            key="modelo_exame_fisico",
            label_visibility="visible"
        )
        # Nova lógica para atualizar resultado_exame_fisico conforme instrução
        if modelo_selecionado and modelo_selecionado != "+Novo modelo":
            st.session_state.resultado_exame_fisico = modelos_exame_clinico[modelo_selecionado]
        elif modelo_selecionado == "+Novo modelo":
            st.session_state.resultado_exame_fisico = ""
        # ============================ FIM SEÇÃO EXAME FÍSICO REORGANIZADA ============================

        # === NOVA SEÇÃO DE PATOLOGIA - BLOCO ATUALIZADO ===
        # Inicializa a lista de patologias, se ainda não existir
        if "patologias_identificadas" not in st.session_state:
            st.session_state.patologias_identificadas = []

        # Carrega base de patologias pré-cadastradas
        with open("data/patologias.json", "r", encoding="utf-8") as f:
            base_patologias = json.load(f)

        # Exibir lista de patologias já inseridas
        st.markdown("### 🧬 Patologia")
        for idx, pat in enumerate(st.session_state.patologias_identificadas):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.write(f"- {pat}")
            with col2:
                if st.button("❌", key=f"del_pat_{idx}"):
                    st.session_state.patologias_identificadas.pop(idx)
                    st.experimental_rerun()

        # Opção de adicionar nova
        patologias_disponiveis = [f"{p['nome']} (CID {p['cid']})" for p in base_patologias]
        patologias_disponiveis.append("+ Incluir nova patologia")
        nova_patologia_selecionada = st.selectbox("Adicionar nova patologia", patologias_disponiveis)

        if nova_patologia_selecionada == "+ Incluir nova patologia":
            with st.form("form_nova_patologia"):
                nome = st.text_input("Nome da patologia")
                cid = st.text_input("CID")
                definicao = st.text_area("Definição técnica (não será exibida na interface)")
                submitted = st.form_submit_button("Salvar")
                if submitted:
                    nova = {
                        "nome": nome,
                        "cid": cid,
                        "definicao": definicao
                    }
                    base_patologias.append(nova)
                    with open("data/patologias.json", "w", encoding="utf-8") as f:
                        json.dump(base_patologias, f, ensure_ascii=False, indent=2)
                    st.session_state.patologias_identificadas.append(f"{nome} (CID {cid})")
                    st.success("Patologia adicionada com sucesso.")
                    st.experimental_rerun()
        else:
            if st.button("Adicionar Patologia"):
                if nova_patologia_selecionada not in st.session_state.patologias_identificadas:
                    st.session_state.patologias_identificadas.append(nova_patologia_selecionada)
                    st.experimental_rerun()
        # === FIM DA SEÇÃO DE PATOLOGIA ===

        st.markdown("### 📆 Incapacidade")
        incapacidade_opcoes = ["Sim", "Não", "Parcial", "Permanente"]
        st.selectbox("Houve incapacidade laboral?", incapacidade_opcoes, key="incapacidade", index=incapacidade_opcoes.index(incapacidade) if incapacidade in incapacidade_opcoes else 0)
        # Ajustar datas
        def parse_date_field(field):
            if isinstance(field, date):
                return field
            elif isinstance(field, str) and field:
                try:
                    return datetime.strptime(field, "%Y-%m-%d").date()
                except Exception:
                    try:
                        return datetime.strptime(field, "%d-%m-%Y").date()
                    except Exception:
                        return None
            return None
        data_inicio_dt = parse_date_field(data_inicio)
        data_fim_dt = parse_date_field(data_fim)
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("Data de início da incapacidade (se houver)", data_inicio_dt, key="data_inicio")
        with col2:
            st.date_input("Data provável de término (se houver)", data_fim_dt, key="data_fim")

        st.markdown("### ✉️ Resposta aos Quesitos")
        st.text_area(
            "Transcreva ou cole aqui as respostas aos quesitos",
            quesitos or "", height=80, key="quesitos"
        )

        st.markdown("### 📝 Conclusão")
        st.text_area(
            "Conclusão do perito com base nos dados acima",
            conclusao or "", height=80, key="conclusao"
        )

        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            st.button("🔙 Voltar")
        with col2:
            st.button("💾 Salvar e continuar depois")
        with col3:
            st.button("🧾 Finalizar e Gerar Laudo")


if __name__ == "__main__":
    main()


# ======= CONTEÚDO DO ARQUIVO laudos_ad.py INCORPORADO ABAIXO =======

import os
from datetime import datetime
from PyPDF2 import PdfReader
import streamlit as st

def gerar_laudo_ad(processo):
    """
    Função exemplo para geração de laudo AD.
    Adapte a lógica conforme necessário.
    """
    st.write("Gerando laudo AD para o processo:", processo.get("numero_processo", "N/A"))
    # Aqui você pode adicionar o processamento real, gerar PDF, etc.
    processo["anexo_status"] = "Pronto"
    return True

# ======= FIM DO ARQUIVO laudos_ad.py =======

# ======= FIM DO ARQUIVO laudos_ad.py =======






def gerenciar_configuracoes():
    import streamlit as st

    st.title("⚙️ Configurações")
    aba = st.radio("Escolha uma aba:", ["Modelos de Exame Clínico", "Modelos de Patologias"], horizontal=True)

    if "modelos_exame" not in st.session_state:
        st.session_state.modelos_exame = []
    if "modelos_patologias" not in st.session_state:
        st.session_state.modelos_patologias = []

    if aba == "Modelos de Exame Clínico":
        st.subheader("Modelos de Exame Clínico")
        novo_modelo = st.text_area("Novo modelo de exame clínico:")
        if st.button("Adicionar Modelo"):
            if novo_modelo.strip():
                st.session_state.modelos_exame.append(novo_modelo.strip())
                st.success("Modelo adicionado com sucesso!")

        for i, modelo in enumerate(st.session_state.modelos_exame):
            st.text_area(f"Modelo {i + 1}", value=modelo, key=f"exame_{i}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar", key=f"salvar_exame_{i}"):
                    st.session_state.modelos_exame[i] = st.session_state[f"exame_{i}"]
                    st.success("Modelo atualizado.")
            with col2:
                if st.button("Excluir", key=f"excluir_exame_{i}"):
                    st.session_state.modelos_exame.pop(i)
                    st.success("Modelo excluído.")
                    st.experimental_rerun()

    elif aba == "Modelos de Patologias":
        st.subheader("Modelos de Patologias")
        nova_patologia = st.text_input("Nova patologia comum:")
        if st.button("Adicionar Patologia"):
            if nova_patologia.strip():
                st.session_state.modelos_patologias.append(nova_patologia.strip())
                st.success("Patologia adicionada com sucesso!")

        for i, patologia in enumerate(st.session_state.modelos_patologias):
            st.text_input(f"Patologia {i + 1}", value=patologia, key=f"patologia_{i}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar", key=f"salvar_patologia_{i}"):
                    st.session_state.modelos_patologias[i] = st.session_state[f"patologia_{i}"]
                    st.success("Patologia atualizada.")
            with col2:
                if st.button("Excluir", key=f"excluir_patologia_{i}"):
                    st.session_state.modelos_patologias.pop(i)
                    st.success("Patologia excluída.")
                    st.experimental_rerun()