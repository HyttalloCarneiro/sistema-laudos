import streamlit as st
import datetime
import uuid
import calendar

# ---------------------
# 1. CONFIGURAÇÃO INICIAL
# ---------------------
st.set_page_config(
    page_title="Meu Perito",
    layout="wide"
)

# DEMO USERS (login e perfil)
DEMO_USERS = {
    "dr.hyttallo": {"password": "admin123", "role": "admin"},
    "assistente1": {"password": "assist123", "role": "assistant"},
}

LOCATIONS = [
    {"id": "juazeiro", "name": "17ª Vara Federal", "city": "Juazeiro do Norte"},
    {"id": "salgueiro", "name": "20ª Vara Federal", "city": "Salgueiro"},
    {"id": "iguatu", "name": "25ª Vara Federal", "city": "Iguatu"},
    {"id": "ouricuri", "name": "27ª Vara Federal", "city": "Ouricuri"},
    {"id": "sousa", "name": "15ª Vara Federal", "city": "Sousa"},
    {"id": "diversas", "name": "Estaduais (Diversas varas)", "city": "Diversas"}
]

# Session State Inicial
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "appointments" not in st.session_state:
    st.session_state.appointments = []

# ---------------------
# 2. FUNÇÕES
# ---------------------
def login():
    user = st.session_state.user
    pwd = st.session_state.pwd
    if user in DEMO_USERS and DEMO_USERS[user]["password"] == pwd:
        st.session_state.logged_in = True
        st.session_state.username = user
        st.session_state.role = DEMO_USERS[user]["role"]
        st.success(f"Bem-vindo(a), {user}!")
        st.rerun()
    else:
        st.error("Usuário ou senha inválidos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

def render_calendar(month, year):
    st.subheader(f"Calendário de {calendar.month_name[month]} de {year}")
    days = calendar.monthcalendar(year, month)
    cols = st.columns(7)
    for i, name in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
        cols[i].markdown(f"**{name}**")

    for week in days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date_obj = datetime.date(year, month, day)
                if cols[i].button(str(day), key=f"day_{day}_{month}"):
                    st.session_state.selected_date = date_obj

# ---------------------
# 3. AUTENTICAÇÃO
# ---------------------
if not st.session_state.logged_in:
    st.title("🔐 Login")
    st.text_input("Usuário", key="user")
    st.text_input("Senha", key="pwd", type="password")
    st.button("Entrar", on_click=login)
    st.stop()

# ---------------------
# 4. TELA PRINCIPAL
# ---------------------
st.sidebar.title("👤 Usuário")
st.sidebar.write(f"Bem-vindo, **{st.session_state.username}**")
st.sidebar.write(f"Perfil: **{st.session_state.role}**")
st.sidebar.button("Sair", on_click=logout)

st.title("📅 Agenda de Perícias")

# Parte 1: Calendário
today = datetime.date.today()
month = st.sidebar.selectbox("Mês", list(range(1, 13)), index=today.month - 1)
year = st.sidebar.selectbox("Ano", list(range(today.year, today.year + 2)), index=0)

render_calendar(month, year)

selected_date = st.session_state.get("selected_date", today)
st.markdown(f"### Data Selecionada: {selected_date.strftime('%d/%m/%Y')}")

with st.form("add_pericia"):
    local = st.selectbox("Selecione o local da perícia", [l["name"] for l in LOCATIONS])
    obs = st.text_area("Observações (opcional)")
    submitted = st.form_submit_button("Agendar")
    if submitted:
        loc = next(l for l in LOCATIONS if l["name"] == local)
        new_appt = {
            "id": str(uuid.uuid4()),
            "date": selected_date.isoformat(),
            "location_id": loc["id"],
            "location_name": loc["name"],
            "description": obs or "-"
        }
        st.session_state.appointments.append(new_appt)
        st.success(f"Perícia agendada em {loc['name']} para {selected_date.strftime('%d/%m/%Y')}.")

# Parte 2: Locais
st.markdown("---")
st.subheader("📍 Locais de Atuação")
for loc in LOCATIONS:
    st.markdown(f"- **{loc['name']}** – *{loc['city']}*")

# Parte 3: Lista de Perícias
st.markdown("---")
st.subheader("📋 Perícias Agendadas")

filter_loc = st.selectbox("Filtrar por local", ["Todos"] + [l["name"] for l in LOCATIONS])
filtros = []

for appt in sorted(st.session_state.appointments, key=lambda x: x["date"]):
    appt_date = datetime.date.fromisoformat(appt["date"])
    if filter_loc != "Todos" and appt["location_name"] != filter_loc:
        continue
    filtros.append(appt)

if filtros:
    for appt in filtros:
        appt_date = datetime.date.fromisoformat(appt["date"])
        st.markdown(f"🗓️ {appt_date.strftime('%d/%m/%Y')} – **{appt['location_name']}**")
        st.markdown(f"↪️ {appt['description']}")
        if st.session_state.role == "admin":
            if st.button("Excluir", key=f"del_{appt['id']}"):
                st.session_state.appointments.remove(appt)
                st.rerun()
        st.markdown("---")
else:
    st.info("Nenhuma perícia encontrada para o filtro selecionado.")
