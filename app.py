
import streamlit as st

# --- Sessão de estado ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "users" not in st.session_state:
    st.session_state.users = {
        "hyttallocarneiro": {"password": "admin123", "role": "admin"}
    }

# --- Login ---
def login():
    user = st.session_state.get("login_user", "")
    pwd = st.session_state.get("login_pass", "")
    if user in st.session_state.users and st.session_state.users[user]["password"] == pwd:
        st.session_state.logged_in = True
        st.session_state.username = user
        st.session_state.role = st.session_state.users[user]["role"]
    else:
        st.error("Usuário ou senha inválidos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# --- Cadastrar novo usuário (admin apenas) ---
def cadastrar_usuario():
    with st.sidebar.expander("👥 Cadastrar novo usuário"):
        novo_usuario = st.text_input("Novo usuário", key="novo_usuario")
        nova_senha = st.text_input("Senha", type="password", key="nova_senha")
        novo_perfil = st.selectbox("Perfil", ["assistant", "admin"], key="novo_perfil")
        if st.button("Cadastrar", key="botao_cadastro"):
            if novo_usuario in st.session_state.users:
                st.warning("Usuário já existe.")
            else:
                st.session_state.users[novo_usuario] = {"password": nova_senha, "role": novo_perfil}
                st.success("Usuário cadastrado com sucesso!")

# --- Tela de login ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>Meu Perito</h1>", unsafe_allow_html=True)
    st.text_input("Usuário", key="login_user")
    st.text_input("Senha", type="password", key="login_pass")
    st.button("Entrar", on_click=login)
    st.stop()

# --- Menu lateral ---
st.sidebar.title("👤 Usuário")
st.sidebar.write(f"Bem-vindo, **{st.session_state.username}**")
st.sidebar.write(f"Perfil: **{st.session_state.role}**")
st.sidebar.button("Sair", on_click=logout)

# --- Ações do administrador ---
if st.session_state.role == "admin":
    cadastrar_usuario()

# --- Página principal ---
st.title("Painel principal do sistema")
st.write("Bem-vindo ao sistema de laudos. As funcionalidades serão construídas etapa por etapa.")
