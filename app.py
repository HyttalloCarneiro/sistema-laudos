
import streamlit as st

# --- Sessão do usuário ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# --- Usuários demo temporários ---
DEMO_USERS = {
    "hyttallocarneiro": {"password": "admin123", "role": "admin"},
    "pauloramone": {"password": "paulo123", "role": "assistant"}
}

def login():
    user = st.session_state.get("login_user", "")
    pwd = st.session_state.get("login_pass", "")
    if user in DEMO_USERS and DEMO_USERS[user]["password"] == pwd:
        st.session_state.logged_in = True
        st.session_state.username = user
        st.session_state.role = DEMO_USERS[user]["role"]
    else:
        st.error("Email ou senha inválidos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

def user_menu():
    with st.container():
        st.markdown(
            f"""
            <div style='position: absolute; top: 10px; right: 30px; text-align: right;'>
                <div><b>Usuário:</b> {st.session_state.username}</div>
                <div><b>Perfil:</b> {st.session_state.role}</div>
                <form action="#" method="post">
                </form>
            </div>
            """,
            unsafe_allow_html=True
        )

        option = st.selectbox(
            "Selecionar ação",
            ["", "Cadastrar novo usuário", "Gerenciar usuários", "Alterar senha", "Sair"],
            key="user_action",
            label_visibility="collapsed"
        )

        if option == "Sair":
            logout()
            st.experimental_rerun()

        elif option == "Cadastrar novo usuário" and st.session_state.role == "admin":
            with st.form("cadastro"):
                new_user = st.text_input("Novo usuário (email ou nome de usuário)")
                new_pass = st.text_input("Senha inicial", type="password")
                new_role = st.selectbox("Perfil do novo usuário", ["assistant", "admin"])
                submitted = st.form_submit_button("Cadastrar")
                if submitted:
                    if new_user in DEMO_USERS:
                        st.warning("Usuário já existe.")
                    else:
                        DEMO_USERS[new_user] = {
                            "password": new_pass,
                            "role": new_role
                        }
                        st.success("Usuário cadastrado com sucesso!")

# --- Tela de login ---
if not st.session_state.logged_in:
    st.markdown("""<h1 style='text-align: center;'>Meu Perito</h1>""", unsafe_allow_html=True)
    st.text_input("Email (ou nome de utilizador)", key="login_user")
    st.text_input("Senha", type="password", key="login_pass")
    st.button("Entrar", on_click=login)
    st.stop()

# --- Interface principal ---
user_menu()
st.write("Conteúdo principal da aplicação pode começar aqui...")
