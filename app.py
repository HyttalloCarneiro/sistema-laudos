import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import json
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Sistema de Laudos Periciais",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Diretório para armazenar dados
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Arquivos de dados
USERS_FILE = DATA_DIR / "users.json"
PERICIAS_FILE = DATA_DIR / "pericias.json"

# Locais de atuação
LOCAIS_ATUACAO = [
    "17ª Vara Federal (Juazeiro do Norte)",
    "20ª Vara Federal (Salgueiro)",
    "25ª Vara Federal (Iguatu)",
    "27ª Vara Federal (Ouricuri)",
    "15ª Vara Federal (Sousa)",
    "Estaduais (Diversas varas)"
]

# Funções de gerenciamento de dados
def load_users():
    """Carrega usuários do arquivo JSON"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Usuário administrador padrão
        default_users = {
            "admin": {
                "password": "admin123",
                "role": "administrador",
                "name": "Dr. Hyttallo"
            }
        }
        save_users(default_users)
        return default_users

def save_users(users):
    """Salva usuários no arquivo JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_pericias():
    """Carrega perícias do arquivo JSON"""
    if PERICIAS_FILE.exists():
        with open(PERICIAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_pericias(pericias):
    """Salva perícias no arquivo JSON"""
    with open(PERICIAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(pericias, f, ensure_ascii=False, indent=2)

def authenticate_user(username, password):
    """Autentica usuário"""
    users = load_users()
    if username in users and users[username]["password"] == password:
        return users[username]
    return None

def create_calendar_view(year, month):
    """Cria visualização do calendário"""
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    st.subheader(f"📅 {month_name} {year}")
    
    # Cabeçalho dos dias da semana
    days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    cols = st.columns(7)
    for i, day in enumerate(days):
        cols[i].markdown(f"**{day}**")
    
    # Perícias carregadas
    pericias = load_pericias()
    
    # Dias do mês
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                has_pericia = date_str in pericias
                
                if has_pericia:
                    local = pericias[date_str]["local"]
                    cols[i].button(
                        f"**{day}**\n📍 {local[:15]}...",
                        key=f"day_{date_str}",
                        help=f"Perícia em: {local}",
                        type="primary"
                    )
                else:
                    if cols[i].button(f"{day}", key=f"day_{date_str}"):
                        st.session_state.selected_date = date_str

def main():
    """Função principal do aplicativo"""
    
    # Inicialização do estado da sessão
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None

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
        
        # Informações do sistema
        st.markdown("---")
        st.info("💡 **Usuário padrão:** admin | **Senha:** admin123")
        
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
        
        # Sidebar para administração
        if user_info['role'] == 'administrador':
            with st.sidebar:
                st.markdown("### 🛠️ Administração")
                
                if st.button("👥 Gerenciar Usuários"):
                    st.session_state.show_user_management = True
                
                if st.button("📊 Relatórios"):
                    st.session_state.show_reports = True
        
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
                        users = load_users()
                        if new_username not in users:
                            users[new_username] = {
                                "password": new_password,
                                "role": new_role,
                                "name": new_name
                            }
                            save_users(users)
                            st.success(f"✅ Usuário {new_username} criado com sucesso!")
                        else:
                            st.error("❌ Usuário já existe!")
            
            # Lista de usuários existentes
            users = load_users()
            st.markdown("#### Usuários Cadastrados")
            for username, info in users.items():
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(f"**{info['name']}** ({username})")
                col2.write(f"*{info['role'].title()}*")
                if username != st.session_state.username:  # Não pode deletar a si mesmo
                    if col3.button("🗑️", key=f"del_{username}"):
                        del users[username]
                        save_users(users)
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
                    format_func=lambda x: calendar.month_name[x]
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
                st.markdown(f"### 📝 Agendar Perícia - {st.session_state.selected_date}")
                
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
                            pericias = load_pericias()
                            pericias[st.session_state.selected_date] = {
                                "local": local_pericia,
                                "hora": hora_pericia.strftime("%H:%M"),
                                "observacoes": observacoes,
                                "criado_por": st.session_state.username,
                                "criado_em": datetime.now().isoformat()
                            }
                            save_pericias(pericias)
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
                
                pericias = load_pericias()
                pericias_filtradas = []
                
                for data, info in pericias.items():
                    if info['local'] == st.session_state.filtro_local:
                        pericias_filtradas.append({
                            'Data': data,
                            'Horário': info['hora'],
                            'Local': info['local'],
                            'Observações': info.get('observacoes', '')
                        })
                
                if pericias_filtradas:
                    df = pd.DataFrame(pericias_filtradas)
                    df = df.sort_values('Data')
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhuma perícia agendada para este local.")
                
                if st.button("🔄 Limpar Filtro"):
                    if 'filtro_local' in st.session_state:
                        del st.session_state.filtro_local
                    st.rerun()
        
        with tab2:
            st.markdown("### 📋 Gerenciar Todas as Perícias")
            
            pericias = load_pericias()
            
            if pericias:
                # Converter para DataFrame
                pericias_list = []
                for data, info in pericias.items():
                    pericias_list.append({
                        'Data': data,
                        'Horário': info['hora'],
                        'Local': info['local'],
                        'Observações': info.get('observacoes', ''),
                        'Criado por': info.get('criado_por', 'N/A')
                    })
                
                df = pd.DataFrame(pericias_list)
                df = df.sort_values('Data', ascending=False)
                
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
                    df_filtrado = df_filtrado[df_filtrado['Data'] >= str(filtro_data)]
                
                st.dataframe(df_filtrado, use_container_width=True)
                
                # Opção para deletar perícias (apenas admin)
                if user_info['role'] == 'administrador':
                    st.markdown("#### 🗑️ Remover Perícia")
                    data_remover = st.selectbox(
                        "Selecione a data para remover",
                        [""] + list(pericias.keys())
                    )
                    
                    if data_remover and st.button("🗑️ Confirmar Remoção", type="secondary"):
                        pericias = load_pericias()
                        if data_remover in pericias:
                            del pericias[data_remover]
                            save_pericias(pericias)
                            st.success("✅ Perícia removida com sucesso!")
                            st.rerun()
            else:
                st.info("📭 Nenhuma perícia agendada ainda.")

if __name__ == "__main__":
    main()
