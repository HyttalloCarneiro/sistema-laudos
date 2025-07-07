import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import json
import locale
from reportlab.pdfgen import canvas
from io import BytesIO
import base64

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
                pericias_do_dia = []
                for chave, info in st.session_state.pericias.items():
                    if '_' in chave:
                        data_chave = chave.split('_')[0]
                    else:
                        data_chave = chave

                    if data_chave == date_str:
                        pericias_do_dia.append(info['local'])

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
    hoje = datetime.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year
    mes_seguinte = (mes_atual % 12) + 1
    ano_seguinte = ano_atual + 1 if mes_seguinte == 1 else ano_atual

    dias_mes_atual = set()
    dias_mes_seguinte = set()

    for p in pericias_local:
        data_obj = datetime.strptime(p['Data_Sort'], "%Y-%m-%d").date()
        if data_obj.month == mes_atual and data_obj.year == ano_atual:
            dias_mes_atual.add(data_obj)
        elif data_obj.month == mes_seguinte and data_obj.year == ano_seguinte:
            dias_mes_seguinte.add(data_obj)

    st.metric("Dias com Perícias - Mês Atual", len(dias_mes_atual))
    st.metric("Dias com Perícias - Mês Seguinte", len(dias_mes_seguinte))

def show_processos_view(data_iso, local_name):
    """Mostra a tela de gerenciamento de processos para uma data/local específico"""
    data_br = format_date_br(data_iso)
    st.markdown(f"## 📋 Processos - {data_br}")
    st.markdown(f"**Local:** {local_name}")

    # Botão para voltar
    if st.button("← Voltar para " + local_name):
        st.session_state.selected_date_local = None
        st.rerun()

    # Botão para adicionar outro local nesta data
    st.markdown("---")
    if st.button("➕ Adicionar outro local nesta data"):
        st.session_state["adicionar_local"] = True

    # Lista de locais disponíveis para adicionar (excluindo os já usados na data)
    def get_locais_disponiveis_para_data(data_iso):
        locais_usados = []
        for chave, info in st.session_state.pericias.items():
            if '_' in chave:
                data_chave = chave.split('_')[0]
                if data_chave == data_iso:
                    locais_usados.append(info['local'])
        return [l for l in get_all_locais() if l not in locais_usados]

    def adicionar_novo_local_para_data(data_iso, novo_local):
        chave = f"{data_iso}_{novo_local}"
        if chave not in st.session_state.pericias:
            st.session_state.pericias[chave] = {
                "local": novo_local,
                "observacoes": "",
                "criado_por": st.session_state.username,
                "criado_em": datetime.now().isoformat()
            }
        # Inicializa lista de processos para o novo local
        if chave not in st.session_state.processos:
            st.session_state.processos[chave] = []

    if st.session_state.get("adicionar_local"):
        lista_de_locais_disponiveis = get_locais_disponiveis_para_data(data_iso)
        if not lista_de_locais_disponiveis:
            st.info("Todos os locais já estão cadastrados nesta data.")
        else:
            novo_local = st.selectbox("Selecione o novo local", lista_de_locais_disponiveis)
            if st.button("Confirmar local"):
                adicionar_novo_local_para_data(data_iso, novo_local)
                st.success("Novo local adicionado!")
                st.session_state["adicionar_local"] = False
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
                    value=datetime.strptime("09:00", "%H:%M").time(),
                    step=900
                )
            with col2:
                tipo_pericia = st.selectbox("Tipo", TIPOS_PERICIA)
                situacao = st.selectbox("Situação", SITUACOES_PROCESSO)

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
                            "criado_em": datetime.now().isoformat()
                        }
                        st.session_state.processos[key_processos].append(novo_processo)
                        st.success("✅ Processo adicionado com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Número do processo e nome da parte são obrigatórios!")

    # Listar processos existentes
    processos_lista = st.session_state.processos.get(key_processos, [])

    # Funções auxiliares para ações confirmadas
    def excluir_processo(processo_id):
        st.session_state.processos[key_processos].pop(processo_id)
        st.success("🗑️ Processo excluído com sucesso.")
        st.session_state["processo_acao_flag"] = None
        st.session_state["processo_acao_tipo"] = None
        st.rerun()

    def marcar_como_ausente(processo_id):
        processo = processos_ordenados[processo_id]
        st.session_state.processos[key_processos][processo_id]['situacao'] = 'Ausente'
        # Gerar PDF de certidão de ausência usando reportlab
        buffer = BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "CERTIDÃO DE AUSÊNCIA")
        c.setFont("Helvetica", 12)
        c.drawString(100, 720, f"Certifico que a parte {processo['nome_parte']} esteve ausente à perícia médica em {format_date_br(data_iso)}.")
        c.drawString(100, 700, f"Número do Processo: {processo['numero_processo']}")
        c.drawString(100, 680, f"Horário: {processo['horario']}")
        c.drawString(100, 660, f"Local: {local_name}")
        c.save()
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="certidao_ausencia_{processo["numero_processo"]}.pdf">📄 Baixar Certidão</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.session_state["processo_acao_flag"] = None
        st.session_state["processo_acao_tipo"] = None
        st.rerun()

    def realizar_acao_confirmada(processo_id):
        acao = st.session_state.get("processo_acao_tipo")
        if acao == "excluir":
            excluir_processo(processo_id)
        elif acao == "ausente":
            marcar_como_ausente(processo_id)

    if processos_lista:
        st.markdown("### 📋 Processos Cadastrados")
        # Ordenar por horário
        processos_ordenados = sorted(processos_lista, key=lambda x: x['horario'])
        # Novo cabeçalho de colunas
        colunas = ["Anexar Processo", "Horário", "Número do Processo", "Nome da parte", "Situação", "Ação"]
        header_cols = st.columns([2, 2, 3, 3, 2, 2])
        for i, nome_col in enumerate(colunas):
            header_cols[i].markdown(f"**{nome_col}**")
        for idx, processo in enumerate(processos_ordenados):
            processo_id = idx
            # Exibir confirmação de ação se necessário
            if st.session_state.get("processo_acao_flag") == processo_id:
                with st.container():
                    st.warning("Tem certeza desta ação?")
                    col_sim, col_nao = st.columns(2)
                    if col_sim.button("Sim", key=f"sim_{processo_id}"):
                        realizar_acao_confirmada(processo_id)
                        return
                    if col_nao.button("Não", key=f"nao_{processo_id}"):
                        st.session_state["processo_acao_flag"] = None
                        st.session_state["processo_acao_tipo"] = None
                        st.rerun()
                        return
                continue
            # Linha normal de processo
            row_cols = st.columns([2, 2, 3, 3, 2, 2])
            with row_cols[0]:
                st.button("📎 Em breve", key=f"anexar_{key_processos}_{idx}", disabled=True)
            row_cols[1].write(processo['horario'])
            row_cols[2].write(processo['numero_processo'])
            row_cols[3].write(processo['nome_parte'])
            row_cols[4].write(processo['situacao'])
            # Botões de ação lado a lado, largura igual, sem texto verticalizado
            with row_cols[5]:
                action_cols = st.columns([1, 1, 1])
                # Redigir Laudo (desabilitado, só ícone)
                with action_cols[0]:
                    st.button("", key=f"laudo_{key_processos}_{idx}", icon="✏️", disabled=True)
                # Ausente
                with action_cols[1]:
                    if processo['situacao'].lower() != 'ausente':
                        ausente_clicked = st.button("", key=f"ausente_{processo_id}", icon="🚫")
                        if ausente_clicked and not (st.session_state.get("processo_acao_flag") == processo_id and st.session_state.get("processo_acao_tipo") == "ausente"):
                            st.session_state["processo_acao_flag"] = processo_id
                            st.session_state["processo_acao_tipo"] = "ausente"
                            st.rerun()
                # Excluir
                with action_cols[2]:
                    excluir_clicked = st.button("", key=f"excluir_{processo_id}", icon="🗑️")
                    if excluir_clicked and not (st.session_state.get("processo_acao_flag") == processo_id and st.session_state.get("processo_acao_tipo") == "excluir"):
                        st.session_state["processo_acao_flag"] = processo_id
                        st.session_state["processo_acao_tipo"] = "excluir"
                        st.rerun()
        # Estatísticas dos processos (ajustado)
        st.markdown("### 📊 Estatísticas dos Processos")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_a_realizar = len([p for p in processos_lista if p['situacao'] != 'Concluído'])
            st.metric("Total de Perícias a Realizar", total_a_realizar)
        with col2:
            total_realizadas = len([p for p in processos_lista if p['situacao'] == 'Concluído'])
            st.metric("Total de Perícias Realizadas", total_realizadas)
        with col3:
            total_ausentes = len([p for p in processos_lista if p['situacao'].lower() == 'ausente'])
            st.metric("Total de Ausentes", total_ausentes)
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
                
                # Se o usuário clicou em um dia com múltiplos locais, exibe multiselect para escolher locais
                if st.session_state.selected_date_multilocais and has_permission(user_info, 'agendar_pericias'):
                    date_info = st.session_state.selected_date_multilocais
                    date_str = date_info["date"]
                    locais = date_info["locais"]
                    date_formatted = format_date_br(date_str)
                    st.markdown("---")
                    st.markdown(f"### 📍 Escolha o(s) local(is) para {date_formatted}")
                    locais_escolhidos = st.multiselect("Selecione os locais", locais, default=locais, key="multiselect_multilocais")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirmar Local(is)"):
                            if locais_escolhidos:
                                # Se selecionar mais de um, mostra apenas o primeiro (ou pode iterar, mas manter lógica atual)
                                # Aqui, abre o primeiro local selecionado
                                st.session_state.selected_date_local = {"data": date_str, "local": locais_escolhidos[0]}
                                st.session_state.selected_date_multilocais = None
                                st.rerun()
                            else:
                                st.warning("Selecione ao menos um local.")
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

                    st.markdown("#### ➕ Cadastrar nova perícia em outro local")
                    st.markdown("*Mesmo dia, local diferente:*")
                    
                    with st.form("add_pericia"):
                        # Apenas local e observações, sem horário
                        local_pericia = st.selectbox("Escolha outro local da perícia", get_all_locais())
                        observacoes = st.text_area("Observações (opcional)")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ Confirmar Perícia", type="primary"):
                                # Criar chave composta de data + local (permite múltiplas perícias no mesmo dia)
                                chave_base = st.session_state.selected_date
                                chave_completa = f"{chave_base}_{local_pericia}"
                                if chave_completa not in st.session_state.pericias:
                                    st.session_state.pericias[chave_completa] = {
                                        "local": local_pericia,
                                        "observacoes": observacoes,
                                        "criado_por": st.session_state.username,
                                        "criado_em": datetime.now().isoformat()
                                    }
                                    st.success("✅ Perícia agendada com sucesso!")
                                else:
                                    st.warning("⚠️ Já há perícia agendada neste local e data.")
                                st.session_state.selected_date = None
                                st.rerun()
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

if __name__ == "__main__":
    main()