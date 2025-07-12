import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "pages"))

import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import calendar
from datetime import datetime, date
import json
import locale

# Ajuste dos imports dos módulos das páginas
import laudos_ad

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
                        st.rerun()
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
                if processo.get("pdf") is None:
                    st.write("📎 Anexar")
                elif processo.get("pre_laudo") is None:
                    st.write("⏳ Aguardando")
                else:
                    st.write("✅ Pronto")
            row_cols[1].write(processo['horario'])
            row_cols[2].write(processo['numero_processo'])
            row_cols[3].write(processo['nome_parte'])
            row_cols[4].write(processo['tipo'].split('(')[-1].replace(')', ''))
            row_cols[5].write(processo['situacao'])
            # Novo bloco unificado de botões de ação
            with row_cols[6]:
                col_a, col_b, col_c = st.columns([1, 1, 1])

                # Removido botão de redigir laudo (📝) e checagem de tipo de processo
                with col_a:
                    st.write("")  # Ocupa o espaço para manter alinhamento

                with col_b:
                    if st.button("🚫", key=f"ausente_{key_processos}_{idx}"):
                        st.session_state.confirm_action = ("ausencia", key_processos, processo)
                        st.rerun()

                with col_c:
                    if st.button("🗑️", key=f"excluir_{key_processos}_{idx}"):
                        st.session_state.confirm_action = ("excluir", key_processos, processo)
                        st.rerun()

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
                                st.rerun()
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
            # st.info("⏳ Iniciando leitura dos processos...")  # Remove info/notification
            # (mantido apenas ação de lote, sem botões extras de redigir laudo)
            for idx, processo in enumerate(processos_ordenados):
                chave_pdf = f"pdf_{key_processos}_{idx}"
                chave_texto = f"text_{key_processos}_{idx}"
                if chave_pdf in st.session_state:
                    arquivo_pdf = st.session_state[chave_pdf]
                    texto_extraido = extrair_texto_pdf(arquivo_pdf)
                    st.session_state[chave_texto] = texto_extraido
                    # Após geração do pré-laudo, marcar laudo_gerado=True
                    st.session_state.processos[key_processos][idx]["laudo_gerado"] = True
            # Nenhum botão "Redigir Laudo" criado aqui

    else:
        st.info("📭 Nenhum processo cadastrado para esta data/local ainda.")
def main():
    """Função principal do aplicativo"""
    
    # Inicializar dados da sessão
    init_session_data()

    # Tela de login
    if st.session_state.get("pagina") == "redigir_laudo":
        if st.session_state.get("modo_redacao") == "AD":
            laudos_ad.redigir_laudo_ad()
        elif st.session_state.get("modo_redacao") == "BPC":
            from pages.laudos_bpc import redigir_laudo_bpc
            redigir_laudo_bpc(st.session_state.get("processo_atual"))
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
        
        # Verificar qual tela mostrar
        if st.session_state.selected_date_local:
            if isinstance(st.session_state.selected_date_local, dict):
                data_iso = st.session_state.selected_date_local["data"]
                local_name = st.session_state.selected_date_local["local"]
                show_processos_view(data_iso, local_name)
        
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
                
                # Se o usuário clicou em um dia com múltiplos locais, exibe selectbox para escolher o local
                if st.session_state.selected_date_multilocais and has_permission(user_info, 'agendar_pericias'):
                    date_info = st.session_state.selected_date_multilocais
                    date_str = date_info["date"]
                    locais = date_info["locais"]
                    date_formatted = format_date_br(date_str)
                    st.markdown("---")
                    st.markdown(f"### 📍 Escolha o local para {date_formatted}")
                    local_escolhido = st.selectbox("Selecione o local", locais, key="selectbox_multilocais")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirmar Local"):
                            st.session_state.selected_date_local = {"data": date_str, "local": local_escolhido}
                            st.session_state.selected_date_multilocais = None
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancelar"):
                            st.session_state.selected_date_multilocais = None
                            st.rerun()

                # Formulário para adicionar perícia na data selecionada
                elif st.session_state.selected_date and has_permission(user_info, 'agendar_pericias'):
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
                                    # Gerenciar vínculo de múltiplos locais
                                    data = st.session_state.selected_date
                                    info_pericia = {
                                        "local": local_pericia,
                                        "observacoes": observacoes,
                                        "criado_por": st.session_state.username,
                                        "criado_em": datetime.now().isoformat()
                                    }

                                    chave = f"{data}_{local_pericia}"
                                    st.session_state.pericias[chave] = info_pericia

                                    # Atualizar pericias_por_dia para permitir múltiplos locais por data
                                    if data not in st.session_state.pericias_por_dia:
                                        st.session_state.pericias_por_dia[data] = [local_pericia]
                                    else:
                                        if local_pericia not in st.session_state.pericias_por_dia[data]:
                                            st.session_state.pericias_por_dia[data].append(local_pericia)

                                    st.success("✅ Perícia agendada com sucesso!")
                                    st.session_state.selected_date = None
                                    st.rerun()
                                else:
                                    st.error(f"❌ Já existe uma perícia agendada para {local_pericia} nesta data!")

                        with col2:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state.selected_date = None
                                st.rerun()

                # Tela da data: mostrar locais vinculados e permitir vincular outro local
                # (Nova lógica para múltiplos locais na data)
                # Exemplo: st.session_state['pericias'][data] pode ser lista ou string
                if st.session_state.selected_date and st.session_state.selected_date in st.session_state.pericias:
                    pericias_na_data = st.session_state.pericias[st.session_state.selected_date]
                    # Mostra selectbox se for lista
                    if isinstance(pericias_na_data, list):
                        local_escolhido = st.selectbox(
                            "Selecione o local de atuação nesta data:",
                            pericias_na_data,
                            key="local_escolhido_dia"
                        )
                    else:
                        local_escolhido = pericias_na_data
                    # Aqui, utilize local_escolhido para carregar processos desse local, etc.
                    # Exemplo: st.write(f"Processos para o local: {local_escolhido}")

                    # Localize a lógica do botão "Vincular outro local nesta data"
                    if st.button("🔗 Vincular outro local nesta data"):
                        locais_disponiveis = [l for l in st.session_state['locais'] if l not in st.session_state['pericias'][st.session_state.selected_date]]
                        if locais_disponiveis:
                            novo_local = st.selectbox("Selecione o novo local para vincular:", locais_disponiveis, key="novo_local_vinculo")
                            if st.button("Salvar local vinculado"):
                                if isinstance(st.session_state['pericias'][st.session_state.selected_date], list):
                                    if novo_local not in st.session_state['pericias'][st.session_state.selected_date]:
                                        st.session_state['pericias'][st.session_state.selected_date].append(novo_local)
                                else:
                                    st.session_state['pericias'][st.session_state.selected_date] = [st.session_state['pericias'][st.session_state.selected_date], novo_local]
                                st.experimental_rerun()
                        else:
                            st.info("Todos os locais já estão vinculados a esta data.")

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

if __name__ == "__main__":
    main()

# Calendário inicial: destaque datas com múltiplos locais
# Exemplo de código para destacar datas com múltiplos locais
# (Coloque este trecho no local apropriado para exibir a lista de datas)
# for data, locais in st.session_state['pericias'].items():
#     if isinstance(locais, list) and len(locais) > 1:
#         st.markdown(f"📌 **{data.strftime('%d-%m-%Y')}** — {len(locais)} locais")
#     else:
#         st.markdown(f"📅 {data.strftime('%d-%m-%Y')} — {locais if isinstance(locais, str) else locais[0]}")