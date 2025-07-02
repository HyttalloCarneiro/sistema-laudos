import streamlit as st
import datetime
import uuid
import calendar
from PIL import Image

st.set_page_config(page_title="Meu Perito", layout="wide")

# --- DADOS EM MEMÓRIA (temporários) ---
DEMO_USERS = {
    "hyttallocarneiro": {"password": "admin123", "role": "admin", "first_login": False},
    "pauloramone": {"password": "paulo123", "role": "assistant", "first_login": True},
    "hc.periciamedica@hotmail.com": {"password": "admin123", "role": "admin", "first_login": False},
}

LOCATIONS = [
    {"id": "juazeiro", "name": "17ª Vara Federal", "city": "Juazeiro do Norte"},
    {"id": "salgueiro", "name": "20ª Vara Federal", "city": "Salgueiro"},
    {"id": "iguatu", "name": "25ª Vara Federal", "city": "Iguatu"},
    {"id": "ouricuri", "name": "27ª Vara Federal", "city": "Ouricuri"},
    {"id": "sousa", "name": "15ª Vara Federal", "city": "Sousa"},
    {"id": "diversas", "name": "Estaduais (Diversas varas)", "city": "Diversas"}
]

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "appointments" not in st.session_state:
    st.session_state.appointments = []
if "change_password_mode" not in st.session_state:
    st.session_state.change_password_mode = False
if "menu_option" not in st.session_state:
    st.session_state.menu_option = None

# --- FUNÇÕES ---
def login():
    user = st.session_state.user
    pwd = st.session_state.pwd
    if user in DEMO_USERS and DEMO_USERS[user]["password"] == pwd:
        st.session_state.username = user
        st.session_state.role = DEMO_USERS[user]["role"]
        if DEMO_USERS[user]["first_login"]:
            st.session_state.change_password_mode = True
        else:
            st.session_state.logged_in = True
    else:
        st.error("Email ou senha inválidos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.change_password_mode = False
    st.rerun()

def alterar_senha(usuario, senha_atual, nova_senha):
    if DEMO_USERS[usuario]["password"] != senha_atual:
        return False
    DEMO_USERS[usuario]["password"] = nova_senha
    DEMO_USERS[usuario]["first_login"] = False
    return True

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

# --- CSS PARA FUNDO E MENU TOPO ---
st.markdown("""
<style>
body {
    background-image: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1950&q=80');
    background-size: cover;
    background-position: center;
}
.login-box {
    background-color: rgba(255,255,255,0.9);
    padding: 2em;
    border-radius: 10px;
    width: 100%;
    max-width: 400px;
    margin: 5em auto;
}
.top-right-menu {
    position: absolute;
    top: 20px;
    right: 30px;
    background-color: #ffffffdd;
    padding: 10px 15px;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
if not st.session_state.logged_in and not st.session_state.change_password_mode:
    with st.container():
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.title("Meu Perito")
        st.text_input("Email (ou nome de utilizador)", key="user")
        st.text_input("Senha", type="password", key="pwd")
        st.button("Entrar", on_click=login)
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- FORÇA TROCA DE SENHA NO PRIMEIRO LOGIN ---
if st.session_state.change_password_mode:
    st.warning("Você deve alterar sua senha antes de continuar.")
    with st.form("first_change_form"):
        st.text_input("Senha atual", type="password", key="old_pass")
        st.text_input("Nova senha", type="password", key="new_pass")
        st.text_input("Confirme a nova senha", type="password", key="confirm_pass")
        if st.form_submit_button("Alterar senha"):
            if st.session_state.new_pass != st.session_state.confirm_pass:
                st.error("As senhas novas não coincidem.")
            elif alterar_senha(st.session_state.username, st.session_state.old_pass, st.session_state.new_pass):
                st.success("Senha alterada com sucesso!")
                st.session_state.change_password_mode = False
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Senha atual incorreta.")
    st.stop()

# --- MENU SUPERIOR DIREITO ---
st.markdown("""
<div class='top-right-menu'>
<b>Usuário:</b> {user}<br>
<small>perfil: {role}</small>
</div>
""".format(user=st.session_state.username, role=st.session_state.role), unsafe_allow_html=True)

option = st.selectbox("Selecionar ação", ["Cadastrar novo usuário", "Gerenciar usuários", "Alterar senha", "Sair"], key="menu_action")

if option == "Sair":
    logout()
elif option == "Alterar senha":
    with st.form("manual_change_form"):
        st.text_input("Senha atual", type="password", key="manual_old")
        st.text_input("Nova senha", type="password", key="manual_new")
        st.text_input("Confirmar nova senha", type="password", key="manual_confirm")
        if st.form_submit_button("Atualizar senha"):
            if st.session_state.manual_new != st.session_state.manual_confirm:
                st.error("As senhas novas não coincidem.")
            elif alterar_senha(st.session_state.username, st.session_state.manual_old, st.session_state.manual_new):
                st.success("Senha atualizada com sucesso!")
            else:
                st.error("Senha atual incorreta.")

elif option == "Cadastrar novo usuário" and st.session_state.role == "admin":
    with st.form("cadastro_form"):
        novo_usuario = st.text_input("Novo usuário (email ou nome de usuário)")
        nova_senha = st.text_input("Senha inicial", type="password")
        novo_perfil = st.selectbox("Perfil do novo usuário", ["admin", "assistant"])
        if st.form_submit_button("Cadastrar"):
            if novo_usuario in DEMO_USERS:
                st.error("Usuário já existe.")
            else:
                DEMO_USERS[novo_usuario] = {
                    "password": nova_senha,
                    "role": novo_perfil,
                    "first_login": True
                }
                st.success("Usuário cadastrado com sucesso!")
