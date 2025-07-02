import streamlit as st
import datetime
import uuid # Para gerar IDs únicos para agendamentos e locais

# --- Configurações Iniciais e Dados Hardcoded (DEMONSTRATIVOS) ---
# 🚨 ATENÇÃO: CREDENCIAIS HARDCODED. NÃO USE EM PRODUÇÃO!
# Para um sistema real, estas credenciais viriam de um backend seguro e banco de dados.
DEMO_USERS = {
    "dr.hyttallo": {"password": "admin_password", "role": "admin"},
    "assistente1": {"password": "assistant_password", "role": "assistant"},
    "assistente2": {"password": "assistant_password", "role": "assistant"},
}

# 🚨 ATENÇÃO: LOCAIS HARDCODED. Em um sistema real, seriam gerenciados via backend.
LOCATIONS = [
    {"id": str(uuid.uuid4()), "name": "17ª Vara Federal", "city": "Juazeiro do Norte"},
    {"id": str(uuid.uuid4()), "name": "20ª Vara Federal", "city": "Salgueiro"},
    {"id": str(uuid.uuid4()), "name": "25ª Vara Federal", "city": "Iguatu"},
    {"id": str(uuid.uuid4()), "name": "27ª Vara Federal", "city": "Ouricuri"},
    {"id": str(uuid.uuid4()), "name": "15ª Vara Federal", "city": "Sousa"},
    {"id": str(uuid.uuid4()), "name": "Estaduais (Diversas varas)", "city": "Diversas"}
]

# Inicialização das variáveis de estado de sessão do Streamlit
# Usamos session_state para manter o estado do app enquanto o usuário interage.
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "appointments" not in st.session_state:
    # Lista de dicionários para armazenar agendamentos:
    # [{"id": "...", "date": "...", "location_id": "...", "location_name": "...", "description": "..."}]
    st.session_state.appointments = []

