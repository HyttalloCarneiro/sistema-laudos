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

# Locais de atuação
LOCAIS_ATUACAO = [
    "17ª Vara Federal (Juazeiro do Norte)",
    "20ª Vara Federal (Salgueiro)",
    "25ª Vara Federal (Iguatu)",
    "27ª Vara Federal (Ouricuri)",
    "15ª Vara Federal (Sousa)",
    "Estaduais (Diversas varas)"
]

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
    """Cria visualização do calendário"""
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    st.subheader(f"📅 {month_name} {year}")
    
    # Cabeçalho dos dias da semana
    days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    cols = st.columns(7)
    for i, day in enumerate(days):
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
                    # Truncar nome do local para exibição
                    local_short = local.split('(')[0].strip() if '(' in local else local[:15]
                    cols[i].button(
                        f"**{day}**\n📍 {local_short}",
                        key=f"day_{date_str}",
                        help=f"Perícia em: {local}",
                        type="primary",
                        use_container_width=True
                    )
                else:
                
