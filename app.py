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

# Locais de atuação
LOCAIS_ATUACAO = [
    "17ª Vara Federal (Juazeiro do Norte)",
    "20ª Vara Federal (Salgueiro)",
    "25ª Vara Federal (Iguatu)",
    "27ª Vara Federal (Ouricuri)",
    "15ª Vara Federal (Sousa)",
    "Estaduais (Diversas varas)"
]

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
                "name": "Dr. Hyttallo"
            }
        }
    
    if 'pericias' not in st.session_state:
        st.session_state.pericias = {}
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None

def authenticate_user(username, password):
    """Autentica usuário"""
    if username in st.session_state.users:
        if st.session_state.users[username]["password"] == password:
            return st.session_state.users[username]
    return None

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
        
        # Removido: Informações do sistema com credenciais expostas
        
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
                st.rerun()
        
        st.markdown("---")
        
        # Sidebar para administração e configurações
        with st.sidebar:
            st.markdown("### ⚙️ Configurações")
            
            # Opção para mudar senha (disponível para todos)
            if st.button("🔑 Mudar Senha"):
                st.session_state.show_change_password = True
            
            if user_info['role'] == 'administrador':
                st.markdown("### 🛠️ Administração")
                
                if st.button("👥 Gerenciar Usuários"):
                    st.session_state.show_user_management = True
                
                if st.button("📊 Relatórios"):
                    st.session_state.show_reports = True
        
        # Formulário para mudar senha
        if st.session_state.get('show_change_password', False):
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
        
        # Gerenciamento de usuários (apenas admin)
        if user_info['role'] == 'administrador' and st.session_state.get('show_user_management', False):
            st.markdown("### 👥 Gerenciamento de Usuários")
            
            with st.expander("➕ Criar Novo Usuário"):
                with st.form("create_user"):
                    new_username = st.text_input("Nome de usuário")
                    new_password = st.text_input("Senha", type="password")
                    new_name = st.text_input("Nome completo")
                    new_role = st.selectbox("Perfil", ["assistente", "administrador"])
                    
                    if st.form_submit_button("Criar Usuário"):
                        if new_username not in st.session_state.users:
                            if len(new_password) >= 6:
                                st.session_state.users[new_username] = {
                                    "password": new_password,
                                    "role": new_role,
                                    "name": new_name
                                }
                                st.success(f"✅ Usuário {new_username} criado com sucesso!")
                            else:
                                st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                        else:
                            st.error("❌ Usuário já existe!")
            
            # Lista de usuários existentes
            st.markdown("#### Usuários Cadastrados")
            for username, info in st.session_state.users.items():
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(f"**{info['name']}** ({username})")
                col2.write(f"*{info['role'].title()}*")
                if username != st.session_state.username:
                    if col3.button("🗑️", key=f"del_{username}"):
                        del st.session_state.users[username]
                        st.rerun()
        
        # Interface principal
        tab1, tab2 = st.tabs(["📅 Calendário e Perícias", "📋 Gerenciar Perícias"])
        
        with tab1:
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
            if st.session_state.selected_date:
                st.markdown("---")
                date_formatted = format_date_br(st.session_state.selected_date)
                st.markdown(f"### 📝 Agendar Perícia - {date_formatted}")
                
                with st.form("add_pericia"):
                    col1, col2 = st.columns(2)
                    with col1:
                        local_pericia = st.selectbox("Local da Perícia", LOCAIS_ATUACAO)
                    with col2:
                        hora_pericia = st.time_input("Horário", value=datetime.strptime("09:00", "%H:%M").time())
                    
                    observacoes = st.text_area("Observações (opcional)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("✅ Confirmar Perícia", type="primary"):
                            st.session_state.pericias[st.session_state.selected_date] = {
                                "local": local_pericia,
                                "hora": hora_pericia.strftime("%H:%M"),
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
            
            # Locais de atuação
            st.markdown("---")
            st.markdown("### 🏛️ Locais de Atuação")
            
            cols = st.columns(3)
            for i, local in enumerate(LOCAIS_ATUACAO):
                with cols[i % 3]:
                    if st.button(f"📍 {local}", key=f"local_{i}", use_container_width=True):
                        st.session_state.filtro_local = local
            
            # Lista de perícias por local (se filtro ativo)
            if st.session_state.get('filtro_local'):
                st.markdown(f"### 📋 Perícias - {st.session_state.filtro_local}")
                
                pericias_filtradas = []
                for data, info in st.session_state.pericias.items():
                    if info['local'] == st.session_state.filtro_local:
                        pericias_filtradas.append({
                            'Data': format_date_br(data),
                            'Horário': info['hora'],
                            'Local': info['local'],
                            'Observações': info.get('observacoes', '')
                        })
                
                if pericias_filtradas:
                    df = pd.DataFrame(pericias_filtradas)
                    # Ordenar por data (convertendo de volta para ISO para ordenação)
                    df['Data_Sort'] = df['Data'].apply(format_date_iso)
                    df = df.sort_values('Data_Sort').drop('Data_Sort', axis=1)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhuma perícia agendada para este local.")
                
                if st.button("🔄 Limpar Filtro"):
                    if 'filtro_local' in st.session_state:
                        del st.session_state.filtro_local
                    st.rerun()
        
        with tab2:
            st.markdown("### 📋 Gerenciar Todas as Perícias")
            
            if st.session_state.pericias:
                # Converter para DataFrame
                pericias_list = []
                for data, info in st.session_state.pericias.items():
                    pericias_list.append({
                        'Data': format_date_br(data),
                        'Horário': info['hora'],
                        'Local': info['local'],
                        'Observações': info.get('observacoes', ''),
                        'Criado por': info.get('criado_por', 'N/A')
                    })
                
                df = pd.DataFrame(pericias_list)
                # Ordenar por data
                df['Data_Sort'] = df['Data'].apply(format_date_iso)
                df = df.sort_values('Data_Sort', ascending=False).drop('Data_Sort', axis=1)
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    filtro_local_geral = st.selectbox(
                        "Filtrar por local",
                        ["Todos"] + LOCAIS_ATUACAO,
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
                
                # Opção para deletar perícias (apenas admin)
                if user_info['role'] == 'administrador':
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