# --- Funções de Autenticação (DEMONSTRATIVAS) ---
def login():
    username = st.session_state.login_username
    password = st.session_state.login_password
    if username in DEMO_USERS and DEMO_USERS[username]["password"] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_role = DEMO_USERS[username]["role"]
        st.success(f"Bem-vindo(a), {username.capitalize()}!")
        st.rerun() # Reinicia o app para ir para a tela principal
    else:
        st.error("Usuário ou senha inválidos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.success("Sessão encerrada.")
    st.rerun() # Reinicia o app para voltar para a tela de login

# --- Configuração da Página do Streamlit ---
st.set_page_config(
    page_title="Meu Perito - Sistema de Gerenciamento de Perícias",
    layout="wide", # Layout wide usa a largura total da tela
    initial_sidebar_state="expanded"
)

# --- Aviso de Segurança Importante ---
st.info("""
    **🚨 AVISO IMPORTANTE: CÓDIGO DEMONSTRATIVO PARA FLUXO DE UI ��**

    Este código `app.py` é uma **DEMONSTRAÇÃO VISUAL E FUNCIONAL** das suas solicitações,
    focando na interface de usuário (UI) e no fluxo de interação.

    **NÃO É SEGURO NEM ROBUSTO PARA USO EM PRODUÇÃO COM DADOS REAIS.**

    *   **Autenticação:** Credenciais hardcoded, sem hashing de senha.
    *   **Persistência de Dados:** Agendamentos armazenados apenas na sessão atual, **perdidos ao reiniciar o aplicativo**.
    *   **Autorização:** Lógica de permissões (admin/assistente) muito simplificada.

    Para um sistema real com dados sensíveis, é **INDISPENSÁVEL** a implementação de um **BACKEND DEDICADO**
    (com um framework como Django ou Flask, e um banco de dados como PostgreSQL) para gerenciar
    usuários, senhas criptografadas e persistência segura dos dados.
""")

# --- Lógica Principal do Aplicativo ---

# 1º) Módulo de Autenticação: Exigir usuário e senha
if not st.session_state.logged_in:
    st.title("🔐 Acesso ao Sistema Meu Perito")
    st.write("Por favor, insira suas credenciais para acessar o sistema.")
    with st.form("login_form", clear_on_submit=False):
        st.text_input("Usuário", key="login_username", help="Ex: dr.hyttallo ou assistente1")
        st.text_input("Senha", type="password", key="login_password", help="Ex: admin_password ou assistant_password")
        st.form_submit_button("Entrar", on_click=login)
else:
    # Usuário logado, exibe o aplicativo principal
    st.sidebar.title(f"Olá, Dr. {st.session_state.username.capitalize()} 👋")
    st.sidebar.write(f"**Perfil:** {st.session_state.user_role.capitalize()}")
    st.sidebar.button("Sair", on_click=logout, type="secondary")

    st.title("✨ Meu Perito: Gerenciamento de Agendamentos e Laudos")

    # 2º) Calendário e Inclusão de Perícias
    st.header("��️ Agendar Nova Perícia")
    today = datetime.date.today()
    
    # Campo para selecionar a data da perícia
    selected_date_for_add = st.date_input(
        "Selecione a data da perícia a ser agendada",
        today,
        help="Use este seletor para escolher o dia do agendamento."
    )

    # Exemplo conceitual de calendário mensal (Streamlit não tem uma grade de calendário nativa)
    st.subheader(f"Visão do Mês: {selected_date_for_add.strftime('%B de %Y')}")
    st.markdown(f"> **Dia Selecionado para Agendamento:** {selected_date_for_add.strftime('%d/%m/%Y')}")
    st.markdown("---")

    with st.form("add_appointment_form", clear_on_submit=True):
        st.subheader("📝 Detalhes da Perícia")
        
        # Seleção do local da perícia
        selected_location_name = st.selectbox(
            "Local da Perícia",
            options=[loc["name"] for loc in LOCATIONS],
            key="appointment_location",
            help="Escolha um dos locais de atuação."
        )
        
        description = st.text_area(
            "Observações da Perícia (opcional)",
            placeholder="Ex: Nome do periciado, tipo de perícia, observações relevantes...",
            key="appointment_description",
            height=100
        )

        if st.form_submit_button("Adicionar Perícia"):
            # Encontra o ID do local selecionado
            selected_location_id = next(loc["id"] for loc in LOCATIONS if loc["name"] == selected_location_name)

            new_appointment = {
                "id": str(uuid.uuid4()), # ID único para este agendamento
                "date": selected_date_for_add.isoformat(), # Armazena data como string ISO para compatibilidade
                "location_id": selected_location_id,
                "location_name": selected_location_name, # Armazena o nome para facilitar exibição
                "description": description if description else "Nenhuma observação."
            }
            st.session_state.appointments.append(new_appointment)
            st.success(f"✅ Perícia agendada para {selected_date_for_add.strftime('%d/%m/%Y')} em **{selected_location_name}**.")

    st.markdown("---")

    # 3º) Exposição dos Locais de Atuação
    st.header("🌍 Meus Locais de Atuação")
    st.write("Estes são os locais onde o Dr. Hyttallo realiza perícias:")

    # Exibição dos locais em colunas para melhor organização
    cols = st.columns(3) # Cria 3 colunas
    for i, loc in enumerate(LOCATIONS):
        with cols[i % 3]: # Distribui os locais pelas colunas
            st.markdown(f"- **{loc['name']}**")
            if loc['city']:
                st.markdown(f"  *{loc['city']}*")
    st.markdown("---")

    # 4º) Listagem e Filtragem de Perícias
    st.header("�� Próximas Perícias Agendadas")

    # Opções de filtro para o local
    all_locations_option = "Todos os Locais"
    filter_location_name = st.selectbox(
        "Filtrar Perícias por Local",
        options=[all_locations_option] + [loc["name"] for loc in LOCATIONS],
        key="filter_location_select",
        help="Selecione um local para ver as perícias específicas."
    )
    
    # Campo para filtrar por data (a partir de hoje)
    filter_start_date = st.date_input(
        "Ver perícias a partir de:",
        datetime.date.today(),
        help="As perícias serão listadas a partir desta data."
    )

    # Filtra os agendamentos
    filtered_appointments = []
    
    for appt in st.session_state.appointments:
        appt_date_obj = datetime.date.fromisoformat(appt["date"])
        
        # Filtra por data: apenas agendamentos a partir da data de filtro
        if appt_date_obj >= filter_start_date:
            # Filtra por local (se "Todos os Locais" não estiver selecionado)
            if filter_location_name == all_locations_option or appt["location_name"] == filter_location_name:
                filtered_appointments.append(appt)

    # Ordena os agendamentos por data para melhor visualização
    filtered_appointments.sort(key=lambda x: x["date"])

    if filtered_appointments:
        st.subheader(f"Perícias Encontradas ({len(filtered_appointments)}):")
        for appt in filtered_appointments:
            date_obj = datetime.date.fromisoformat(appt["date"])
            
            # Exibe os detalhes da perícia
            st.markdown(f"**🗓️ Data:** {date_obj.strftime('%d/%m/%Y')} | **📍 Local:** {appt['location_name']}")
            st.markdown(f"  **Observações:** {appt['description']}")
            
            # Botão de exclusão (visível apenas para administradores)
            if st.session_state.user_role == "admin":
                if st.button(
                    f"Excluir Perícia ({date_obj.strftime('%d/%m/%Y')} - {appt['location_name']})",
                    key=f"delete_btn_{appt['id']}",
                    type="secondary"
                ):
                    st.session_state.appointments.remove(appt)
                    st.success("🗑️ Perícia excluída com sucesso.")
                    st.rerun() # Recarrega a página para atualizar a lista
            st.markdown("---")
    else:
        st.info("Nenhuma perícia agendada para os filtros selecionados ou no futuro. Comece agendando uma acima!")
