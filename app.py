import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import json
import locale

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
    "17ª Vara Federal (Juazeiro do Norte)",
    "20ª Vara Federal (Salgueiro)",
    "25ª Vara Federal (Iguatu)",
    "27ª Vara Federal (Ouricuri)",
    "15ª Vara Federal (Sousa)"
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
    "gerenciar_locais_estaduais": False
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
            # Se já está no formato DD-MM-YYYY
            if len(parts[0]) == 2:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
            # Se está no formato YYYY-MM-DD
            else:
                return date_str
    return date_str

# Função para inicializar dados na sessão
def init_session_data():
    """Inicializa dados na sessão do Streamlit"""
    if 'users' not in st.session_state:
        st.session_state.users = {
            "admin": {
                "password": "admin123",
                "role": "administrador",
                "name": "Dr. Hyttallo",
                "permissoes": {}  # Admin tem todas as permissões
            }
        }
    
    if 'pericias' not in st.session_state:
        st.session_state.pericias = {}
    
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
    """Retorna todos os locais (federais + estaduais)"""
    return LOCAIS_FEDERAIS + st.session_state.locais_estaduais

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
                has_pericia = date_str in st.session_state.pericias
                
                if has_pericia:
                    local = st.session_state.pericias[date_str]["local"]
                    local_short = local.split('(')[0].strip() if '(' in local else local[:15]
                    cols[i].button(
                        f"**{day}**\n📍 {local_short}",
                        key=f"day_{date_str}",
                        help=f"Perícia em: {local}",
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
    for data, info in st.session_state.pericias.items():
        if info['local'] == local_name:
            pericias_local.append({
                'Data': format_date_br(data),
                'Local': info['local'],
                'Observações': info.get('observacoes', ''),
                'Criado por': info.get('criado_por', 'N/A'),
                'Data_Sort': data
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
        
        # Mostrar perícias futuras
        if futuras:
            st.markdown("### 📅 Perícias Agendadas")
            df_futuras = pd.DataFrame(futuras)
            df_futuras = df_futuras.sort_values('Data_Sort')
            df_futuras = df_futuras.drop('Data_Sort', axis=1)
            st.dataframe(df_futuras, use_container_width=True)
        
        # Mostrar perícias passadas
        if passadas:
            st.markdown("### 📋 Histórico de Perícias")
            df_passadas = pd.DataFrame(passadas)
            df_passadas = df_passadas.sort_values('Data_Sort', ascending=False)
            df_passadas = df_passadas.drop('Data_Sort', axis=1)
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
        futuras_count = len([p for p in pericias_local if datetime.strptime(p['Data_Sort'], '%Y-%m-%d').date() >= hoje])
        st.metric("Perícias Futuras", futuras_count)
    
    with col3:
        passadas_count = len([p for p in pericias_local if datetime.strptime(p['Data_Sort'], '%Y-%m-%d').date() < hoje])
        st.metric("Perícias Realizadas", passadas_count)

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
            
            # Botão para voltar ao calendário principal
            if st.session_state.current_local_filter:
                if st.button("🏠 Voltar ao Calendário Principal"):
                    st.session_state.current_local_filter = None
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
                    st.rerun()
            
            # Listar locais estaduais
            if st.session_state.locais_estaduais:
                for local in st.session_state.locais_estaduais:
                    if st.button(f"📍 {local}", key=f"sidebar_estadual_{local}", use_container_width=True):
                        st.session_state.current_local_filter = local
                        st.session_state.show_user_management = False
                        st.session_state.show_change_password = False
                        st.session_state.show_estaduais_management = False
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
        
        # Gerenciamento de locais estaduais
        if st.session_state.show_estaduais_management and user_info['role'] == 'administrador':
            st.markdown("### 🏛️ Gerenciar Locais Estaduais")
            
            # Adicionar novo local estadual
            with st.form("add_local_estadual"):
                st.markdown("#### ➕ Adicionar Novo Local Estadual")
                novo_local = st.text_input("Nome do Local")
                
                if st.form_submit_button("Adicionar Local"):
                    if novo_local and novo_local not in st.session_state.locais_estaduais:
                        st.session_state.locais_estaduais.append(novo_local)
                        st.success(f"✅ Local '{novo_local}' adicionado com sucesso!")
                        st.rerun()
                    elif novo_local in st.session_state.locais_estaduais:
                        st.error("❌ Este local já existe!")
                    else:
                        st.error("❌ Por favor, insira um nome para o local!")
            
            # Listar e gerenciar locais existentes
            if st.session_state.locais_estaduais:
                st.markdown("#### 📋 Locais Estaduais Cadastrados")
                for i, local in enumerate(st.session_state.locais_estaduais):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"📍 {local}")
                    with col2:
                        if st.button("🗑️", key=f"del_estadual_{i}"):
                            st.session_state.locais_estaduais.remove(local)
                            st.success(f"Local '{local}' removido!")
                            st.rerun()
            else:
                st.info("📭 Nenhum local estadual cadastrado ainda.")
            
            st.markdown("---")
        
        # Formulário para mudar senha (aparece apenas quando ativado)
        if st.session_state.show_change_password:
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
        
        # Gerenciamento de usuários (aparece apenas quando ativado pelo admin)
        if user_info['role'] == 'administrador' and st.session_state.show_user_management:
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
                                        "gerenciar_locais_estaduais": perm_gerenciar_locais_estaduais
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
        
        # Interface principal
        if st.session_state.current_local_filter:
            # Visualização específica do local
            show_local_specific_view(st.session_state.current_local_filter)
        
        elif not st.session_state.show_user_management and not st.session_state.show_estaduais_management:
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
                
                # Formulário simplificado para adicionar perícia na data selecionada
                if st.session_state.selected_date and has_permission(user_info, 'agendar_pericias'):
                    st.markdown("---")
                    date_formatted = format_date_br(st.session_state.selected_date)
                    st.markdown(f"### 📝 Agendar Perícia - {date_formatted}")
                    
                    with st.form("add_pericia"):
                        # Apenas local e observações, sem horário
                        local_pericia = st.selectbox("Local da Perícia", get_all_locais())
                        observacoes = st.text_area("Observações (opcional)")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ Confirmar Perícia", type="primary"):
                                st.session_state.pericias[st.session_state.selected_date] = {
                                    "local": local_pericia,
                                    "observacoes": observacoes,
                                    "criado_por": st.session_state.username,
                                    "criado_em": datetime.now().isoformat()
                                }
                                st.success("✅ Perícia agendada com sucesso!")
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
                    if st.session_state.locais_estaduais:
                        st.markdown("#### 🏛️ Estaduais")
                        cols = st.columns(3)
                        for i, local in enumerate(st.session_state.locais_estaduais):
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
                    for data, info in st.session_state.pericias.items():
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
                        for data in st.session_state.pericias.keys():
                            data_br = format_date_br(data)
                            local = st.session_state.pericias[data]['local']
                            opcoes_remover.append(f"{data_br} - {local}")
                        
                        data_remover_display = st.selectbox(
                            "Selecione a perícia para remover",
                            opcoes_remover
                        )
                        
                        if data_remover_display and st.button("🗑️ Confirmar Remoção", type="secondary"):
                            # Extrair a data original da opção selecionada
                            data_br = data_remover_display.split(' - ')[0]
                            data_iso = format_date_iso(data_br)
                            
                            if data_iso in st.session_state.pericias:
                                del st.session_state.pericias[data_iso]
                                st.success("✅ Perícia removida com sucesso!")
                                st.rerun()
                else:
                    st.info("📭 Nenhuma perícia agendada ainda.")

if __name__ == "__main__":
    main()
