import os
import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import plotly.express as px
import plotly.graph_objects as go
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.supabase_database import SupabaseDatabase
from core.models.professor import Professor
from core.models.curso import Cursos
from core.models.disciplinas import Disciplinas
from core.models.analise import Analise
from core.models.ementa import Ementa, EmentaCreate
from core.services.google_drive_service import GoogleDriveService

# Adicionar o diretório raiz do projeto ao path para importar o módulo ai
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from ai import GroqClient

# Inicializa a base de dados
import importlib
import sys

# Forçar recarregamento do módulo para garantir que temos a versão mais recente
module_name = 'core.database.supabase_database'
if module_name in sys.modules:
    importlib.reload(sys.modules[module_name])

# Recarregar também o import
from core.database.supabase_database import SupabaseDatabase
importlib.reload(sys.modules[module_name])

# Criar instância do database
database = SupabaseDatabase()

# Atualizar cliente se necessário (já é feito no __init__ do SupabaseDatabase)
from core.config.supabase_config import supabase_config
if database.use_supabase:
    # Tentar usar service_role se disponível, senão usar anon
    database.client = supabase_config.get_client(use_service_role=True) or supabase_config.get_client()

# Verificar se os métodos necessários existem
required_methods = ['update_analise_comentario', 'check_analise_exists_for_ementa_and_curso']
missing_methods = [method for method in required_methods if not hasattr(database, method)]

if missing_methods:
    # Se ainda estiver faltando, tentar recriar o objeto
    print(f"⚠️ Métodos faltando: {missing_methods}. Recriando objeto database...")
    database = SupabaseDatabase()
    if database.use_supabase:
        database.client = supabase_config.get_client(use_service_role=True) or supabase_config.get_client()

# Inicializa o serviço do Google Drive
drive_service = GoogleDriveService()

# Configura a página do Streamlit
st.set_page_config(
    layout="wide", 
    page_title="Nexus Education", 
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# Ocultar sidebar completamente via CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# CSS personalizado minimalista com as cores especificadas
st.markdown("""
<style>
    /* Reset e configurações globais */
    .stApp {
        background-color: #ffffff;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background-color: #ffffff;
        color: #2c3e50;
        border-radius: 0;
        margin-bottom: 2rem;
        border-bottom: 2px solid #34495e;
    }
    
    /* Tipografia profissional */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Cores mais profissionais */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #34495e;
        --accent-color: #3498db;
        --text-color: #2c3e50;
        --border-color: #e0e0e0;
    }
    
    /* Melhorar espaçamentos e tipografia */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Estilo mais corporativo para métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #7f8c8d;
        font-weight: 500;
    }
    
    /* Bordas mais sutis */
    .stDataFrame, .stTable {
        border: 1px solid #e0e0e0;
    }
    
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 0 !important;
        border: none !important;
        border-radius: 0;
        background-color: transparent !important;
        box-shadow: none !important;
    }
    
    /* Garantir que os formulários tenham o mesmo tamanho */
    form[data-testid="stForm"] {
        max-width: 500px;
        margin: 0 auto;
        width: 100%;
    }
    
    /* Remover contorno do container do título */
    .login-container h3 {
        margin: 0 0 1.5rem 0;
        padding: 0;
        border: none !important;
    }
    
    /* Garantir que ambos os formulários tenham a mesma largura */
    #login_form,
    #register_form {
        max-width: 500px;
        margin: 0 auto;
        width: 100%;
    }
    
    .course-card {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }
    
    .course-card h4 {
        margin: 0 0 0.5rem 0;
        color: #000000;
        font-weight: 600;
    }
    
    .course-card p {
        margin: 0;
        color: #000000;
        opacity: 0.7;
    }
    
    .discipline-item {
        background-color: #ffffff;
        border: 1px solid #5271ff;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.25rem 0;
        transition: all 0.2s ease;
    }
    
    .discipline-item:hover {
        background-color: rgba(82, 113, 255, 0.05);
        border-color: #5271ff;
    }
    
    .upload-area {
        border: 2px dashed #bdc3c7;
        border-radius: 6px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        color: #2c3e50;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #28a745;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #dc3545;
    }
    
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #17a2b8;
    }
    
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #ffc107;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #5271ff;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(82, 113, 255, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #5271ff;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #000000;
        opacity: 0.7;
        margin: 0;
    }
    
    .main-content {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid #5271ff;
    }
    
    /* Botões personalizados */
    .stButton > button {
        background-color: #5271ff;
        color: #ffffff;
        border: none !important;
        border-radius: 4px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        outline: none !important;
    }
    
    .stButton > button:hover {
        background-color: #4056e6;
        box-shadow: 0 2px 6px rgba(82, 113, 255, 0.3);
        border: none !important;
        outline: none !important;
    }
    
    .stButton > button:focus {
        border: none !important;
        outline: none !important;
        box-shadow: 0 2px 4px rgba(82, 113, 255, 0.2);
    }
    
    /* Remover contorno dos botões de formulário (login e cadastro) */
    form .stButton > button,
    form button[type="submit"],
    .stForm .stButton > button {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .stForm .stButton > button:hover,
    .stForm .stButton > button:focus {
        border: none !important;
        outline: none !important;
    }
    
    /* Tabs styling - Centralizar e mesmo tamanho */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: center !important;
        gap: 0 !important;
        width: 100% !important;
        margin: 0 auto !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        flex: 1 !important;
        max-width: 250px !important;
        min-width: 200px !important;
        text-align: center !important;
        padding: 0.75rem 1rem !important;
    }
    
    /* Garantir que o container das tabs esteja centralizado */
    div[data-testid="stTabs"] {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    
    div[data-testid="stTabs"] > div {
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        background-color: #ffffff;
        color: #2c3e50;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2c3e50;
        box-shadow: 0 0 0 2px rgba(44, 62, 80, 0.1);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > div {
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        background-color: #ffffff;
        color: #2c3e50;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        color: #2c3e50;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-top: none;
        border-radius: 0 0 4px 4px;
    }
    
    /* Logo styling */
    .logo-container {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid #5271ff;
    }
    
    .logo-network {
        width: 60px;
        height: 40px;
        margin: 0 auto 1rem;
        display: block;
    }
    
    .logo-text {
        color: #000000;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .logo-subtitle {
        color: #000000;
        font-size: 0.8rem;
        font-weight: 400;
        margin: 0.25rem 0;
        opacity: 0.8;
    }
    
    .logo-line {
        width: 60px;
        height: 2px;
        background-color: #2c3e50;
        margin: 0.5rem auto 0;
        border-radius: 1px;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        color: #2c3e50;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #5271ff;
        color: #ffffff;
        border-color: #5271ff;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 4px;
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }
    
    [data-testid="metric-container"] > div {
        color: #2c3e50;
    }
    
    [data-testid="metric-value"] {
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* Remove default Streamlit styling */
    .stApp > header {
        background-color: #ffffff;
    }
    
    .stApp > header > div {
        background-color: #ffffff;
    }
    
    /* Barra de navegação no topo */
    .top-navbar {
        background-color: #ffffff;
        border-bottom: 2px solid #5271ff;
        padding: 1rem 2rem;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .nav-left {
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    
    .nav-logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .nav-logo img {
        height: 40px;
        width: auto;
    }
    
    .nav-user-info {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .nav-user-info h4 {
        margin: 0;
        color: #2c3e50;
        font-size: 1rem;
    }
    
    .nav-user-info p {
        margin: 0;
        color: #7f8c8d;
        font-size: 0.85rem;
    }
    
    .nav-buttons {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .nav-button {
        padding: 0.5rem 1rem;
        border-radius: 4px;
        border: 1px solid #5271ff;
        background-color: #ffffff;
        color: #5271ff;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
    }
    
    .nav-button:hover {
        background-color: #5271ff;
        color: #ffffff;
    }
    
    .nav-button.active {
        background-color: #5271ff;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# Função para verificar se o usuário está logado
def is_logged_in():
    return 'user_logged_in' in st.session_state and st.session_state.user_logged_in

# Função para lidar com erros de token do Google Drive
def handle_drive_token_error():
    """Lida com erros de token do Google Drive"""
    st.error("Token do Google Drive expirado.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Para resolver este problema:**
        
        1. **Opção 1 - Renovar automaticamente:**
           - Clique no botão "Renovar Token" abaixo
           - Siga as instruções no navegador
        
        2. **Opção 2 - Renovar manualmente:**
           - Execute: `python renovar_token.py`
           - Siga as instruções no terminal
        
        3. **Opção 3 - Processar sem Google Drive:**
           - Use apenas análise local (sem upload)
        """)
    
    with col2:
        if st.button("Renovar Token", type="primary"):
            try:
                # Tentar renovar o token
                if drive_service.authenticate():
                    st.success("✅ Token renovado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Falha ao renovar token. Tente a opção manual.")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
        
        if st.button("Processar Sem Drive"):
            st.session_state['skip_drive'] = True
            st.success("✅ Modo local ativado. PDFs serão processados localmente.")
            st.rerun()

# Função para fazer logout
def logout():
    for key in ['user_logged_in', 'user_data', 'selected_course']:
        if key in st.session_state:
            del st.session_state[key]

# Função para hash da senha
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Função para converter datetime para string JSON-serializable
def convert_datetime_for_json(data: dict) -> dict:
    """Converte objetos datetime em strings para serialização JSON"""
    converted = data.copy()
    for key, value in converted.items():
        if isinstance(value, datetime):
            converted[key] = value.isoformat()
        elif isinstance(value, dict):
            converted[key] = convert_datetime_for_json(value)
    return converted

# Função para validar email (apenas emails que contenham @ifsp)
def is_valid_email(email: str) -> bool:
    import re
    
    # Verificar formato básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    
    # Verificar se o email contém @ifsp
    email_lower = email.lower()
    return '@ifsp' in email_lower

# Função para validar senha
def is_valid_password(password: str) -> tuple[bool, str]:
    """
    Valida se a senha atende aos requisitos:
    - Pelo menos um número
    - Pelo menos um caractere especial: #, @, $, !, _, *
    
    Retorna: (é_válida, mensagem_erro)
    """
    import re
    
    if not password:
        return False, "Senha não pode estar vazia!"
    
    # Verificar se tem pelo menos um número
    if not re.search(r'\d', password):
        return False, "A senha deve conter pelo menos um número!"
    
    # Verificar se tem pelo menos um caractere especial permitido
    special_chars = ['#', '@', '$', '!', '_', '*']
    if not any(char in password for char in special_chars):
        return False, "A senha deve conter pelo menos um caractere especial (#, @, $, !, _, *)!"
    
    return True, ""

# Função para cadastrar professor
def register_professor(professor_data: Dict) -> bool:
    try:
        # Verificar se email já existe
        if database.verify_email_exists(professor_data['email_educacional']):
            st.error("Email já cadastrado!")
            return False
        
        # Verificar se prontuário já existe
        if database.verify_prontuario_exists(professor_data['prontuario']):
            st.error("Prontuário já cadastrado!")
            return False
        
        # Hash da senha
        professor_data['senha'] = hash_password(professor_data['senha'])
        
        # Criar professor
        professor_info = {
            'prontuario': professor_data['prontuario'],
            'nome': professor_data['nome'],
            'email_educacional': professor_data['email_educacional'],
            'senha': professor_data['senha']
        }
        
        professor = Professor(**professor_info)
        database.create_professor(convert_datetime_for_json(professor.model_dump()))
        
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar: {str(e)}")
        import traceback
        st.error(f"Detalhes do erro: {traceback.format_exc()}")
        return False

# Função para autenticar professor por email
def authenticate_professor(email: str, senha: str) -> Optional[Dict]:
    try:
        senha_hash = hash_password(senha)
        # Usar service role para autenticação também
        from core.config.supabase_config import supabase_config
        temp_client = supabase_config.get_client(use_service_role=True)
        database.client = temp_client
        
        professor = database.authenticate_professor(email, senha_hash)
        if professor:
            return professor
        return None
    except Exception as e:
        st.error(f"Erro na autenticação: {str(e)}")
        return None

# Função para autenticar professor por prontuário
def authenticate_professor_by_prontuario(prontuario: str, senha: str) -> Optional[Dict]:
    try:
        # Usar service role para autenticação também
        from core.config.supabase_config import supabase_config
        temp_client = supabase_config.get_client(use_service_role=True)
        database.client = temp_client
        
        # Passar a senha sem hash - a função do banco já faz o hash
        professor = database.authenticate_professor_by_prontuario(prontuario, senha)
        if professor:
            return professor
        return None
    except Exception as e:
        st.error(f"Erro na autenticação: {str(e)}")
        return None

# Função unificada para autenticar professor (detecta automaticamente email ou prontuário)
def authenticate_professor_unified(login_field: str, senha: str) -> Optional[Dict]:
    """Autentica professor detectando automaticamente se é email ou prontuário"""
    try:
        if is_valid_email(login_field):
            # É um email
            return authenticate_professor(login_field, senha)
        elif len(login_field) == 9:
            # É um prontuário
            return authenticate_professor_by_prontuario(login_field, senha)
        else:
            return None
    except Exception as e:
        st.error(f"Erro na autenticação: {str(e)}")
        return None

# Função para processar uploads de PDFs
def process_uploaded_files(uploaded_files, course_code: str, professor_prontuario: str) -> List[Dict]:
    """Processa arquivos PDFs enviados e cria registros de ementas"""
    if not uploaded_files:
        return []
    
    if len(uploaded_files) < 1:
        st.error("Selecione pelo menos 1 PDF!")
        return []
    
    if len(uploaded_files) > 5:
        st.error("Máximo 5 PDFs por lote!")
        return []
    
    # Verificar se Google Drive está configurado
    drive_available = os.path.exists('credentials.json')
    
    if not drive_available:
        st.warning("Google Drive não configurado. Arquivos serão salvos apenas localmente.")
    
    # Processar uploads
    ementas_data = []
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            # Salvar arquivo temporariamente
            file_path = f"src/data/uploads/{uploaded_file.name}"
            os.makedirs("src/data/uploads", exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Upload para Google Drive se disponível
            drive_id = None
            if drive_available and not st.session_state.get('skip_drive', False):
                try:
                    with st.spinner(f"Enviando {uploaded_file.name} para o Google Drive..."):
                        drive_id = drive_service.upload_file(
                            file_path, 
                            uploaded_file.name, 
                            'application/pdf'
                        )
                    
                    if drive_id:
                        st.success(f"{uploaded_file.name} enviado para o Google Drive.")
                    else:
                        st.warning(f"Falha ao enviar {uploaded_file.name} para o Google Drive")
                except Exception as e:
                    error_msg = str(e)
                    if "invalid_grant" in error_msg or "Token has been expired" in error_msg:
                        st.error(f"Token do Google Drive expirado para {uploaded_file.name}")
                        handle_drive_token_error()
                        return []  # Parar processamento
                    else:
                        st.warning(f"Erro ao enviar {uploaded_file.name} para o Google Drive: {error_msg}")
                        st.info("Continuando com processamento local...")
            else:
                drive_id = f"local_{i}_{datetime.now().timestamp()}"
            
            # Criar registro da ementa (sem id_ementa - será gerado pelo Supabase)
            ementa_data = {
                'drive_id': drive_id,
                'data_upload': datetime.now()
            }
            
            # Usar apenas os campos necessários para criação
            ementa_dict = convert_datetime_for_json(ementa_data)
            ementa_dict['professor_id'] = professor_prontuario
            
            try:
                ementa_result = database.create_ementa(ementa_dict)
                
                if ementa_result and 'id_ementa' in ementa_result:
                    ementa_id = ementa_result['id_ementa']
                    ementas_data.append({
                        'id_ementa': ementa_id,
                        'nome_arquivo': uploaded_file.name,
                        'caminho': file_path,
                        'drive_id': drive_id
                    })
                    st.success(f"✅ {uploaded_file.name} processado com sucesso (ID: {ementa_id})")
                else:
                    st.error(f"❌ Erro ao criar registro da ementa para {uploaded_file.name}. Resultado: {ementa_result}")
                    continue
            except Exception as e:
                st.error(f"❌ Erro ao criar ementa para {uploaded_file.name}: {str(e)}")
                import traceback
                st.error(f"Detalhes: {traceback.format_exc()}")
                continue
                
        except Exception as e:
            st.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")
    
    return ementas_data

# Função para upload de PDFs (mantida para compatibilidade)
def upload_pdfs(course_code: str, professor_prontuario: str) -> List[Dict]:
    """Função legada - use process_uploaded_files diretamente"""
    uploaded_files = st.file_uploader(
        "Selecione os PDFs (Ementa + Histórico Escolar)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Mínimo 1 PDF, máximo 5 PDFs por lote"
    )
    
    if uploaded_files:
        return process_uploaded_files(uploaded_files, course_code, professor_prontuario)
    
    return []

# Função para análise real com IA
def process_analysis_with_ai(ementa_id: int, course_code: str, professor_prontuario: str) -> List[Dict]:
    """Processa análise real usando IA"""
    
    try:
        # Inicializar cliente de IA
        ai_client = GroqClient()
    except ValueError as e:
        st.error(f"Erro de configuração da API: {str(e)}")
        st.info("Para configurar a chave da API do Groq:")
        st.info("1. Acesse https://console.groq.com/keys")
        st.info("2. Crie uma conta e obtenha sua chave da API")
        st.info("3. Configure a variável de ambiente GROQ_API_KEY ou crie um arquivo .env")
        return []
    
    try:
        # Verificar se ementa_id é válido
        if not ementa_id or ementa_id is None:
            st.error("ID da ementa inválido. Verifique se o upload foi realizado corretamente.")
            return []
        
        # Buscar dados da ementa
        ementa_data = database.get_ementa_by_id(ementa_id)
        if not ementa_data:
            st.error(f"❌ Ementa {ementa_id} não encontrada no banco de dados.")
            return []
        
        # Verificar se a ementa tem arquivo associado
        if not ementa_data.get('file_path') and not ementa_data.get('drive_id'):
            st.error(f"❌ Ementa {ementa_id} não possui arquivo PDF associado. Não é possível processar a análise.")
            return []
        
        # Buscar dados do curso
        curso_data = database.get_curso_by_codigo(course_code)
        if not curso_data:
            st.error(f"Curso {course_code} não encontrado!")
            return []
        
        # Se a ementa tem drive_id, baixar do Google Drive
        if ementa_data.get('drive_id') and not ementa_data['drive_id'].startswith('local_'):
            with st.spinner("Baixando ementa do Google Drive..."):
                file_content = drive_service.download_file(
                    ementa_data['drive_id'], 
                    f"ementa_{ementa_id}.pdf"
                )
                if file_content:
                    # Salvar temporariamente
                    temp_path = f"src/data/uploads/temp_ementa_{ementa_id}.pdf"
                    os.makedirs("src/data/uploads", exist_ok=True)
                    with open(temp_path, "wb") as f:
                        f.write(file_content)
                    
                    # Extrair dados do PDF usando sistema híbrido (rápido + IA)
                    from helper import read_pdf_with_docling
                    pdf_data = read_pdf_with_docling(temp_path, ai_client)
                    texto_ementa = pdf_data.get("text", "")
                    structured_data = pdf_data.get("structured_data")
                    extraction_method = pdf_data.get("method", "unknown")
                    
                    # Exibir método de extração
                    if extraction_method == "pymupdf_ai_structured":
                        st.success("Extração rápida + IA para estruturação")
                    elif extraction_method == "docling":
                        st.info("Usando Docling para extração estruturada")
                    elif extraction_method == "pymupdf_fast":
                        st.info("Extração rápida com PyMuPDF")
                    elif extraction_method == "pymupdf_fallback":
                        st.warning("Fallback para PyMuPDF simples")
                    
                    # Limpar arquivo temporário
                    os.remove(temp_path)
                else:
                    st.error("Erro ao baixar ementa do Google Drive")
                    return []
        else:
            # Buscar arquivo local
            local_files = [f for f in os.listdir("src/data/uploads") if not f.startswith("temp_")]
            matching_files = [f for f in local_files if f.endswith(".pdf")]
            
            if matching_files:
                file_path = f"src/data/uploads/{matching_files[-1]}"  # Usar o último arquivo
                
                # Extrair dados do PDF usando sistema híbrido (rápido + IA)
                from helper import read_pdf_with_docling
                pdf_data = read_pdf_with_docling(file_path, ai_client)
                texto_ementa = pdf_data.get("text", "")
                structured_data = pdf_data.get("structured_data")
                extraction_method = pdf_data.get("method", "unknown")
                
                # Exibir método de extração
                if extraction_method == "pymupdf_ai_structured":
                    st.success("Extração rápida + IA para estruturação")
                elif extraction_method == "docling":
                    st.info("Usando Docling para extração estruturada")
                elif extraction_method == "pymupdf_fast":
                    st.info("Extração rápida com PyMuPDF")
                elif extraction_method == "pymupdf_fallback":
                    st.warning("Fallback para PyMuPDF simples")
            else:
                st.error("Arquivo da ementa não encontrado!")
                return []
        
        if not texto_ementa.strip():
            st.error("Não foi possível extrair texto da ementa!")
            return []
        
        # Gerar resumo da ementa
        with st.spinner("Gerando resumo da ementa..."):
            resumo_ementa = ai_client.resume_ementa(texto_ementa)
        
        # Gerar score da análise
        with st.spinner("Calculando score da análise..."):
            score = ai_client.generate_score(resumo_ementa, curso_data)
            if score is None:
                score = 5.0  # Score padrão
            
            # Garantir que score é um número válido
            try:
                score = float(score)
                if score < 0 or score > 10:
                    score = 5.0  # Score padrão se fora do range
            except (ValueError, TypeError):
                score = 5.0  # Score padrão se não conseguir converter
        
        # Gerar análise detalhada
        with st.spinner("Gerando análise detalhada..."):
            texto_analise = ai_client.generate_opinion(resumo_ementa, curso_data)
        
        # Extrair nome do aluno do resumo ou dos dados estruturados
        import re
        nome_aluno = "Nome não identificado"
        
        # Tentar extrair do Docling primeiro
        if 'structured_data' in locals() and structured_data:
            student_info = structured_data.get("student_info", {})
            if student_info.get("nome"):
                nome_aluno = student_info["nome"]
        
        # Fallback para regex no resumo
        if nome_aluno == "Nome não identificado":
            nome_match = re.search(r"## Nome Completo\s*(.*)", resumo_ementa)
            nome_aluno = nome_match.group(1).strip() if nome_match else "Nome não identificado"
        
        # Criar dados da análise com JSON estruturado do Docling
        analise_data = {
            'ementa_fk': ementa_id,
            'nome_aluno': nome_aluno,
            'adequado': score >= 7.0,
            'score': int(score * 10),  # Converter para escala 0-100
            'texto_analise': texto_analise,
            'materias_restantes': "Ver análise detalhada" if score < 7.0 else "Nenhuma"
        }
        
        # Adicionar dados estruturados se disponível
        if 'structured_data' in locals() and structured_data:
            analise_data['dados_estruturados_json'] = json.dumps(structured_data, ensure_ascii=False)
        
        # Salvar análise no banco
        try:
            # Criar objeto Analise
            analise = Analise(**analise_data)
            analise_dict = convert_datetime_for_json(analise.model_dump())
            analise_dict['professor_id'] = professor_prontuario
            
            # Garantir que todos os campos obrigatórios estão presentes
            required_fields = {
                'nome_aluno': analise_dict.get('nome_aluno', 'Nome não identificado'),
                'ementa_fk': analise_dict.get('ementa_fk'),
                'adequado': analise_dict.get('adequado', False),
                'score': analise_dict.get('score', 0),
                'texto_analise': analise_dict.get('texto_analise', ''),
                'professor_id': analise_dict.get('professor_id', professor_prontuario)
            }
            
            # Atualizar analise_dict com campos obrigatórios
            analise_dict.update(required_fields)
            
            # Salvar no banco com relacionamento ao curso
            print(f"🔍 [DEBUG] Salvando análise com curso_codigo: {course_code}")
            print(f"🔍 [DEBUG] Dados da análise: {analise_dict.keys()}")
            analise_result = database.create_analise(analise_dict, curso_codigo=course_code)
            
            if analise_result:
                analise_id = analise_result.get('analise_id')
                analise_data['analise_id'] = analise_id
                
                if analise_id:
                    st.success(f"✅ Análise salva com sucesso! ID: {analise_id} | Vinculada ao curso: {course_code}")
                    
                    # Verificar se o relacionamento foi criado (aguardar um pouco para garantir que foi processado)
                    import time
                    time.sleep(0.5)
                    
                    try:
                        analise_cursos = database.get_analise_cursos(analise_id)
                        print(f"🔍 [DEBUG] Cursos relacionados à análise {analise_id}: {analise_cursos}")
                        
                        if analise_cursos and len(analise_cursos) > 0:
                            curso_encontrado = any(c.get('codigo_curso') == course_code or c.get('curso_fk') == course_code for c in analise_cursos)
                            if curso_encontrado:
                                st.success(f"✅ Relacionamento com curso {course_code} criado com sucesso!")
                            else:
                                st.warning(f"⚠️ Análise salva, mas relacionamento com curso {course_code} não encontrado.")
                                st.info(f"   Cursos encontrados: {[c.get('codigo_curso', c.get('curso_fk', 'N/A')) for c in analise_cursos]}")
                        else:
                            st.warning(f"⚠️ Análise salva, mas nenhum relacionamento com curso foi encontrado.")
                            st.info(f"   Verifique os logs do console para mais detalhes.")
                    except Exception as e:
                        print(f"❌ Erro ao verificar relacionamento: {e}")
                        st.warning(f"⚠️ Análise salva, mas não foi possível verificar o relacionamento com o curso.")
                else:
                    st.warning(f"⚠️ Análise salva, mas ID não foi retornado.")
            else:
                st.error("❌ Falha ao salvar análise no banco de dados. Verifique os logs para mais detalhes.")
                analise_data['analise_id'] = None
                
        except Exception as e:
            st.error(f"❌ Erro ao salvar análise: {str(e)}")
            import traceback
            st.error(f"Detalhes do erro: {traceback.format_exc()}")
            analise_data['analise_id'] = None
        
        return [analise_data]
    
    except Exception as e:
        st.error(f"Erro ao processar análise: {str(e)}")
        return []

# ==================== INTERFACE PRINCIPAL ====================

# Cabeçalho principal

# Verificar se usuário está logado
if not is_logged_in():
    # ==================== PÁGINA DE LOGIN ====================
    
    # Logo no topo da página de login/cadastro
    logo_path = os.path.join(project_root, "images", "logo-nexus.png")
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, use_container_width=True)
    
    # Tabs para Login e Cadastro
    # Se show_login_tab estiver definido, mostrar login primeiro
    if st.session_state.get('show_login_tab', False):
        tab1, tab2 = st.tabs(["Login", "Cadastro"])
        # Limpar o flag após usar
        del st.session_state['show_login_tab']
    else:
        tab1, tab2 = st.tabs(["Login", "Cadastro"])
    
    with tab1:
        # Mostrar mensagem se foi redirecionado do cadastro
        if st.session_state.get('show_login_tab', False):
            st.success("Cadastro realizado com sucesso. Faça login com suas credenciais.")
        
        with st.form("login_form"):
            st.markdown("""
            <div class="login-container">
                <h3 style="text-align: center; margin-bottom: 1.5rem;">Login</h3>
            </div>
            """, unsafe_allow_html=True)
            
            login_field = st.text_input("Email ou Prontuário", placeholder="seu.email@universidade.edu ou SP1234567")
            senha = st.text_input("Senha", type="password")
            
            # Botão centralizado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                login_submitted = st.form_submit_button("Entrar", use_container_width=True)
        
        if login_submitted:
            if login_field and senha:
                # Detectar automaticamente se é email ou prontuário e autenticar
                professor = authenticate_professor_unified(login_field, senha)
                if professor:
                    st.session_state.user_logged_in = True
                    st.session_state.user_data = professor
                    
                    # Verificar se o professor tem cursos associados
                    professor_courses = database.get_professor_courses(professor['prontuario'])
                    if not professor_courses:
                        # Se não tiver cursos, redirecionar para gerenciamento
                        st.session_state.current_page = "gerenciar_cursos"
                    else:
                        # Se tiver cursos, ir para página principal
                        st.session_state.current_page = "home"
                    
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    # Verificar se o formato está correto
                    if is_valid_email(login_field):
                        st.error("Email ou senha incorretos!")
                    elif len(login_field) == 9:
                        st.error("Prontuário ou senha incorretos!")
                    else:
                        st.error("Digite um email válido ou um prontuário de 9 dígitos!")
            else:
                st.error("Preencha todos os campos!")
    
    with tab2:
        with st.form("register_form"):
            st.markdown("""
            <div class="login-container">
                <h3 style="text-align: center; margin-bottom: 1.5rem;">Cadastrar</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Dados Pessoais")
            nome = st.text_input("Nome Completo", placeholder="Seu nome completo")
            prontuario = st.text_input("Prontuário", placeholder="SP3456789", max_chars=9)
            email = st.text_input("Email Educacional", placeholder="seu.email@ifsp.edu.br")
            senha = st.text_input("Senha", type="password", help="A senha deve conter pelo menos um número e um caractere especial (#, @, $, !, _, *)")
            confirmar_senha = st.text_input("Confirmar Senha", type="password")
            
            st.info("Após o cadastro, você poderá selecionar os cursos que leciona na área do professor.")
            st.info("Email permitido: apenas emails que contenham @ifsp")
            st.info("Senha: deve conter pelo menos um número e um caractere especial (#, @, $, !, _, *)")
            
            # Botão de cadastro centralizado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                cadastrar_submitted = st.form_submit_button("Cadastrar", use_container_width=True)
        
        if cadastrar_submitted:
            if nome and prontuario and email and senha and confirmar_senha:
                if senha != confirmar_senha:
                    st.error("Senhas não coincidem!")
                elif not is_valid_email(email):
                    st.error("Email inválido! O email deve conter @ifsp")
                elif len(prontuario) != 9:
                    st.error("Prontuário deve ter 9 dígitos!")
                else:
                    # Validar senha
                    senha_valida, mensagem_erro = is_valid_password(senha)
                    if not senha_valida:
                        st.error(mensagem_erro)
                    else:
                        professor_data = {
                            'prontuario': prontuario,
                            'nome': nome,
                            'email_educacional': email,
                            'senha': senha
                        }
                        
                        success = register_professor(professor_data)
                        if success:
                            st.success("Cadastro realizado com sucesso.")
                            st.info("Realizando login automaticamente...")
                            
                            # Fazer login automático após cadastro
                            professor = authenticate_professor(email, senha)
                            if professor:
                                st.session_state.user_logged_in = True
                                st.session_state.user_data = professor
                                
                                # Verificar se o professor tem cursos associados
                                professor_courses = database.get_professor_courses(professor['prontuario'])
                                if not professor_courses:
                                    # Se não tiver cursos, redirecionar para gerenciamento
                                    st.session_state.current_page = "gerenciar_cursos"
                                else:
                                    # Se tiver cursos, ir para página principal
                                    st.session_state.current_page = "home"
                                
                                st.success("Login automático realizado com sucesso.")
                                st.rerun()
                            else:
                                st.error("Erro no login automático. Faça login manualmente.")
                                st.session_state['show_login_tab'] = True
                                st.rerun()

else:
    # ==================== ÁREA LOGADA ====================
    
    # Inicializar página atual se não existir
    if 'current_page' not in st.session_state:
        # Verificar se o professor tem cursos associados
        professor_courses = database.get_professor_courses(st.session_state.user_data['prontuario'])
        st.session_state.professor_courses = professor_courses
        if not professor_courses:
            st.session_state.current_page = "gerenciar_cursos"
        else:
            st.session_state.current_page = "home"
    
    # Garantir que os cursos estão no session_state (só recarregar se não existir)
    if 'professor_courses' not in st.session_state:
        professor_courses = database.get_professor_courses(st.session_state.user_data['prontuario'])
        st.session_state.professor_courses = professor_courses
    
    # Barra de navegação no topo
    logo_path = os.path.join(project_root, "images", "logo-nexus.png")
    
    # Criar barra de navegação no topo - agrupando logo e informações do usuário
    nav_col1, nav_col2, nav_col3 = st.columns([3, 2, 2])
    
    with nav_col1:
        # Container com logo e informações do usuário agrupadas
        logo_user_col1, logo_user_col2 = st.columns([1, 2])
        
        with logo_user_col1:
            # Logo do Nexus Education (aumentada)
            if os.path.exists(logo_path):
                st.image(logo_path, width=300)
            else:
                # Fallback para SVG caso a imagem não exista (aumentado)
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg viewBox="0 0 60 40" xmlns="http://www.w3.org/2000/svg" style="width: 120px; height: 80px;">
                    <circle cx="30" cy="8" r="4" fill="#5271ff" stroke="none"/>
                    <circle cx="15" cy="20" r="4" fill="#5271ff" stroke="none"/>
                    <circle cx="45" cy="20" r="4" fill="#5271ff" stroke="none"/>
                    <circle cx="8" cy="32" r="4" fill="#5271ff" stroke="none"/>
                    <circle cx="22" cy="32" r="4" fill="#5271ff" stroke="none"/>
                    <circle cx="38" cy="32" r="4" fill="#5271ff" stroke="none"/>
                    <circle cx="52" cy="32" r="4" fill="#5271ff" stroke="none"/>
                    <line x1="30" y1="12" x2="15" y2="16" stroke="#5271ff" stroke-width="2"/>
                    <line x1="30" y1="12" x2="45" y2="16" stroke="#5271ff" stroke-width="2"/>
                    <line x1="15" y1="24" x2="8" y2="28" stroke="#5271ff" stroke-width="2"/>
                    <line x1="15" y1="24" x2="22" y2="28" stroke="#5271ff" stroke-width="2"/>
                    <line x1="45" y1="24" x2="38" y2="28" stroke="#5271ff" stroke-width="2"/>
                    <line x1="45" y1="24" x2="52" y2="28" stroke="#5271ff" stroke-width="2"/>
                </svg>
                    <div>
                        <h3 style="margin: 0; color: #2c3e50; font-size: 2rem;">Nexus</h3>
                        <p style="margin: 0; color: #7f8c8d; font-size: 1.2rem;">EDUCATION</p>
                    </div>
            </div>
            """, unsafe_allow_html=True)
        
        with logo_user_col2:
            # Informações do usuário (agrupadas com a logo)
            st.markdown(f"<h4 style='margin-bottom: 0.5rem; font-size: 1.3rem;'>{st.session_state.user_data['nome']}</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 0.95rem; margin: 0.3rem 0;'><strong>Prontuário:</strong> {st.session_state.user_data['prontuario']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 0.95rem; margin: 0.3rem 0;'><strong>Email:</strong> {st.session_state.user_data['email_educacional']}</p>", unsafe_allow_html=True)
    
    with nav_col2:
        # Espaço vazio para balanceamento
        st.empty()
    
    with nav_col3:
        # Botões de navegação (sem emojis)
        nav_btn1, nav_btn2, nav_btn3 = st.columns(3)
        
        with nav_btn1:
            if st.button("Principal", use_container_width=True, 
                     type="primary" if st.session_state.current_page == "home" else "secondary"):
                st.session_state.current_page = "home"
                st.rerun()
        
        with nav_btn2:
            if st.button("Gerenciamento", use_container_width=True,
                     type="primary" if st.session_state.current_page == "gerenciar_cursos" else "secondary"):
                st.session_state.current_page = "gerenciar_cursos"
                st.rerun()
        
        with nav_btn3:
            if st.button("Sair", use_container_width=True):
                logout()
                st.rerun()
    
    st.markdown("---")
    
    # ==================== PÁGINA: GERENCIAR CURSOS ====================
    if st.session_state.current_page == "gerenciar_cursos":
        st.markdown("## Gerenciamento de Cursos e Disciplinas")
        
        # Seção: Selecionar Curso Existente
        st.markdown("### Selecionar Curso")
        
        # Buscar todos os cursos disponíveis
        todos_cursos = database.get_all_cursos()
        
        if todos_cursos:
            # Buscar cursos já associados ao professor
            cursos_professor = database.get_professor_courses(st.session_state.user_data['prontuario'])
            cursos_professor_ids = [curso['codigo_curso'] for curso in cursos_professor]
            
            # Filtrar cursos não associados
            cursos_disponiveis = [curso for curso in todos_cursos if curso['codigo_curso'] not in cursos_professor_ids]
            
            if cursos_disponiveis:
                with st.form("select_curso_form"):
                    st.markdown("**Selecione um curso para associar:**")
                    
                    # Criar opções para o selectbox
                    opcoes_cursos = [f"{curso['codigo_curso']} - {curso['nome']}" for curso in cursos_disponiveis]
                    
                    curso_selecionado = st.selectbox(
                        "Cursos Disponíveis",
                        options=opcoes_cursos,
                        index=None,
                        placeholder="Escolha um curso..."
                    )
                    
                    if st.form_submit_button("✅ Associar Curso", use_container_width=True, type="primary"):
                        if curso_selecionado:
                            try:
                                # Extrair código do curso da opção selecionada
                                codigo_curso = curso_selecionado.split(" - ")[0]
                                
                                # Vincular professor ao curso
                                database.create_professor_curso_relationship(
                                    st.session_state.user_data['prontuario'],
                                    codigo_curso
                                )
                                
                                st.success(f"Curso associado com sucesso.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao associar curso: {str(e)}")
                        else:
                            st.error("Selecione um curso!")
            else:
                st.info("Todos os cursos disponíveis já estão associados ao seu perfil.")
        else:
            st.warning("Nenhum curso cadastrado no sistema. Entre em contato com o administrador.")
        
        st.markdown("---")
        st.markdown("### Meus Cursos")
        
        # Buscar cursos do professor
        professor_cursos = database.get_professor_courses(st.session_state.user_data['prontuario'])
        
        if professor_cursos:
            for curso in professor_cursos:
                with st.expander(f"🎓 {curso['codigo_curso']} - {curso['nome']}", expanded=False):
                    st.markdown(f"**Código:** {curso['codigo_curso']}")
                    st.markdown(f"**Nome:** {curso['nome']}")
                    
                    # Botão de ação
                    if st.button("Ver Disciplinas", key=f"view_disciplines_{curso['codigo_curso']}", use_container_width=True):
                        st.session_state[f"show_disciplines_{curso['codigo_curso']}"] = True
                        st.rerun()
                    
                    # Exibir disciplinas se solicitado
                    if st.session_state.get(f"show_disciplines_{curso['codigo_curso']}", False):
                        st.markdown("---")
                        st.markdown("### Disciplinas do Curso")
                        
                        # Buscar disciplinas do curso
                        disciplinas_curso = database.get_curso_disciplines(curso['codigo_curso'])
                        
                        if disciplinas_curso:
                            # Criar DataFrame para exibição
                            df_disciplinas = pd.DataFrame(disciplinas_curso)
                            df_disciplinas = df_disciplinas[['id_disciplina', 'nome', 'carga_horaria']]
                            df_disciplinas.columns = ['Código', 'Nome da Disciplina', 'Carga Horária (h)']
                            
                            # Preencher valores nulos
                            df_disciplinas['Carga Horária (h)'] = df_disciplinas['Carga Horária (h)'].fillna('Não informado')
                            
                            # Exibir tabela
                            st.dataframe(df_disciplinas, use_container_width=True)
                            
                            # Estatísticas
                            total_disciplinas = len(disciplinas_curso)
                            total_horas = sum([disc.get('carga_horaria', 0) for disc in disciplinas_curso if isinstance(disc.get('carga_horaria'), (int, float))])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total de Disciplinas", total_disciplinas)
                            with col2:
                                st.metric("Total de Horas", f"{total_horas}h")
                        else:
                            st.info("Nenhuma disciplina cadastrada para este curso.")
                        
                        # Botão para fechar visualização
                        if st.button("Fechar Disciplinas", key=f"close_disciplines_{curso['codigo_curso']}", use_container_width=True):
                            st.session_state[f"show_disciplines_{curso['codigo_curso']}"] = False
                            st.rerun()
                    
                    # Buscar disciplinas do curso
                    disciplinas = database.get_curso_disciplines(curso['codigo_curso'])
                    
                    st.markdown("---")
                    st.markdown("### Disciplinas")
                    
                    if disciplinas:
                        for disc in disciplinas:
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**{disc['id_disciplina']}** - {disc['nome']}")
                            with col2:
                                st.markdown(f"⏰ {disc['carga_horaria']}h")
                    else:
                        st.info("Nenhuma disciplina cadastrada para este curso.")
                    
                    # Seção: Gerenciar Disciplinas do Curso
                    st.markdown("---")
                    st.markdown("### 📚 Disciplinas do Curso")
                    
                    # Buscar disciplinas já associadas ao curso
                    disciplinas_curso = database.get_curso_disciplines(curso['codigo_curso'])
                    
                    if disciplinas_curso:
                        st.markdown("**Disciplinas já adicionadas ao curso:**")
                        
                        for disc in disciplinas_curso:
                            with st.container():
                                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                                
                                with col1:
                                    st.markdown(f"**{disc['id_disciplina']}** - {disc['nome']}")
                                
                                with col2:
                                    # Campo para editar carga horária
                                    nova_carga_key = f"edit_carga_{curso['codigo_curso']}_{disc['id_disciplina']}"
                                    nova_carga = st.number_input(
                                        "Carga Horária (h)",
                                        min_value=1,
                                        max_value=500,
                                        value=disc.get('carga_horaria', 60) or 60,
                                        key=nova_carga_key,
                                        step=1,
                                        label_visibility="collapsed"
                                    )
                                
                                with col3:
                                    # Botão para atualizar carga horária
                                    if st.button("✏️ Atualizar", key=f"update_{curso['codigo_curso']}_{disc['id_disciplina']}", use_container_width=True):
                                        try:
                                            if hasattr(database, '_get_client'):
                                                client = database._get_client(prefer_service_role=True)
                                                if client:
                                                    client.table("disciplinas").update({
                                                        'carga_horaria': nova_carga
                                                    }).eq('id_disciplina', disc['id_disciplina']).execute()
                                                    st.success(f"Carga horária de {disc['nome']} atualizada para {nova_carga}h!")
                                                    st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao atualizar carga horária: {str(e)}")
                                
                                with col4:
                                    # Botão para remover disciplina do curso
                                    if st.button("🗑️ Remover", key=f"remove_{curso['codigo_curso']}_{disc['id_disciplina']}", use_container_width=True, type="secondary"):
                                        try:
                                            # Remover relacionamento curso-disciplina
                                            if hasattr(database, '_get_client'):
                                                client = database._get_client(prefer_service_role=True)
                                                if client:
                                                    # Buscar o ID do relacionamento
                                                    response = client.table("cursos_disciplina").select("*").eq("curso_fk", curso['codigo_curso']).eq("disciplina_fk", disc['id_disciplina']).execute()
                                                    if response.data:
                                                        rel_id = response.data[0].get('id') if 'id' in response.data[0] else None
                                                        if rel_id:
                                                            client.table("cursos_disciplina").delete().eq('id', rel_id).execute()
                                                        else:
                                                            # Tentar deletar sem ID
                                                            client.table("cursos_disciplina").delete().eq("curso_fk", curso['codigo_curso']).eq("disciplina_fk", disc['id_disciplina']).execute()
                                                    st.success(f"Disciplina {disc['nome']} removida do curso!")
                                                    st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao remover disciplina: {str(e)}")
                                
                                st.markdown("---")
                    else:
                        st.info("Nenhuma disciplina adicionada ao curso ainda.")
                    
                    # Seção: Adicionar novas disciplinas
                    st.markdown("---")
                    st.markdown("### ➕ Adicionar Novas Disciplinas ao Curso")
                    
                    # Buscar todas as disciplinas disponíveis
                    todas_disciplinas = database.get_all_disciplinas()
                    
                    # Buscar disciplinas já associadas ao curso
                    disciplinas_curso_ids = {disc['id_disciplina'] for disc in disciplinas_curso}
                    
                    if todas_disciplinas:
                        # Filtrar apenas disciplinas não adicionadas
                        disciplinas_disponiveis = [d for d in todas_disciplinas if d['id_disciplina'] not in disciplinas_curso_ids]
                        
                        if disciplinas_disponiveis:
                            st.info(f"Selecione as disciplinas que deseja adicionar ao curso e defina a carga horária de cada uma antes de adicionar.")
                            
                            # Usar session_state para controlar seleções
                            form_key = f"add_disc_form_{curso['codigo_curso']}"
                            
                            # Inicializar session_state para este formulário
                            if form_key not in st.session_state:
                                st.session_state[form_key] = {}
                            
                            # Mostrar disciplinas fora do form para permitir edição dinâmica
                            st.markdown("#### Disciplinas Disponíveis")
                            st.markdown("**Selecione as disciplinas e defina a carga horária antes de adicionar:**")
                            
                            # Dividir em colunas para melhor visualização
                            num_cols = 2
                            cols = st.columns(num_cols)
                            
                            # Inicializar session_state para cargas horárias
                            for disciplina in disciplinas_disponiveis:
                                carga_key = f"carga_{curso['codigo_curso']}_{disciplina['id_disciplina']}"
                                if carga_key not in st.session_state:
                                    st.session_state[carga_key] = disciplina.get('carga_horaria', 60) or 60
                            
                            for idx, disciplina in enumerate(disciplinas_disponiveis):
                                col_idx = idx % num_cols
                                with cols[col_idx]:
                                    # Checkbox para selecionar (fora do form para atualização dinâmica)
                                    check_key = f"check_{curso['codigo_curso']}_{disciplina['id_disciplina']}"
                                    # Inicializar no session_state se não existir
                                    if check_key not in st.session_state:
                                        st.session_state[check_key] = False
                                    
                                    selecionada = st.checkbox(
                                        f"{disciplina['id_disciplina']} - {disciplina['nome']}",
                                        key=check_key,
                                        value=st.session_state[check_key]
                                    )
                                    
                                    # Se selecionada, mostrar campo de carga horária
                                    if selecionada:
                                        carga_key = f"carga_{curso['codigo_curso']}_{disciplina['id_disciplina']}"
                                        # Inicializar no session_state se não existir
                                        if carga_key not in st.session_state:
                                            st.session_state[carga_key] = disciplina.get('carga_horaria', 60) or 60
                                        
                                        carga_horaria = st.number_input(
                                            "Carga Horária (h)",
                                            min_value=1,
                                            max_value=500,
                                            value=st.session_state[carga_key],
                                            key=carga_key,
                                            step=1
                                        )
                            
                            st.markdown("---")
                            
                            # Botão para adicionar (fora do form)
                            if st.button("Adicionar Disciplinas Selecionadas", key=f"btn_add_{curso['codigo_curso']}", use_container_width=True, type="primary"):
                                # Coletar disciplinas selecionadas
                                disciplinas_selecionadas = {}
                                
                                for disciplina in disciplinas_disponiveis:
                                    check_key = f"check_{curso['codigo_curso']}_{disciplina['id_disciplina']}"
                                    if st.session_state.get(check_key, False):
                                        carga_key = f"carga_{curso['codigo_curso']}_{disciplina['id_disciplina']}"
                                        carga_horaria = st.session_state.get(carga_key, disciplina.get('carga_horaria', 60) or 60)
                                        
                                        disciplinas_selecionadas[disciplina['id_disciplina']] = {
                                            'nome': disciplina['nome'],
                                            'carga_horaria': carga_horaria,
                                            'disciplina_original': disciplina
                                        }
                                
                                if disciplinas_selecionadas:
                                    sucesso_count = 0
                                    erro_count = 0
                                    
                                    for disc_id, disc_data in disciplinas_selecionadas.items():
                                        try:
                                            # Atualizar carga horária da disciplina se necessário
                                            if disc_data['carga_horaria'] != disc_data['disciplina_original'].get('carga_horaria'):
                                                # Atualizar disciplina no banco
                                                try:
                                                    if hasattr(database, '_get_client'):
                                                        client = database._get_client(prefer_service_role=True)
                                                        if client:
                                                            client.table("disciplinas").update({
                                                                'carga_horaria': disc_data['carga_horaria']
                                                            }).eq('id_disciplina', disc_id).execute()
                                                except Exception as e:
                                                    st.warning(f"Não foi possível atualizar carga horária de {disc_data['nome']}: {str(e)}")
                                            
                                    # Vincular ao curso
                                            if database.create_curso_disciplina_relationship(curso['codigo_curso'], disc_id):
                                                sucesso_count += 1
                                                # Limpar seleção do session_state
                                                check_key = f"check_{curso['codigo_curso']}_{disc_id}"
                                                if check_key in st.session_state:
                                                    st.session_state[check_key] = False
                                            else:
                                                erro_count += 1
                                        except Exception as e:
                                            st.error(f"Erro ao adicionar {disc_data['nome']}: {str(e)}")
                                            erro_count += 1
                                    
                                    if sucesso_count > 0:
                                        st.success(f"{sucesso_count} disciplina(s) adicionada(s) com sucesso!")
                                    if erro_count > 0:
                                        st.error(f"Erro ao adicionar {erro_count} disciplina(s).")
                                    
                                    if sucesso_count > 0:
                                        st.rerun()
                                else:
                                    st.warning("Selecione pelo menos uma disciplina para adicionar!")
                            else:
                                st.info("Todas as disciplinas disponíveis já foram adicionadas ao curso.")
                    else:
                        st.warning("Nenhuma disciplina cadastrada no sistema. Entre em contato com o administrador.")
        else:
            st.info("Você ainda não possui cursos cadastrados.")
        
        st.markdown("---")
    
    # ==================== PÁGINA: HOME (PRINCIPAL) ====================
    elif st.session_state.current_page == "home":
        # Inicializar analyses_data se não existir
        if 'analyses_data' not in st.session_state:
            st.session_state.analyses_data = []
        
        # Título principal
        st.markdown("### Página Principal")
        st.markdown("**Sistema de Análise de Requerimentos Acadêmicos**")
        
        # Buscar cursos do professor (armazenar no session_state para evitar reconsultas)
        if 'professor_courses' not in st.session_state:
            professor_courses = database.get_professor_courses(st.session_state.user_data['prontuario'])
            st.session_state.professor_courses = professor_courses
        else:
            professor_courses = st.session_state.professor_courses
        
        if not professor_courses:
            st.warning("Você não possui cursos cadastrados. Entre em contato com o administrador.")
            st.stop()
        
        # Selecionar automaticamente o primeiro curso (Análise e Desenvolvimento de Sistemas)
        # Como todos os professores estão associados apenas a este curso, usamos o primeiro
        curso_automatico = professor_courses[0]
        course_code = curso_automatico['codigo_curso']
        
        # Atualizar o curso selecionado no session_state
        st.session_state.selected_course = course_code
        
        # Mostrar informações do curso selecionado automaticamente
        curso_info = database.get_curso_by_codigo(course_code)
        if curso_info:
            st.markdown(f"### {curso_info['nome']}")
            st.markdown(f"**Código:** {curso_info['codigo_curso']}")
            st.markdown(f"**Descrição:** {curso_info['descricao_curso']}")
        else:
            st.error(f"Erro: Não foi possível carregar informações do curso {course_code}")
            st.info("Entre em contato com o administrador.")
            st.stop()
        
        st.markdown("---")
        
        # Seção: Análise de Documentos
        st.markdown("### Análise de Documentos")
        st.markdown("**Faça upload dos PDFs (Ementa + Histórico Escolar) e processe a análise com IA**")
        
        # Upload de PDFs
        st.markdown("#### Upload de Ementas")
        st.markdown("""
        <div class="upload-area">
        <p>Arraste e solte seus PDFs aqui ou clique para selecionar</p>
        <p><small>Mínimo: 1 PDF | Máximo: 5 PDFs por lote</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Usar uma key única para o file_uploader baseada em um contador
        uploader_key = f"file_uploader_{course_code}"
        if 'uploader_counter' not in st.session_state:
            st.session_state.uploader_counter = 0
        
        # Criar key única combinando course_code e counter
        unique_uploader_key = f"{uploader_key}_{st.session_state.uploader_counter}"
        
        # Verificar se deve limpar (quando botão limpar for clicado)
        if st.session_state.get('clear_uploads', False):
            st.session_state.uploader_counter += 1
            st.session_state.clear_uploads = False
            unique_uploader_key = f"{uploader_key}_{st.session_state.uploader_counter}"
        
        uploaded_files = st.file_uploader(
            "Selecione os PDFs (Ementa + Histórico Escolar)",
            type=['pdf'],
            accept_multiple_files=True,
            help="Mínimo 1 PDF, máximo 5 PDFs por lote",
            key=unique_uploader_key
        )
        
        # Processar uploads se houver arquivos
        # Usar session_state para persistir ementas_data entre recarregamentos
        ementas_key = f'ementas_data_{course_code}'
        
        # Inicializar ementas_data do session_state se não existir
        if ementas_key not in st.session_state:
            st.session_state[ementas_key] = []
        
        if uploaded_files and len(uploaded_files) > 0:
            # Processar novos arquivos
            ementas_data = process_uploaded_files(uploaded_files, course_code, st.session_state.user_data['prontuario'])
            if ementas_data and len(ementas_data) > 0:
                # Adicionar aos dados existentes ou substituir
                st.session_state[ementas_key] = ementas_data
                st.success(f"{len(ementas_data)} PDF(s) carregado(s) com sucesso.")
            elif ementas_data is None or len(ementas_data) == 0:
                st.warning("Nenhum PDF foi processado com sucesso. Verifique os erros acima.")
        else:
            # Usar dados do session_state se existirem
            ementas_data = st.session_state.get(ementas_key, [])
            if ementas_data and len(ementas_data) > 0:
                st.info(f"{len(ementas_data)} PDF(s) já carregado(s). Clique em 'Processar Análises' para analisar.")
        
        # Botão para processar análises
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("🔍 Processar Análises", use_container_width=True, type="primary"):
                # Buscar ementas_data do session_state
                ementas_data = st.session_state.get(ementas_key, [])
                
                # Debug: mostrar o que está no session_state
                if not ementas_data or len(ementas_data) == 0:
                    # Tentar buscar de uploaded_files também (caso ainda esteja disponível)
                    if uploaded_files and len(uploaded_files) > 0:
                        st.info("Processando arquivos recém-enviados...")
                        ementas_data = process_uploaded_files(uploaded_files, course_code, st.session_state.user_data['prontuario'])
                        if ementas_data and len(ementas_data) > 0:
                            st.session_state[ementas_key] = ementas_data
                
                # Validação: garantir que há PDFs/ementas antes de processar
                if not ementas_data or len(ementas_data) == 0:
                    st.error("❌ Nenhum PDF foi carregado. Por favor, faça upload de pelo menos um PDF antes de processar as análises.")
                    st.stop()
                
                # Verificar se há ementas válidas
                ementas_validas = [e for e in ementas_data if e.get('id_ementa') and e['id_ementa'] is not None]
                if not ementas_validas or len(ementas_validas) == 0:
                    st.error("❌ Nenhuma ementa válida encontrada. Por favor, faça upload de PDFs válidos.")
                    st.stop()
                
                # Verificar se já existem análises para essas ementas e curso
                ementas_com_analise_existente = []
                ementas_sem_analise = []
                
                for ementa_data in ementas_validas:
                    ementa_id = ementa_data.get('id_ementa')
                    analise_existente = database.check_analise_exists_for_ementa_and_curso(ementa_id, course_code)
                    if analise_existente:
                        ementas_com_analise_existente.append({
                            'ementa': ementa_data,
                            'analise': analise_existente
                        })
                    else:
                        ementas_sem_analise.append(ementa_data)
                
                # Se há análises existentes, perguntar ao usuário
                if ementas_com_analise_existente:
                    st.warning(f"⚠️ {len(ementas_com_analise_existente)} PDF(s) já possuem análise para este curso:")
                    for item in ementas_com_analise_existente:
                        ementa = item['ementa']
                        analise = item['analise']
                        st.info(f"📄 **{ementa.get('nome_arquivo', 'Arquivo')}** - Análise ID: {analise.get('analise_id')} | Aluno: {analise.get('nome_aluno', 'N/A')} | Score: {analise.get('score', 'N/A')}/100")
                    
                    # Perguntar se deseja reprocessar
                    col_reprocess1, col_reprocess2 = st.columns(2)
                    with col_reprocess1:
                        reprocessar = st.button("🔄 Reprocessar Todas", use_container_width=True, type="primary")
                    with col_reprocess2:
                        processar_apenas_novas = st.button("✅ Processar Apenas Novas", use_container_width=True)
                    
                    if not reprocessar and not processar_apenas_novas:
                        st.stop()
                    
                    if processar_apenas_novas:
                        # Processar apenas as que não têm análise
                        ementas_para_processar = ementas_sem_analise
                        if not ementas_para_processar:
                            st.info("✅ Todas as ementas já possuem análise. Nada a processar.")
                            st.stop()
                    else:
                        # Reprocessar todas
                        ementas_para_processar = ementas_validas
                else:
                    # Não há análises existentes, processar todas
                    ementas_para_processar = ementas_validas
                    reprocessar = False
                
                # Processar análises
                if ementas_para_processar and len(ementas_para_processar) > 0:
                    with st.spinner("Processando análises com IA..."):
                        all_analyses = []
                        valid_ementas = 0
                        
                        for ementa_data in ementas_para_processar:
                            ementa_id = ementa_data.get('id_ementa')
                            
                            # Se for reprocessar e já existe análise, deletar a antiga primeiro
                            if reprocessar:
                                analise_existente = database.check_analise_exists_for_ementa_and_curso(ementa_id, course_code)
                                if analise_existente:
                                    analise_id_antiga = analise_existente.get('analise_id')
                                    if analise_id_antiga:
                                        try:
                                            database.delete_analise(analise_id_antiga, st.session_state.user_data['prontuario'])
                                            st.info(f"🗑️ Análise anterior (ID: {analise_id_antiga}) removida para reprocessamento.")
                                        except Exception as e:
                                            st.warning(f"⚠️ Não foi possível remover análise anterior: {e}")
                            
                            # Processar análise
                            analyses = process_analysis_with_ai(
                                ementa_id, 
                                course_code, 
                                st.session_state.user_data['prontuario']
                            )
                            if analyses and len(analyses) > 0:
                                all_analyses.extend(analyses)
                                valid_ementas += 1
                        
                        if valid_ementas > 0:
                            st.success(f"✅ Análises processadas com sucesso. {valid_ementas} ementa(s) processada(s).")
                            st.session_state.analyses_data = all_analyses
                            st.rerun()
                        else:
                            st.error("❌ Nenhuma análise foi processada com sucesso.")
                else:
                    st.info("✅ Nenhuma ementa para processar.")
        
        with col_btn2:
            if st.button("🔄 Limpar Uploads", use_container_width=True):
                # Limpar dados de análises e ementas
                if 'analyses_data' in st.session_state:
                    del st.session_state.analyses_data
                # Limpar ementas_data do session_state
                ementas_key = f'ementas_data_{course_code}'
                if ementas_key in st.session_state:
                    del st.session_state[ementas_key]
                # Incrementar contador para resetar o file_uploader
                if 'uploader_counter' in st.session_state:
                    st.session_state.uploader_counter += 1
                st.session_state['clear_uploads'] = True
                
                st.success("Uploads limpos com sucesso!")
                st.rerun()
        
        # Exibir resultado da análise de forma centralizada (apenas se analyses_data existir)
        if 'analyses_data' in st.session_state and st.session_state.analyses_data:
            st.markdown("---")
            if len(st.session_state.analyses_data) == 1:
                # Se há apenas uma análise, exibir de forma destacada
                analise = st.session_state.analyses_data[0]
                
                # Container centralizado para o resultado
                st.markdown("### Análise da IA")
                
                # Card com informações principais
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Aluno:** {analise['nome_aluno']}")
                
                with col2:
                    st.markdown(f"**Score:** {analise['score']}/100")
                
                with col3:
                    status = "Adequado" if analise['adequado'] else "Não Adequado"
                    st.markdown(f"**Status:** {status}")
                
                # Exibir o texto da análise de forma destacada
                st.markdown("---")
                st.markdown("### Análise Detalhada")
                
                # Container com estilo para o texto da IA
                st.markdown("""
                <div style="
                    background-color: #f8f9fa;
                    border: 2px solid #e9ecef;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: left;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                ">
                """, unsafe_allow_html=True)
                
                # Exibir o texto da análise
                st.markdown(analise.get('texto_analise', 'Análise não disponível'))
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Informações adicionais
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Matérias Restantes:** {analise.get('materias_restantes', 'N/A')}")
                
                with col2:
                    st.markdown(f"**ID da Análise:** {analise.get('analise_id', 'N/A')}")
                
                # Criar selected_rows para uma análise única
                selected_rows = [{
                    'ID': analise.get('analise_id'),
                    'Nome': analise.get('nome_aluno'),
                    'Score': analise.get('score'),
                    'Adequado': analise.get('adequado'),
                    'Matérias Restantes': analise.get('materias_restantes'),
                    'id_ementa': analise.get('ementa_fk'),
                    'Análise': analise.get('texto_analise', '')
                }]
                
                # Botões de ação para análise única
                st.markdown("---")
                st.markdown("##### Ações")
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                
                with col_btn1:
                    # Botão de Comentário
                    analise_id_btn = selected_rows[0].get('ID', 0)
                    comentario_key = f"comentario_btn_single_{analise_id_btn}"
                    
                    if st.button("💬 Comentário", use_container_width=True, key=comentario_key):
                        # Inicializar estado de edição de comentário
                        analise_id = selected_rows[0].get('ID', 0)
                        st.session_state[f'editing_comentario_{analise_id}'] = True
                        # Buscar comentário existente
                        analise_completa = database.get_analise_by_id(analise_id)
                        comentario_atual = analise_completa.get('comentario', '') if analise_completa else ''
                        st.session_state[f'comentario_text_{analise_id}'] = comentario_atual
                        st.rerun()
                
                with col_btn2:
                    if st.button("Deletar Análise", use_container_width=True, key="delete_single"):
                        analise_id = selected_rows[0].get('ID', 0)
                        if database.delete_analise(analise_id, st.session_state.user_data['prontuario']):
                            st.success(f"Análise de {selected_rows[0]['Nome']} deletada.")
                            # Remover da lista de análises
                            if 'analyses_data' in st.session_state:
                                st.session_state.analyses_data = [
                                    a for a in st.session_state.analyses_data 
                                    if a.get('analise_id') != analise_id
                                ]
                            st.rerun()
                        else:
                            st.error("Erro ao deletar análise")
                
                with col_btn3:
                    if st.button("Ver Análise Detalhada", use_container_width=True, key="view_single"):
                        row = selected_rows[0]
                        # Manter expander aberto se estiver editando comentário
                        analise_id_exp = row.get('ID')
                        editing_exp_key = f'editing_comentario_{analise_id_exp}'
                        is_editing = st.session_state.get(editing_exp_key, False)
                        with st.expander(f"Análise Detalhada - {row['Nome']}", expanded=True or is_editing):
                            # Buscar dados completos do banco
                            analise_completa = database.get_analise_by_id(row.get('ID'))
                            
                            if analise_completa:
                                # Análise da IA
                                st.markdown("**Análise:**")
                                st.markdown(analise_completa.get('texto_analise', row.get('Análise', '')))
                                st.markdown("---")
                                
                                # Dados estruturados se existirem
                                if analise_completa.get('dados_estruturados_json'):
                                    try:
                                        dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                        
                                        st.markdown("**Dados Estruturados:**")
                                        student_info = dados_estruturados.get('student_info', {})
                                        
                                        col_a, col_b = st.columns(2)
                                        with col_a:
                                            st.markdown(f"**Nome:** {student_info.get('nome', 'N/A')}")
                                            st.markdown(f"**RA:** {student_info.get('ra', 'N/A')}")
                                            st.markdown(f"**CPF:** {student_info.get('cpf', 'N/A')}")
                                        with col_b:
                                            st.markdown(f"**Curso:** {student_info.get('curso', 'N/A')}")
                                            st.markdown(f"**Data Matrícula:** {student_info.get('data_matricula', 'N/A')}")
                                            
                                        with st.expander("🔍 Ver JSON Completo"):
                                            st.json(dados_estruturados)
                                    except:
                                        pass
                            else:
                                st.markdown("**Resposta da IA:**")
                                st.markdown(row.get('Análise', 'Análise não disponível'))
                
                with col_btn4:
                    if st.button("🧹 Limpar Análises", use_container_width=True, key="clear_single"):
                        if 'analyses_data' in st.session_state:
                            del st.session_state.analyses_data
                        st.success("Análises limpas!")
                        st.rerun()
                
                # Exibir análise selecionada com opção de editar comentário
                st.markdown("---")
                st.markdown("##### 👀 Análise Selecionada")
                row = selected_rows[0]
                analise_id = row.get('ID', 0)
                
                # Verificar se está editando comentário para esta análise
                editing_key = f'editing_comentario_{analise_id}'
                comentario_text_key = f'comentario_text_{analise_id}'
                
                # Buscar comentário existente
                analise_completa = database.get_analise_by_id(analise_id)
                comentario_atual = analise_completa.get('comentario', '') if analise_completa else ''
                
                # Manter expander aberto se estiver editando comentário
                analise_id_exp = row.get('ID', 0)
                editing_exp_key = f'editing_comentario_{analise_id_exp}'
                is_editing = st.session_state.get(editing_exp_key, False)
                with st.expander(f"{row['Nome']} - Score: {row['Score']} - {'Adequado' if row['Adequado'] else 'Não Adequado'}", expanded=is_editing):
                    st.markdown("**Resposta Completa da IA:**")
                    st.markdown(row['Análise'])
                    st.markdown("---")
                    st.markdown(f"**Score:** {row['Score']}/100")
                    st.markdown(f"**Matérias Restantes:** {row['Matérias Restantes']}")
                    status_msg = 'Adequado para o curso' if row['Adequado'] else 'Precisa de melhorias'
                    st.markdown(f"**Status:** {status_msg}")
                    
                    # Seção de comentário
                    st.markdown("---")
                    st.markdown("**💬 Comentário do Professor:**")
                    
                    # Se está editando comentário
                    if st.session_state.get(editing_key, False):
                        # Inicializar texto do comentário se não existir
                        if comentario_text_key not in st.session_state:
                            st.session_state[comentario_text_key] = comentario_atual
                        
                        # Textbox para editar comentário
                        novo_comentario = st.text_area(
                            "Digite seu comentário sobre esta análise:",
                            value=st.session_state[comentario_text_key],
                            height=150,
                            key=f"textarea_comentario_single_{analise_id}"
                        )
                        
                        col_save, col_cancel, col_close = st.columns(3)
                        with col_save:
                            if st.button("💾 Salvar Comentário", use_container_width=True, key=f"save_comentario_single_{analise_id}"):
                                # Função para atualizar comentário (com fallback se método não existir)
                                def update_comentario(analise_id, comentario, professor_id):
                                    # Tentar usar o método se existir
                                    if hasattr(database, 'update_analise_comentario'):
                                        return database.update_analise_comentario(analise_id, comentario, professor_id)
                                    
                                    # Fallback: atualizar diretamente usando o cliente Supabase
                                    try:
                                        # Verificar se a análise existe e pertence ao professor
                                        analise_data = database.get_analise_by_id(analise_id)
                                        if not analise_data:
                                            st.error(f"❌ Análise {analise_id} não encontrada")
                                            return False
                                        
                                        if analise_data.get('professor_id') != professor_id:
                                            st.error("❌ Professor não tem permissão para atualizar esta análise")
                                            return False
                                        
                                        # Usar cliente Supabase diretamente
                                        from core.config.supabase_config import supabase_config
                                        client = supabase_config.get_client(use_service_role=True) or supabase_config.get_client()
                                        
                                        if not client:
                                            st.error("❌ Nenhum cliente Supabase disponível!")
                                            return False
                                        
                                        # Atualizar comentário
                                        update_data = {
                                            'comentario': comentario if comentario else None,
                                            'updated_at': datetime.now().isoformat()
                                        }
                                        
                                        response = client.table("analises").update(update_data).eq("analise_id", analise_id).eq("professor_id", professor_id).execute()
                                        
                                        if response.data and len(response.data) > 0:
                                            return True
                                        else:
                                            st.error("⚠️ Nenhum dado retornado na atualização do comentário")
                                            return False
                                    except Exception as e:
                                        error_msg = str(e)
                                        if 'column' in error_msg.lower() and 'comentario' in error_msg.lower():
                                            st.error("❌ Coluna 'comentario' não existe na tabela 'analises'")
                                            st.info("Execute no Supabase SQL Editor: ALTER TABLE analises ADD COLUMN comentario TEXT;")
                                        else:
                                            st.error(f"❌ Erro ao atualizar comentário: {error_msg}")
                                        return False
                                
                                if update_comentario(
                                    analise_id, 
                                    novo_comentario, 
                                    st.session_state.user_data['prontuario']
                                ):
                                    st.success("✅ Comentário salvo com sucesso!")
                                    st.session_state[editing_key] = False
                                    # Atualizar o comentário no session_state para evitar reconsulta
                                    if 'analyses_data' in st.session_state:
                                        for analise in st.session_state.analyses_data:
                                            if analise.get('analise_id') == analise_id:
                                                analise['comentario'] = novo_comentario
                                    # Atualizar análise completa para mostrar novo comentário
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao salvar comentário. Verifique os logs.")
                        
                        with col_cancel:
                            if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_comentario_single_{analise_id}"):
                                st.session_state[editing_key] = False
                                st.session_state[comentario_text_key] = comentario_atual
                                st.rerun()
                        with col_close:
                            if st.button("🚪 Fechar", use_container_width=True, key=f"close_edit_mode_single_{analise_id}"):
                                st.session_state[editing_key] = False
                                st.rerun()
                    else:
                        # Exibir comentário existente ou mensagem
                        if comentario_atual:
                            st.info(f"📝 {comentario_atual}")
                        else:
                            st.info("Nenhum comentário adicionado ainda.")
                        
                        # Botão para editar comentário
                        if st.button("✏️ Editar Comentário", key=f"edit_comentario_single_{analise_id}", use_container_width=True):
                            st.session_state[editing_key] = True
                            st.session_state[comentario_text_key] = comentario_atual
                            st.rerun()
            else:
                # Se há múltiplas análises, exibir tabela resumida
                st.markdown("### Resumo das Análises Processadas")
                
                # Criar DataFrame para a tabela
                df = pd.DataFrame(st.session_state.analyses_data)
                
                # Adicionar coluna de análise e id_ementa se não existir
                if 'ementa_fk' not in df.columns:
                    df['ementa_fk'] = None
                if 'texto_analise' not in df.columns:
                    df['texto_analise'] = ''
                
                # Selecionar colunas e renomear
                df_display = df[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes']].copy()
                df_display.columns = ['ID', 'Nome', 'Score', 'Adequado', 'Matérias Restantes']
                
                # Verificar se há dados para exibir
                if len(df_display) > 0:
                    # Exibir gráfico de barras
                    st.markdown("##### Gráfico de Pontuações")
                    chart_data = df_display[['Nome', 'Score']].set_index('Nome')
                    st.bar_chart(chart_data)
                    
                    # Configurar tabela AgGrid
                    gb = GridOptionsBuilder.from_dataframe(df_display)
                    gb.configure_pagination(paginationAutoPageSize=True)
                    gb.configure_column("Score", header_name="Score", sort="desc")
                    gb.configure_column("Adequado", header_name="Adequado", cellRenderer="agCheckboxCellRenderer")
                    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
                    gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                    
                    grid_options = gb.build()
                    
                    # Exibir tabela interativa
                    st.markdown("##### Tabela de Análises")
                    response = AgGrid(
                        df_display,
                        grid_options=grid_options,
                        enable_enterprise_modules=True,
                        update_mode=GridUpdateMode.SELECTION_CHANGED,
                        theme='streamlit',
                        height=300
                    )
                    
                    # Obter análises selecionadas
                    selected_rows = []
                    if response:
                        raw_selected = response.get('selected_rows', []) if response else []
                        selected_rows_ids = [row.get('ID') for row in raw_selected]
                        
                        # Buscar dados completos das análises selecionadas
                        for analise in st.session_state.analyses_data:
                            if analise.get('analise_id') in selected_rows_ids:
                                selected_rows.append({
                                    'ID': analise.get('analise_id'),
                                    'Nome': analise.get('nome_aluno'),
                                    'Score': analise.get('score'),
                                    'Adequado': analise.get('adequado'),
                                    'Matérias Restantes': analise.get('materias_restantes'),
                                    'id_ementa': analise.get('ementa_fk'),
                                    'Análise': analise.get('texto_analise', '')
                                })
                    else:
                        # Se há apenas uma análise, usar ela automaticamente
                        if len(st.session_state.analyses_data) == 1:
                            analise = st.session_state.analyses_data[0]
                            selected_rows = [{
                                'ID': analise.get('analise_id'),
                                'Nome': analise.get('nome_aluno'),
                                'Score': analise.get('score'),
                                'Adequado': analise.get('adequado'),
                                'Matérias Restantes': analise.get('materias_restantes'),
                                'id_ementa': analise.get('ementa_fk'),
                                'Análise': analise.get('texto_analise', '')
                            }]
                    
                    # Mostrar preview das análises selecionadas
                    if selected_rows and len(selected_rows) > 0:
                        if len(selected_rows) == 1:
                            st.success(f"1 análise pronta para ação: **{selected_rows[0]['Nome']}**")
                        else:
                            nomes = [row['Nome'] for row in selected_rows]
                            st.success(f"{len(selected_rows)} análises selecionadas: {', '.join(nomes)}")
                        
                        # Mostrar comentários das análises selecionadas
                        st.markdown("---")
                        st.markdown("##### 💬 Comentários das Análises Selecionadas")
                        
                        comentarios_exibidos = False
                        for row in selected_rows:
                            analise_id = row.get('ID', 0)
                            analise_completa = database.get_analise_by_id(analise_id)
                            comentario = analise_completa.get('comentario', '') if analise_completa else ''
                            
                            if comentario:
                                comentarios_exibidos = True
                                with st.container():
                                    st.markdown(f"**📝 {row['Nome']}:**")
                                    st.info(comentario)
                                    st.markdown("---")
                        
                        if not comentarios_exibidos:
                            st.info("Nenhum comentário adicionado às análises selecionadas ainda.")
                            st.markdown("---")
                    
                    # Botões de ação
                    st.markdown("##### Ações")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Botão de Comentário
                        if selected_rows and len(selected_rows) > 0:
                            # Usar o ID da primeira análise selecionada
                            analise_id_btn = selected_rows[0].get('ID', 0)
                            comentario_key = f"comentario_btn_{analise_id_btn}"
                            
                            if st.button("💬 Comentário", use_container_width=True, key=comentario_key):
                                # Inicializar estado de edição de comentário para todas as análises selecionadas
                                for row in selected_rows:
                                    analise_id = row.get('ID', 0)
                                    st.session_state[f'editing_comentario_{analise_id}'] = True
                                    # Buscar comentário existente
                                    analise_completa = database.get_analise_by_id(analise_id)
                                    comentario_atual = analise_completa.get('comentario', '') if analise_completa else ''
                                    st.session_state[f'comentario_text_{analise_id}'] = comentario_atual
                                st.rerun()
                        else:
                            if st.button("💬 Comentário", use_container_width=True, disabled=True):
                                pass
                            st.caption("Selecione uma análise")
                    
                    with col2:
                        if st.button("Deletar Análise", use_container_width=True):
                            if selected_rows:
                                for row in selected_rows:
                                    analise_id = row.get('ID', 0)
                                    if database.delete_analise(analise_id, st.session_state.user_data['prontuario']):
                                        st.success(f"Análise de {row['Nome']} deletada.")
                                        # Remover da lista de análises
                                        st.session_state.analyses_data = [
                                            a for a in st.session_state.analyses_data 
                                            if a.get('analise_id') != analise_id
                                        ]
                                        st.rerun()
                                    else:
                                        st.error("Erro ao deletar análise")
                            else:
                                st.info("Selecione uma análise para deletar")
                    
                    with col3:
                        if st.button("Ver Análise Detalhada", use_container_width=True):
                            if selected_rows:
                                for row in selected_rows:
                                    # Manter expander aberto se estiver editando comentário
                                    analise_id_exp = row.get('ID')
                                    editing_exp_key = f'editing_comentario_{analise_id_exp}'
                                    is_editing = st.session_state.get(editing_exp_key, False)
                                    with st.expander(f"Análise Detalhada - {row['Nome']}", expanded=True or is_editing):
                                        # Buscar dados completos do banco
                                        analise_completa = database.get_analise_by_id(row.get('ID'))
                                        
                                        if analise_completa:
                                            # Análise da IA
                                            st.markdown("**Análise:**")
                                            st.markdown(analise_completa.get('texto_analise', row.get('Análise', '')))
                                            st.markdown("---")
                                            
                                            # Dados estruturados se existirem
                                            if analise_completa.get('dados_estruturados_json'):
                                                try:
                                                    dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                                    
                                                    st.markdown("**Dados Estruturados:**")
                                                    student_info = dados_estruturados.get('student_info', {})
                                                    
                                                    col_a, col_b = st.columns(2)
                                                    with col_a:
                                                        st.markdown(f"**Nome:** {student_info.get('nome', 'N/A')}")
                                                        st.markdown(f"**RA:** {student_info.get('ra', 'N/A')}")
                                                        st.markdown(f"**CPF:** {student_info.get('cpf', 'N/A')}")
                                                    with col_b:
                                                        st.markdown(f"**Curso:** {student_info.get('curso', 'N/A')}")
                                                        st.markdown(f"**Data Matrícula:** {student_info.get('data_matricula', 'N/A')}")
                                                        
                                                    with st.expander("🔍 Ver JSON Completo"):
                                                        st.json(dados_estruturados)
                                                except:
                                                    pass
                                        else:
                                            st.markdown("**Resposta da IA:**")
                                            st.markdown(row.get('Análise', 'Análise não disponível'))
                            else:
                                st.info("📝 Nenhuma análise disponível")
                    
                    with col4:
                        if st.button("🧹 Limpar Análises", use_container_width=True):
                            if 'analyses_data' in st.session_state:
                                del st.session_state.analyses_data
                            st.success("Análises limpas!")
                            st.rerun()
                    
                    # Exibir análises selecionadas com opção de editar comentário
                    if selected_rows:
                        st.markdown("##### 👀 Análises Selecionadas")
                        for row in selected_rows:
                            analise_id = row.get('ID', 0)
                            
                            # Verificar se está editando comentário para esta análise
                            editing_key = f'editing_comentario_{analise_id}'
                            comentario_text_key = f'comentario_text_{analise_id}'
                            
                            # Buscar comentário existente
                            analise_completa = database.get_analise_by_id(analise_id)
                            comentario_atual = analise_completa.get('comentario', '') if analise_completa else ''
                            
                            # Manter expander aberto se estiver editando comentário
                            analise_id_exp = row.get('ID', 0)
                            editing_exp_key = f'editing_comentario_{analise_id_exp}'
                            is_editing = st.session_state.get(editing_exp_key, False)
                            with st.expander(f"{row['Nome']} - Score: {row['Score']} - {'Adequado' if row['Adequado'] else 'Não Adequado'}", expanded=is_editing):
                                st.markdown("**Resposta Completa da IA:**")
                                st.markdown(row['Análise'])
                                st.markdown("---")
                                st.markdown(f"**Score:** {row['Score']}/100")
                                st.markdown(f"**Matérias Restantes:** {row['Matérias Restantes']}")
                                status_msg = 'Adequado para o curso' if row['Adequado'] else 'Precisa de melhorias'
                                st.markdown(f"**Status:** {status_msg}")
                                
                                # Seção de comentário
                                st.markdown("---")
                                st.markdown("**💬 Comentário do Professor:**")
                                
                                # Se está editando comentário
                                if st.session_state.get(editing_key, False):
                                    # Inicializar texto do comentário se não existir
                                    if comentario_text_key not in st.session_state:
                                        st.session_state[comentario_text_key] = comentario_atual
                                    
                                    # Textbox para editar comentário
                                    novo_comentario = st.text_area(
                                        "Digite seu comentário sobre esta análise:",
                                        value=st.session_state[comentario_text_key],
                                        height=150,
                                        key=f"textarea_comentario_{analise_id}"
                                    )
                                    
                                    col_save, col_cancel, col_close = st.columns(3)
                                    with col_save:
                                        if st.button("💾 Salvar Comentário", use_container_width=True, key=f"save_comentario_{analise_id}"):
                                            # Função para atualizar comentário (com fallback se método não existir)
                                            def update_comentario(analise_id, comentario, professor_id):
                                                # Tentar usar o método se existir
                                                if hasattr(database, 'update_analise_comentario'):
                                                    return database.update_analise_comentario(analise_id, comentario, professor_id)
                                                
                                                # Fallback: atualizar diretamente usando o cliente Supabase
                                                try:
                                                    # Verificar se a análise existe e pertence ao professor
                                                    analise_data = database.get_analise_by_id(analise_id)
                                                    if not analise_data:
                                                        st.error(f"❌ Análise {analise_id} não encontrada")
                                                        return False
                                                    
                                                    if analise_data.get('professor_id') != professor_id:
                                                        st.error("❌ Professor não tem permissão para atualizar esta análise")
                                                        return False
                                                    
                                                    # Usar cliente Supabase diretamente
                                                    from core.config.supabase_config import supabase_config
                                                    client = supabase_config.get_client(use_service_role=True) or supabase_config.get_client()
                                                    
                                                    if not client:
                                                        st.error("❌ Nenhum cliente Supabase disponível!")
                                                        return False
                                                    
                                                    # Atualizar comentário
                                                    update_data = {
                                                        'comentario': comentario if comentario else None,
                                                        'updated_at': datetime.now().isoformat()
                                                    }
                                                    
                                                    response = client.table("analises").update(update_data).eq("analise_id", analise_id).eq("professor_id", professor_id).execute()
                                                    
                                                    if response.data and len(response.data) > 0:
                                                        return True
                                                    else:
                                                        st.error("⚠️ Nenhum dado retornado na atualização do comentário")
                                                        return False
                                                except Exception as e:
                                                    error_msg = str(e)
                                                    if 'column' in error_msg.lower() and 'comentario' in error_msg.lower():
                                                        st.error("❌ Coluna 'comentario' não existe na tabela 'analises'")
                                                        st.info("Execute no Supabase SQL Editor: ALTER TABLE analises ADD COLUMN comentario TEXT;")
                                                    else:
                                                        st.error(f"❌ Erro ao atualizar comentário: {error_msg}")
                                                    return False
                                            
                                            if update_comentario(
                                                analise_id, 
                                                novo_comentario, 
                                                st.session_state.user_data['prontuario']
                                            ):
                                                st.success("✅ Comentário salvo com sucesso!")
                                                st.session_state[editing_key] = False
                                                # Atualizar o comentário no session_state para evitar reconsulta
                                                if 'analyses_data' in st.session_state:
                                                    for analise in st.session_state.analyses_data:
                                                        if analise.get('analise_id') == analise_id:
                                                            analise['comentario'] = novo_comentario
                                                # Atualizar análise completa para mostrar novo comentário
                                                st.rerun()
                                            else:
                                                st.error("❌ Erro ao salvar comentário. Verifique os logs.")
                                    
                                    with col_cancel:
                                        if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_comentario_{analise_id}"):
                                            st.session_state[editing_key] = False
                                            st.session_state[comentario_text_key] = comentario_atual
                                            st.rerun()
                                    with col_close:
                                        if st.button("🚪 Fechar", use_container_width=True, key=f"close_edit_mode_{analise_id}"):
                                            st.session_state[editing_key] = False
                                            st.rerun()
                                else:
                                    # Exibir comentário existente ou mensagem
                                    if comentario_atual:
                                        st.info(f"📝 {comentario_atual}")
                                    else:
                                        st.info("Nenhum comentário adicionado ainda.")
                                    
                                    # Botão para editar comentário
                                    if st.button("✏️ Editar Comentário", key=f"edit_comentario_{analise_id}", use_container_width=True):
                                        st.session_state[editing_key] = True
                                        st.session_state[comentario_text_key] = comentario_atual
                                        st.rerun()
                else:
                    st.info("Nenhuma análise encontrada para exibir.")
        
        st.markdown("---")
        
        # Seção: Disciplinas do Curso
        st.markdown("#### Disciplinas do Curso")
        disciplinas_curso = database.get_curso_disciplines(course_code)
        
        if disciplinas_curso:
            # Criar DataFrame com as disciplinas
            df_disciplinas = pd.DataFrame(disciplinas_curso)
            
            # Renomear colunas para melhor exibição
            df_disciplinas_display = df_disciplinas[['id_disciplina', 'nome', 'carga_horaria']].copy()
            df_disciplinas_display.columns = ['Código', 'Nome da Disciplina', 'Carga Horária (h)']
            
            # Preencher valores nulos
            df_disciplinas_display['Carga Horária (h)'] = df_disciplinas_display['Carga Horária (h)'].fillna('Não informado')
            
            # Configurar tabela
            gb_disciplinas = GridOptionsBuilder.from_dataframe(df_disciplinas_display)
            gb_disciplinas.configure_pagination(paginationAutoPageSize=True)
            gb_disciplinas.configure_column("Código", header_name="Código", width=120)
            gb_disciplinas.configure_column("Nome da Disciplina", header_name="Nome da Disciplina", flex=1)
            gb_disciplinas.configure_column("Carga Horária (h)", header_name="Carga Horária", width=150)
            gb_disciplinas.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            
            grid_options_disciplinas = gb_disciplinas.build()
            
            # Exibir tabela de disciplinas
            AgGrid(
                df_disciplinas_display,
                grid_options=grid_options_disciplinas,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme='streamlit',
                height=300
            )
            
            # Mostrar estatísticas das disciplinas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Disciplinas", len(disciplinas_curso))
            with col2:
                carga_total = sum(d.get('carga_horaria', 0) for d in disciplinas_curso if d.get('carga_horaria'))
                st.metric("Carga Horária Total", f"{carga_total}h" if carga_total > 0 else "Não informado")
            with col3:
                carga_media = carga_total / len(disciplinas_curso) if len(disciplinas_curso) > 0 and carga_total > 0 else 0
                st.metric("Carga Horária Média", f"{carga_media:.1f}h" if carga_media > 0 else "Não informado")
        else:
            st.info("Nenhuma disciplina cadastrada para este curso.")
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <p><strong>Informação:</strong> Para cadastrar disciplinas para este curso, acesse a seção de administração.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Seção: Dashboard e Histórico completo do curso
        st.markdown("### Dashboard de Análises")
        st.markdown(f"**Curso:** {curso_info['nome']} ({course_code})")
        
        # Buscar todas as análises do curso selecionado feitas pelo professor logado (histórico)
        historico_analyses = database.get_analises_by_curso_and_professor_usando_relacionamento(course_code, st.session_state.user_data['prontuario'])
        
        if historico_analyses:
            # Criar DataFrame com histórico
            df_historico = pd.DataFrame(historico_analyses)
            
            # ==================== DASHBOARD COM GRÁFICOS ====================
            st.markdown("#### Visão Geral do Curso")
            
            # KPIs Principais
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total de Análises", len(historico_analyses))
            
            with col2:
                adequados_historico = len(df_historico[df_historico['adequado'] == True])
                taxa_adequacao = (adequados_historico / len(historico_analyses) * 100) if len(historico_analyses) > 0 else 0
                st.metric("Adequados", f"{adequados_historico} ({taxa_adequacao:.0f}%)")
            
            with col3:
                nao_adequados = len(historico_analyses) - adequados_historico
                st.metric("Não Adequados", nao_adequados)
            
            with col4:
                score_medio_historico = df_historico['score'].mean()
                st.metric("Score Médio", f"{score_medio_historico:.1f}/100")
            
            with col5:
                score_max_historico = df_historico['score'].max()
                st.metric("Score Máximo", f"{score_max_historico}/100")
            
            st.markdown("---")
            
            # Linha 1: Gráficos de Status e Distribuição de Scores
            st.markdown("#### Análises Estatísticas")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Gráfico de Pizza - Status dos Alunos
                st.markdown("##### Status dos Alunos")
                fig_pie = px.pie(
                    values=[adequados_historico, nao_adequados],
                    names=['Adequados', 'Não Adequados'],
                    color_discrete_sequence=['#28a745', '#dc3545'],
                    hole=0.4
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(
                    showlegend=True,
                    height=300,
                    margin=dict(t=30, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Histograma de Distribuição de Scores
                st.markdown("##### Distribuição de Scores")
                fig_hist = px.histogram(
                    df_historico,
                    x='score',
                    nbins=10,
                    color_discrete_sequence=['#007bff']
                )
                fig_hist.update_layout(
                    xaxis_title="Score",
                    yaxis_title="Quantidade",
                    showlegend=False,
                    height=300,
                    margin=dict(t=30, b=40, l=40, r=0)
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col3:
                # Box Plot de Scores
                st.markdown("##### Análise de Scores")
                fig_box = px.box(
                    df_historico,
                    y='score',
                    color_discrete_sequence=['#17a2b8']
                )
                fig_box.update_layout(
                    yaxis_title="Score",
                    showlegend=False,
                    height=300,
                    margin=dict(t=30, b=40, l=40, r=0)
                )
                st.plotly_chart(fig_box, use_container_width=True)
            
            st.markdown("---")
            
            # Linha 2: Gráficos Temporais e Top Alunos
            col1, col2 = st.columns(2)
            
            with col1:
                # Linha Temporal de Scores (se houver data)
                st.markdown("##### Evolução Temporal")
                if 'created_at' in df_historico.columns:
                    # Converter created_at para datetime
                    df_historico['data'] = pd.to_datetime(df_historico['created_at'])
                    df_sorted = df_historico.sort_values('data')
                    
                    fig_line = px.line(
                        df_sorted,
                        x='data',
                        y='score',
                        markers=True,
                        color_discrete_sequence=['#6f42c1']
                    )
                    fig_line.add_hline(
                        y=70,
                        line_dash="dash",
                        line_color="green",
                        annotation_text="Linha de Corte (70)"
                    )
                    fig_line.update_layout(
                        xaxis_title="Data",
                        yaxis_title="Score",
                        showlegend=False,
                        height=350,
                        margin=dict(t=30, b=40, l=40, r=0)
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    # Gráfico de Barras de Scores por Aluno
                    top_10 = df_historico.nlargest(10, 'score')
                    fig_bar = px.bar(
                        top_10,
                        x='nome_aluno',
                        y='score',
                        color='score',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_bar.update_layout(
                        xaxis_title="Aluno",
                        yaxis_title="Score",
                        showlegend=False,
                        height=350,
                        margin=dict(t=30, b=40, l=40, r=0)
                    )
                    fig_bar.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Tabela de Top 10 Melhores Alunos
                st.markdown("##### Top 10 Melhores Scores")
                top_alunos = df_historico.nlargest(10, 'score')[['nome_aluno', 'score', 'adequado']].copy()
                top_alunos['Posição'] = range(1, len(top_alunos) + 1)
                top_alunos['Status'] = top_alunos['adequado'].apply(lambda x: 'Adequado' if x else 'Não Adequado')
                top_alunos = top_alunos[['Posição', 'nome_aluno', 'score', 'Status']]
                top_alunos.columns = ['#', 'Aluno', 'Score', 'Status']
                
                # Colorir scores
                def highlight_score(row):
                    if row['Score'] >= 80:
                        return ['background-color: #d4edda'] * len(row)
                    elif row['Score'] >= 70:
                        return ['background-color: #fff3cd'] * len(row)
                    else:
                        return ['background-color: #f8d7da'] * len(row)
                
                styled_top = top_alunos.style.apply(highlight_score, axis=1)
                st.dataframe(styled_top, use_container_width=True, height=350)
            
            st.markdown("---")
            
            # Estatísticas Detalhadas
            st.markdown("#### Estatísticas Detalhadas")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Score Mínimo", f"{df_historico['score'].min()}/100")
                st.metric("Mediana", f"{df_historico['score'].median():.1f}/100")
            
            with col2:
                desvio_padrao = df_historico['score'].std()
                st.metric("Desvio Padrão", f"{desvio_padrao:.2f}")
                q1 = df_historico['score'].quantile(0.25)
                st.metric("1º Quartil", f"{q1:.1f}/100")
            
            with col3:
                q3 = df_historico['score'].quantile(0.75)
                st.metric("3º Quartil", f"{q3:.1f}/100")
                scores_acima_70 = len(df_historico[df_historico['score'] >= 70])
                st.metric("Scores ≥ 70", f"{scores_acima_70} ({scores_acima_70/len(df_historico)*100:.0f}%)")
            
            with col4:
                scores_abaixo_50 = len(df_historico[df_historico['score'] < 50])
                st.metric("Scores < 50", f"{scores_abaixo_50} ({scores_abaixo_50/len(df_historico)*100:.0f}%)")
                amplitude = df_historico['score'].max() - df_historico['score'].min()
                st.metric("Amplitude", f"{amplitude}")
            
            st.markdown("---")
            
            # Histórico Completo em Tabela
            st.markdown("#### Histórico Completo de Análises")
            
            # Tabela do histórico
            df_tabela_historico = df_historico[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes']].copy()
            df_tabela_historico.columns = ['ID', 'Nome do Aluno', 'Score', 'Adequado', 'Matérias Restantes']
            df_tabela_historico['Status'] = df_tabela_historico['Adequado'].apply(lambda x: 'Adequado' if x else 'Não Adequado')
            df_tabela_historico = df_tabela_historico[['ID', 'Nome do Aluno', 'Score', 'Status', 'Matérias Restantes']]
            
            # Configurar tabela do histórico
            gb_historico = GridOptionsBuilder.from_dataframe(df_tabela_historico)
            gb_historico.configure_pagination(paginationAutoPageSize=True)
            gb_historico.configure_column("Score", header_name="Score", sort="desc")
            gb_historico.configure_column("Status", header_name="Status")
            gb_historico.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb_historico.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            
            grid_options_historico = gb_historico.build()
            
            # Exibir tabela do histórico
            response_historico = AgGrid(
                df_tabela_historico,
                grid_options=grid_options_historico,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme='streamlit',
                height=400
            )
            
            # Seção: Detalhes Automáticos ao Selecionar
            selected_rows = response_historico.get('selected_rows', []) if response_historico else []
            
            if selected_rows and len(selected_rows) == 1:
                # Mostrar detalhes automaticamente quando uma linha é selecionada
                row = selected_rows[0]
                analise_completa = database.get_analise_by_id(row['ID'])
                
                if analise_completa:
                    st.markdown("---")
                    st.markdown(f"### Detalhes da Análise - {row['Nome do Aluno']}")
                    
                    # Cards com informações principais
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Score", f"{row['Score']}/100")
                    with col2:
                        st.metric("Status", "Adequado" if analise_completa['adequado'] else "Não Adequado")
                    with col3:
                        if 'created_at' in analise_completa:
                            from datetime import datetime
                            data = datetime.fromisoformat(analise_completa['created_at'].replace('Z', '+00:00'))
                            st.metric("Data", data.strftime('%d/%m/%Y'))
                    with col4:
                        metodo = "IA" if analise_completa.get('dados_estruturados_json') else "Regex"
                        st.metric("Método", metodo)
                    
                    # Análise da IA
                    with st.expander("Análise Completa", expanded=True):
                        st.markdown(analise_completa['texto_analise'])
                    
                    # Dados Estruturados Extraídos
                    if analise_completa.get('dados_estruturados_json'):
                        try:
                            dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                            
                            with st.expander("Dados Estruturados Extraídos", expanded=True):
                                # Informações do Aluno
                                st.markdown("#### Informações do Aluno")
                                student_info = dados_estruturados.get('student_info', {})
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown(f"**Nome:** {student_info.get('nome', 'N/A')}")
                                    st.markdown(f"**RA:** {student_info.get('ra', 'N/A')}")
                                    st.markdown(f"**CPF:** {student_info.get('cpf', 'N/A')}")
                                with col_b:
                                    st.markdown(f"**Curso:** {student_info.get('curso', 'N/A')}")
                                    st.markdown(f"**Data Matrícula:** {student_info.get('data_matricula', 'N/A')}")
                                    st.markdown(f"**Período Ingresso:** {student_info.get('periodo_ingresso', 'N/A')}")
                                
                                # Informações de Extração
                                extraction_info = dados_estruturados.get('extraction_info', {})
                                if extraction_info:
                                    st.markdown("#### Informações da Extração")
                                    col_c, col_d, col_e = st.columns(3)
                                    with col_c:
                                        st.markdown(f"**Método:** {extraction_info.get('method', 'N/A')}")
                                    with col_d:
                                        confianca = extraction_info.get('confidence', 0)
                                        st.markdown(f"**Confiança:** {confianca:.2%}")
                                    with col_e:
                                        st.markdown(f"**Formato:** {extraction_info.get('detected_format', 'N/A')}")
                                
                                # Disciplinas (se existirem)
                                disciplines = dados_estruturados.get('disciplines', [])
                                if disciplines:
                                    st.markdown("#### Disciplinas Extraídas")
                                    df_disciplines = pd.DataFrame(disciplines)
                                    st.dataframe(df_disciplines, use_container_width=True)
                                
                                # JSON Completo
                                with st.expander("Ver JSON Completo"):
                                    st.json(dados_estruturados)
                                    
                        except Exception as e:
                            st.warning(f"Erro ao processar dados estruturados: {e}")
                    else:
                        st.info("Esta análise foi processada antes da implementação do sistema de extração estruturada")
            
            # Seção: Ações das Análises
            st.markdown("---")
            st.markdown("### Ações das Análises")
            st.markdown("Digite o ID da análise (visível na coluna ID da tabela acima) para visualizar detalhes ou excluir.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Ver Detalhes da Análise")
                analise_id_ver = st.number_input("ID da Análise:", min_value=1, step=1, key="id_ver_detalhes")
                
                if st.button("Buscar Detalhes", use_container_width=True, key="buscar_detalhes_historico"):
                    analise = database.get_analise_by_id(analise_id_ver)
                    
                    if analise:
                        # Manter expander aberto se estiver editando comentário
                        analise_id_exp = analise['analise_id']
                        editing_exp_key = f'editing_comentario_buscar_{analise_id_exp}'
                        is_editing = st.session_state.get(editing_exp_key, False)
                        with st.expander(f"{analise['nome_aluno']} - Score: {analise['score']}/100", expanded=True or is_editing):
                            st.markdown("**Análise:**")
                            st.markdown(analise['texto_analise'])
                            st.markdown("---")
                            
                            # Dados estruturados se existirem
                            if analise.get('dados_estruturados_json'):
                                try:
                                    dados_estruturados = json.loads(analise['dados_estruturados_json'])
                                    st.markdown("**Dados Estruturados:**")
                                    student_info = dados_estruturados.get('student_info', {})
                                    
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        st.markdown(f"**Nome:** {student_info.get('nome', 'N/A')}")
                                        st.markdown(f"**RA:** {student_info.get('ra', 'N/A')}")
                                        st.markdown(f"**CPF:** {student_info.get('cpf', 'N/A')}")
                                    with col_b:
                                        st.markdown(f"**Curso:** {student_info.get('curso', 'N/A')}")
                                        st.markdown(f"**Data:** {student_info.get('data_matricula', 'N/A')}")
                                    
                                    with st.expander("Ver JSON Completo"):
                                        st.json(dados_estruturados)
                                except:
                                    pass
                            
                            # Informações adicionais
                            st.markdown("---")
                            st.markdown("**Informações da Análise:**")
                            st.markdown(f"- **ID:** {analise['analise_id']}")
                            st.markdown(f"- **Status:** {'Adequado' if analise['adequado'] else 'Não Adequado'}")
                            st.markdown(f"- **Matérias Restantes:** {analise.get('materias_restantes', 'N/A')}")
                            st.markdown(f"- **Data:** {analise.get('created_at', 'N/A')}")
                            
                            # Seção de comentário
                            st.markdown("---")
                            st.markdown("**💬 Comentário do Professor:**")
                            
                            analise_id = analise['analise_id']
                            editing_key = f'editing_comentario_buscar_{analise_id}'
                            comentario_text_key = f'comentario_text_buscar_{analise_id}'
                            comentario_atual = analise.get('comentario', '')
                            
                            # Se está editando comentário
                            if st.session_state.get(editing_key, False):
                                # Inicializar texto do comentário se não existir
                                if comentario_text_key not in st.session_state:
                                    st.session_state[comentario_text_key] = comentario_atual
                                
                                # Textbox para editar comentário
                                novo_comentario = st.text_area(
                                    "Digite seu comentário sobre esta análise:",
                                    value=st.session_state[comentario_text_key],
                                    height=150,
                                    key=f"textarea_comentario_buscar_{analise_id}"
                                )
                                
                                col_save, col_cancel, col_close = st.columns(3)
                                with col_save:
                                    if st.button("💾 Salvar Comentário", use_container_width=True, key=f"save_comentario_buscar_{analise_id}"):
                                        # Função para atualizar comentário
                                        def update_comentario(analise_id, comentario, professor_id):
                                            if hasattr(database, 'update_analise_comentario'):
                                                return database.update_analise_comentario(analise_id, comentario, professor_id)
                                            
                                            # Fallback: atualizar diretamente
                                            try:
                                                analise_data = database.get_analise_by_id(analise_id)
                                                if not analise_data or analise_data.get('professor_id') != professor_id:
                                                    return False
                                                
                                                from core.config.supabase_config import supabase_config
                                                client = supabase_config.get_client(use_service_role=True) or supabase_config.get_client()
                                                if not client:
                                                    return False
                                                
                                                update_data = {
                                                    'comentario': comentario if comentario else None,
                                                    'updated_at': datetime.now().isoformat()
                                                }
                                                
                                                response = client.table("analises").update(update_data).eq("analise_id", analise_id).eq("professor_id", professor_id).execute()
                                                return response.data and len(response.data) > 0
                                            except Exception as e:
                                                st.error(f"❌ Erro: {str(e)}")
                                                return False
                                        
                                        if update_comentario(analise_id, novo_comentario, st.session_state.user_data['prontuario']):
                                            st.success("✅ Comentário salvo com sucesso!")
                                            st.session_state[editing_key] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao salvar comentário.")
                                
                                with col_cancel:
                                    if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_comentario_buscar_{analise_id}"):
                                        st.session_state[editing_key] = False
                                        st.session_state[comentario_text_key] = comentario_atual
                                        st.rerun()
                                with col_close:
                                    if st.button("🚪 Fechar", use_container_width=True, key=f"close_edit_buscar_{analise_id}"):
                                        st.session_state[editing_key] = False
                                        st.rerun()
                            else:
                                # Exibir comentário existente ou mensagem
                                if comentario_atual:
                                    st.info(f"📝 {comentario_atual}")
                                else:
                                    st.info("Nenhum comentário adicionado ainda.")
                                
                                # Botão para editar comentário
                                if st.button("✏️ Editar Comentário", key=f"edit_comentario_buscar_{analise_id}", use_container_width=True):
                                    st.session_state[editing_key] = True
                                    st.session_state[comentario_text_key] = comentario_atual
                                    st.rerun()
                    else:
                        st.error(f"Análise com ID {analise_id_ver} não encontrada.")
            
            with col2:
                st.markdown("##### Excluir Análise")
                
                # Inicializar estado de confirmação
                if 'confirmar_exclusao_id' not in st.session_state:
                    st.session_state.confirmar_exclusao_id = None
                
                analise_id_excluir = st.number_input("ID da Análise:", min_value=1, step=1, key="id_excluir")
                
                # Se não está em modo de confirmação
                if st.session_state.confirmar_exclusao_id is None:
                    if st.button("Excluir Análise", use_container_width=True, key="excluir_analise_historico", type="primary"):
                        # Buscar análise para confirmar
                        analise_confirmacao = database.get_analise_by_id(analise_id_excluir)
                        
                        if analise_confirmacao:
                            st.session_state.confirmar_exclusao_id = analise_id_excluir
                            st.session_state.confirmar_exclusao_nome = analise_confirmacao['nome_aluno']
                            st.rerun()
                        else:
                            st.error(f"Análise com ID {analise_id_excluir} não encontrada.")
                
                # Se está em modo de confirmação
                else:
                    st.warning(f"Você está prestes a excluir a análise de **{st.session_state.confirmar_exclusao_nome}**")
                    st.warning(f"**ID: {st.session_state.confirmar_exclusao_id}**")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Confirmar Exclusão", use_container_width=True, key="confirmar_exclusao_btn", type="primary"):
                            if database.delete_analise(st.session_state.confirmar_exclusao_id, st.session_state.user_data['prontuario']):
                                st.success(f"Análise ID {st.session_state.confirmar_exclusao_id} excluída com sucesso.")
                                st.session_state.confirmar_exclusao_id = None
                                st.session_state.confirmar_exclusao_nome = None
                                st.rerun()
                            else:
                                st.error("Erro ao excluir análise. Você pode não ter permissão.")
                                st.session_state.confirmar_exclusao_id = None
                                st.session_state.confirmar_exclusao_nome = None
                    with col_b:
                        if st.button("Cancelar", use_container_width=True, key="cancelar_exclusao_btn"):
                            st.session_state.confirmar_exclusao_id = None
                            st.session_state.confirmar_exclusao_nome = None
                            st.info("Exclusão cancelada.")
                            st.rerun()
            
            st.markdown("---")
            
            # Exibir análises se existirem
            # Inicializar analyses_data se não existir
            if 'analyses_data' not in st.session_state:
                st.session_state.analyses_data = []
            
            # Usar as análises recém-processadas (já filtradas por professor)
            curso_analyses = st.session_state.analyses_data if st.session_state.analyses_data else []
            
            if curso_analyses:
                st.markdown("#### Resultados das Análises")
                st.markdown("---")
                st.markdown("### Estatísticas do Curso")
                
                # Criar DataFrame com todas as análises do curso
                df_curso = pd.DataFrame(curso_analyses)
                
                # Gráfico de pizza por status
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Status dos Alunos")
                    status_counts = df_curso['adequado'].value_counts()
                    
                    # Preparar dados para o gráfico de pizza
                    labels = ['Adequados' if x else 'Não Adequados' for x in status_counts.index]
                    values = status_counts.values
                    colors = ['#28a745', '#dc3545']  # Verde para adequados, vermelho para não adequados
                    
                    # Criar gráfico de pizza
                    import plotly.express as px
                    fig_pie = px.pie(
                        values=values, 
                        names=labels, 
                        color_discrete_sequence=colors,
                        title="Distribuição por Status"
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    st.markdown("##### Distribuição de Scores")
                    
                    # Criar histograma de scores
                    fig_hist = px.histogram(
                        df_curso, 
                        x='score', 
                        nbins=10,
                        title="Distribuição de Pontuações",
                        labels={'score': 'Score', 'count': 'Número de Alunos'}
                    )
                    fig_hist.update_layout(
                        xaxis_title="Score (0-100)",
                        yaxis_title="Número de Alunos"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                # Estatísticas resumidas
                st.markdown("##### Resumo Estatístico")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Alunos", len(curso_analyses))
                
                with col2:
                    adequados = len(df_curso[df_curso['adequado'] == True])
                    st.metric("Adequados", adequados)
                
                with col3:
                    score_medio = df_curso['score'].mean()
                    st.metric("Score Médio", f"{score_medio:.1f}")
                
                with col4:
                    score_max = df_curso['score'].max()
                    st.metric("Score Máximo", score_max)
                
                # Tabela de todos os alunos analisados no curso
                st.markdown("---")
                st.markdown("### Todos os Alunos Analisados no Curso")
                
                # Verificar se há dados para exibir
                if len(df_curso) > 0:
                    # Preparar dados para a tabela
                    df_tabela = df_curso[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes']].copy()
                    df_tabela.columns = ['ID', 'Nome do Aluno', 'Score', 'Adequado', 'Matérias Restantes']
                    df_tabela['Status'] = df_tabela['Adequado'].apply(lambda x: '✅ Adequado' if x else '❌ Não Adequado')
                    df_tabela = df_tabela[['ID', 'Nome do Aluno', 'Score', 'Status', 'Matérias Restantes']]
                    
                    # Configurar tabela
                    gb_curso = GridOptionsBuilder.from_dataframe(df_tabela)
                    gb_curso.configure_pagination(paginationAutoPageSize=True)
                    gb_curso.configure_column("Score", header_name="Score", sort="desc")
                    gb_curso.configure_column("Status", header_name="Status")
                    gb_curso.configure_selection(selection_mode="multiple", use_checkbox=True)
                    gb_curso.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                    
                    grid_options_curso = gb_curso.build()
                    
                    # Exibir tabela
                    response_curso = AgGrid(
                        df_tabela,
                        grid_options=grid_options_curso,
                        enable_enterprise_modules=True,
                        update_mode=GridUpdateMode.SELECTION_CHANGED,
                        theme='streamlit',
                        height=400
                    )
                else:
                    st.info("Nenhum aluno analisado encontrado para este curso.")
                    response_curso = None
                
                # Detalhes automáticos ao selecionar (curso)
                selected_rows_curso = response_curso.get('selected_rows', []) if response_curso else []
                
                if selected_rows_curso and len(selected_rows_curso) == 1:
                    row = selected_rows_curso[0]
                    analise_completa = database.get_analise_by_id(row['ID'])
                    
                    if analise_completa:
                        st.markdown("---")
                        st.markdown(f"### Detalhes da Análise - {row['Nome do Aluno']}")
                        
                        # Cards com informações principais
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Score", f"{row['Score']}/100")
                        with col2:
                            st.metric("Status", "Adequado" if analise_completa['adequado'] else "Não Adequado")
                        with col3:
                            if 'created_at' in analise_completa:
                                from datetime import datetime
                                data = datetime.fromisoformat(analise_completa['created_at'].replace('Z', '+00:00'))
                                st.metric("Data", data.strftime('%d/%m/%Y'))
                        with col4:
                            metodo = "IA" if analise_completa.get('dados_estruturados_json') else "Regex"
                            st.metric("Método", metodo)
                        
                        # Análise da IA
                        with st.expander("Análise Completa", expanded=True):
                            st.markdown(analise_completa['texto_analise'])
                        
                        # Dados Estruturados Extraídos
                        if analise_completa.get('dados_estruturados_json'):
                            try:
                                dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                
                                with st.expander("Dados Estruturados Extraídos", expanded=True):
                                    # Informações do Aluno
                                    st.markdown("#### Informações do Aluno")
                                    student_info = dados_estruturados.get('student_info', {})
                                    
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        st.markdown(f"**Nome:** {student_info.get('nome', 'N/A')}")
                                        st.markdown(f"**RA:** {student_info.get('ra', 'N/A')}")
                                        st.markdown(f"**CPF:** {student_info.get('cpf', 'N/A')}")
                                    with col_b:
                                        st.markdown(f"**Curso:** {student_info.get('curso', 'N/A')}")
                                        st.markdown(f"**Data Matrícula:** {student_info.get('data_matricula', 'N/A')}")
                                        st.markdown(f"**Período Ingresso:** {student_info.get('periodo_ingresso', 'N/A')}")
                                    
                                    # Informações de Extração
                                    extraction_info = dados_estruturados.get('extraction_info', {})
                                    if extraction_info:
                                        st.markdown("#### Informações da Extração")
                                        col_c, col_d, col_e = st.columns(3)
                                        with col_c:
                                            st.markdown(f"**Método:** {extraction_info.get('method', 'N/A')}")
                                        with col_d:
                                            confianca = extraction_info.get('confidence', 0)
                                            st.markdown(f"**Confiança:** {confianca:.2%}")
                                        with col_e:
                                            st.markdown(f"**Formato:** {extraction_info.get('detected_format', 'N/A')}")
                                    
                                    # Disciplinas (se existirem)
                                    disciplines = dados_estruturados.get('disciplines', [])
                                    if disciplines:
                                        st.markdown("#### Disciplinas Extraídas")
                                        df_disciplines = pd.DataFrame(disciplines)
                                        st.dataframe(df_disciplines, use_container_width=True)
                                    
                                    # JSON Completo
                                    with st.expander("Ver JSON Completo"):
                                        st.json(dados_estruturados)
                                        
                            except Exception as e:
                                st.warning(f"Erro ao processar dados estruturados: {e}")
                        else:
                            st.info("Esta análise foi processada antes da implementação do sistema de extração estruturada")
            
            st.markdown("---")
            
            # Seção: Histórico de Análises do Professor (separado das análises recém-processadas)
            if historico_analyses and len(historico_analyses) > 0:
                st.markdown("### Histórico de Análises do Professor")
                st.info(f"Você possui {len(historico_analyses)} análise(s) histórica(s) para este curso.")
                
                # Criar DataFrame com análises históricas
                df_historico_professor = pd.DataFrame(historico_analyses)
                
                # Estatísticas do histórico do professor
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Histórico", len(historico_analyses))
                
                with col2:
                    adequados_historico = len(df_historico_professor[df_historico_professor['adequado'] == True])
                    st.metric("Adequadas", adequados_historico)
                
                with col3:
                    score_medio_historico = df_historico_professor['score'].mean()
                    st.metric("Score Médio", f"{score_medio_historico:.1f}")
                
                with col4:
                    score_max_historico = df_historico_professor['score'].max()
                    st.metric("Score Máximo", score_max_historico)
                
                # Tabela do histórico do professor
                st.markdown("#### Tabela do Histórico")
                df_tabela_historico_prof = df_historico_professor[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes']].copy()
                df_tabela_historico_prof.columns = ['ID', 'Nome do Aluno', 'Score', 'Adequado', 'Matérias Restantes']
                df_tabela_historico_prof['Status'] = df_tabela_historico_prof['Adequado'].apply(lambda x: 'Adequado' if x else 'Não Adequado')
                df_tabela_historico_prof = df_tabela_historico_prof[['ID', 'Nome do Aluno', 'Score', 'Status', 'Matérias Restantes']]
                
                # Configurar tabela do histórico do professor
                gb_historico_prof = GridOptionsBuilder.from_dataframe(df_tabela_historico_prof)
                gb_historico_prof.configure_pagination(paginationAutoPageSize=True)
                gb_historico_prof.configure_column("Score", header_name="Score", sort="desc")
                gb_historico_prof.configure_column("Status", header_name="Status")
                gb_historico_prof.configure_selection(selection_mode="multiple", use_checkbox=True)
                gb_historico_prof.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                
                grid_options_historico_prof = gb_historico_prof.build()
                
                # Exibir tabela do histórico do professor
                response_historico_prof = AgGrid(
                    df_tabela_historico_prof,
                    grid_options=grid_options_historico_prof,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    theme='streamlit',
                    height=300
                )
            
            st.markdown("---")
            
            # Seção: Estatísticas por Curso
            st.markdown("### Estatísticas por Curso")
            estatisticas_cursos = database.get_estatisticas_por_curso_do_professor(st.session_state.user_data['prontuario'])
            
            if estatisticas_cursos:
                # Criar DataFrame com estatísticas
                df_estatisticas = pd.DataFrame(estatisticas_cursos)
                
                # Configurar tabela de estatísticas
                gb_estatisticas = GridOptionsBuilder.from_dataframe(df_estatisticas)
                gb_estatisticas.configure_pagination(paginationAutoPageSize=True)
                gb_estatisticas.configure_column("total_analises", header_name="Total Análises", sort="desc")
                gb_estatisticas.configure_column("media_score", header_name="Média Score", sort="desc")
                gb_estatisticas.configure_column("taxa_adequacao", header_name="Taxa Adequação")
                gb_estatisticas.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                
                grid_options_estatisticas = gb_estatisticas.build()
                
                # Exibir tabela de estatísticas
                AgGrid(
                    df_estatisticas,
                    grid_options=grid_options_estatisticas,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    theme='streamlit',
                    height=300
                )
            else:
                st.info("Nenhuma estatística encontrada. Faça algumas análises para ver as estatísticas por curso.")
            
            st.markdown("---")
            
            # Seção duplicada removida - histórico agora está no topo, sempre visível
            if False:  # Código antigo mantido para referência - NÃO USAR
                pass
            
            if False:
                # Criar DataFrame com histórico
                df_historico = pd.DataFrame(historico_analyses)
            
                # Estatísticas do histórico
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Histórico", len(historico_analyses))
                
                with col2:
                    adequados_historico = len(df_historico[df_historico['adequado'] == True])
                    st.metric("Adequados", adequados_historico)
                
                with col3:
                    score_medio_historico = df_historico['score'].mean()
                    st.metric("Score Médio", f"{score_medio_historico:.1f}")
                
                with col4:
                    score_max_historico = df_historico['score'].max()
                    st.metric("Score Máximo", score_max_historico)
                
                # Tabela do histórico
                df_tabela_historico = df_historico[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes']].copy()
                df_tabela_historico.columns = ['ID', 'Nome do Aluno', 'Score', 'Adequado', 'Matérias Restantes']
                df_tabela_historico['Status'] = df_tabela_historico['Adequado'].apply(lambda x: '✅ Adequado' if x else '❌ Não Adequado')
                df_tabela_historico = df_tabela_historico[['ID', 'Nome do Aluno', 'Score', 'Status', 'Matérias Restantes']]
                
                # Configurar tabela do histórico
                gb_historico = GridOptionsBuilder.from_dataframe(df_tabela_historico)
                gb_historico.configure_pagination(paginationAutoPageSize=True)
                gb_historico.configure_column("Score", header_name="Score", sort="desc")
                gb_historico.configure_column("Status", header_name="Status")
                gb_historico.configure_selection(selection_mode="multiple", use_checkbox=True)
                gb_historico.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                
                grid_options_historico = gb_historico.build()
                
                # Exibir tabela do histórico
                response_historico = AgGrid(
                    df_tabela_historico,
                    grid_options=grid_options_historico,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    theme='streamlit',
                    height=400
                )
                # else removido - código dentro de if False: nunca será executado
                # st.info("Nenhuma análise encontrada no histórico deste curso.")
                
                # st.markdown("---")
            
            # Seção: Detalhes e Ações das Análises (código desabilitado - dentro de if False:)
            # Todo o código abaixo está comentado pois está dentro de um bloco if False:
            # if historico_analyses:
            #     st.markdown("### Detalhes e Ações das Análises")
            #     st.markdown("Selecione uma ou mais análises na tabela acima e escolha uma ação:")
            #     ... (código comentado)
            
            # Seção removida: duplicação com histórico acima
            
            # Usar historico_analyses ao invés de buscar novamente
            # minhas_analises = historico_analyses
            
            if False:  # Desabilitado - código mantido para referência
                # Criar DataFrame com minhas análises
                df_minhas = pd.DataFrame(minhas_analises)
                
                # Estatísticas das minhas análises
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Minhas Análises", len(minhas_analises))
                
                with col2:
                    adequadas_minhas = len(df_minhas[df_minhas['adequado'] == True])
                    st.metric("Adequadas", adequadas_minhas)
                
                with col3:
                    score_medio_minhas = df_minhas['score'].mean()
                    st.metric("Score Médio", f"{score_medio_minhas:.1f}")
                
                with col4:
                    score_max_minhas = df_minhas['score'].max()
                    st.metric("Score Máximo", score_max_minhas)
                
                # Tabela das minhas análises
                df_tabela_minhas = df_minhas[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes', 'created_at']].copy()
                df_tabela_minhas.columns = ['ID', 'Nome do Aluno', 'Score', 'Adequado', 'Matérias Restantes', 'Data']
                df_tabela_minhas['Status'] = df_tabela_minhas['Adequado'].apply(lambda x: '✅ Adequado' if x else '❌ Não Adequado')
                df_tabela_minhas = df_tabela_minhas[['ID', 'Nome do Aluno', 'Score', 'Status', 'Matérias Restantes', 'Data']]
                
                # Configurar tabela das minhas análises
                gb_minhas = GridOptionsBuilder.from_dataframe(df_tabela_minhas)
                gb_minhas.configure_pagination(paginationAutoPageSize=True)
                gb_minhas.configure_column("Score", header_name="Score", sort="desc")
                gb_minhas.configure_column("Status", header_name="Status")
                gb_minhas.configure_column("Data", header_name="Data", sort="desc")
                gb_minhas.configure_selection(selection_mode="multiple", use_checkbox=True)
                gb_minhas.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                
                grid_options_minhas = gb_minhas.build()
                
                # Exibir tabela das minhas análises
                response_minhas = AgGrid(
                    df_tabela_minhas,
                    grid_options=grid_options_minhas,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    theme='streamlit',
                    height=300
                )
                
                # Botões de ação para minhas análises
                st.markdown("##### ⚙️ Ações das Minhas Análises")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                        if st.button("Ver Análise Detalhada", use_container_width=True):
                            selected_rows = response_minhas.get('selected_rows', []) if response_minhas else []
                            if selected_rows:
                                for row in selected_rows:
                                    # Buscar análise completa
                                    analise_completa = database.get_analise_by_id(row['ID'])
                                    if analise_completa:
                                        st.markdown(f"##### Análise Detalhada - {row['Nome do Aluno']}")
                                        st.markdown("**Resposta da IA:**")
                                        st.markdown(analise_completa['texto_analise'])
                                        st.markdown("---")
                                        st.markdown(f"**Score:** {row['Score']}/100")
                                        st.markdown(f"**Matérias Restantes:** {row['Matérias Restantes']}")
                                        st.markdown(f"**Status:** {'Adequado para o curso' if row['Adequado'] else 'Precisa de melhorias'}")
                                        st.markdown(f"**Data:** {row['Data']}")
                                        
                                        # Seção de comentário
                                        st.markdown("---")
                                        st.markdown("**💬 Comentário do Professor:**")
                                        
                                        analise_id = row['ID']
                                        editing_key = f'editing_comentario_minhas_{analise_id}'
                                        comentario_text_key = f'comentario_text_minhas_{analise_id}'
                                        comentario_atual = analise_completa.get('comentario', '')
                                        
                                        # Se está editando comentário
                                        if st.session_state.get(editing_key, False):
                                            # Inicializar texto do comentário se não existir
                                            if comentario_text_key not in st.session_state:
                                                st.session_state[comentario_text_key] = comentario_atual
                                            
                                            # Textbox para editar comentário
                                            novo_comentario = st.text_area(
                                                "Digite seu comentário sobre esta análise:",
                                                value=st.session_state[comentario_text_key],
                                                height=150,
                                                key=f"textarea_comentario_minhas_{analise_id}"
                                            )
                                            
                                            col_save, col_cancel, col_close = st.columns(3)
                                            with col_save:
                                                if st.button("💾 Salvar Comentário", use_container_width=True, key=f"save_comentario_minhas_{analise_id}"):
                                                    # Função para atualizar comentário
                                                    def update_comentario(analise_id, comentario, professor_id):
                                                        if hasattr(database, 'update_analise_comentario'):
                                                            return database.update_analise_comentario(analise_id, comentario, professor_id)
                                                        
                                                        # Fallback: atualizar diretamente
                                                        try:
                                                            analise_data = database.get_analise_by_id(analise_id)
                                                            if not analise_data or analise_data.get('professor_id') != professor_id:
                                                                return False
                                                            
                                                            from core.config.supabase_config import supabase_config
                                                            client = supabase_config.get_client(use_service_role=True) or supabase_config.get_client()
                                                            if not client:
                                                                return False
                                                            
                                                            update_data = {
                                                                'comentario': comentario if comentario else None,
                                                                'updated_at': datetime.now().isoformat()
                                                            }
                                                            
                                                            response = client.table("analises").update(update_data).eq("analise_id", analise_id).eq("professor_id", professor_id).execute()
                                                            return response.data and len(response.data) > 0
                                                        except Exception as e:
                                                            st.error(f"❌ Erro: {str(e)}")
                                                            return False
                                                    
                                                    if update_comentario(analise_id, novo_comentario, st.session_state.user_data['prontuario']):
                                                        st.success("✅ Comentário salvo com sucesso!")
                                                        st.session_state[editing_key] = False
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ Erro ao salvar comentário.")
                                            
                                            with col_cancel:
                                                if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_comentario_minhas_{analise_id}"):
                                                    st.session_state[editing_key] = False
                                                    st.session_state[comentario_text_key] = comentario_atual
                                                    st.rerun()
                                            with col_close:
                                                if st.button("🚪 Fechar", use_container_width=True, key=f"close_edit_minhas_{analise_id}"):
                                                    st.session_state[editing_key] = False
                                                    st.rerun()
                                        else:
                                            # Exibir comentário existente ou mensagem
                                            if comentario_atual:
                                                st.info(f"📝 {comentario_atual}")
                                            else:
                                                st.info("Nenhum comentário adicionado ainda.")
                                            
                                            # Botão para editar comentário
                                            if st.button("✏️ Editar Comentário", key=f"edit_comentario_minhas_{analise_id}", use_container_width=True):
                                                st.session_state[editing_key] = True
                                                st.session_state[comentario_text_key] = comentario_atual
                                                st.rerun()
                            else:
                                st.info("Selecione uma análise para ver detalhes")
                
                with col2:
                    if st.button("Deletar Análise", use_container_width=True):
                        selected_rows = response_minhas.get('selected_rows', []) if response_minhas else []
                        if selected_rows:
                            for row in selected_rows:
                                analise_id = row['ID']
                                if database.delete_analise(analise_id, st.session_state.user_data['prontuario']):
                                    st.success(f"Análise de {row['Nome do Aluno']} deletada.")
                                    st.rerun()
                                else:
                                    st.error("Erro ao deletar análise")
                        else:
                            st.info("Selecione uma análise para deletar")
                
                with col3:
                    if st.button("Estatísticas Detalhadas", use_container_width=True):
                        st.markdown("##### Estatísticas Detalhadas das Minhas Análises")
                        
                        # Gráfico de distribuição de scores
                        fig_hist_minhas = px.histogram(
                            df_minhas, 
                            x='score', 
                            nbins=10,
                            title="Distribuição de Pontuações - Minhas Análises",
                            labels={'score': 'Score', 'count': 'Número de Análises'}
                        )
                        fig_hist_minhas.update_layout(
                            xaxis_title="Score (0-100)",
                            yaxis_title="Número de Análises"
                        )
                        st.plotly_chart(fig_hist_minhas, use_container_width=True)
                        
                        # Gráfico de pizza por status
                        status_counts_minhas = df_minhas['adequado'].value_counts()
                        labels_minhas = ['Adequados' if x else 'Não Adequados' for x in status_counts_minhas.index]
                        values_minhas = status_counts_minhas.values
                        colors_minhas = ['#28a745', '#dc3545']
                        
                        fig_pie_minhas = px.pie(
                            values=values_minhas, 
                            names=labels_minhas, 
                            color_discrete_sequence=colors_minhas,
                            title="Distribuição por Status - Minhas Análises"
                        )
                        fig_pie_minhas.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie_minhas, use_container_width=True)
                
                # Exibir resultado da análise de forma centralizada (apenas se analyses_data existir)
                if 'analyses_data' in st.session_state and st.session_state.analyses_data:
                    if len(st.session_state.analyses_data) == 1:
                        # Se há apenas uma análise, exibir de forma destacada
                        analise = st.session_state.analyses_data[0]
                        
                        # Container centralizado para o resultado
                        st.markdown("---")
                        st.markdown("### Análise da IA")
                        
                        # Card com informações principais
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.markdown(f"**Aluno:** {analise['nome_aluno']}")
                        
                        with col2:
                            st.markdown(f"**Score:** {analise['score']}/100")
                        
                        with col3:
                            status = "Adequado" if analise['adequado'] else "Não Adequado"
                            st.markdown(f"**Status:** {status}")
                        
                        # Exibir o texto da análise de forma destacada
                        st.markdown("---")
                        st.markdown("### Análise Detalhada")
                        
                        # Container com estilo para o texto da IA
                        st.markdown("""
                        <div style="
                            background-color: #f8f9fa;
                            border: 2px solid #e9ecef;
                            border-radius: 10px;
                            padding: 20px;
                            margin: 20px 0;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            text-align: left;
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            line-height: 1.6;
                        ">
                        """, unsafe_allow_html=True)
                        
                        # Exibir o texto da análise
                        st.markdown(analise['texto_analise'])
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Informações adicionais
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Matérias Restantes:** {analise['materias_restantes']}")
                        
                        with col2:
                            st.markdown(f"**ID da Análise:** {analise['analise_id']}")
                
                # Criar DataFrame para a tabela (simplificada)
                df = pd.DataFrame(st.session_state.analyses_data)
                
                # Adicionar coluna de análise e id_ementa se não existir
                if 'ementa_fk' not in df.columns:
                    df['ementa_fk'] = None
                if 'texto_analise' not in df.columns:
                    df['texto_analise'] = ''
                
                # Selecionar colunas e renomear
                df_display = df[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes']].copy()
                df_display.columns = ['ID', 'Nome', 'Score', 'Adequado', 'Matérias Restantes']
                
                # Criar cópia completa com dados extras para os botões
                df_full = df[['analise_id', 'nome_aluno', 'score', 'adequado', 'materias_restantes', 'ementa_fk', 'texto_analise']].copy()
                df_full.columns = ['ID', 'Nome', 'Score', 'Adequado', 'Matérias Restantes', 'id_ementa', 'Análise']
                df = df_display  # Usar display simplificado para visualização
                
                # Inicializar response e selected_rows
                response = None
                selected_rows = []
                
                # Se há múltiplas análises, exibir tabela resumida
                if len(st.session_state.analyses_data) > 1:
                    st.markdown("---")
                    st.markdown("### Resumo das Análises")
                    
                    # Verificar se há dados para exibir
                    if len(df) > 0:
                        # Exibir gráfico de barras
                        st.markdown("##### Gráfico de Pontuações")
                        chart_data = df[['Nome', 'Score']].set_index('Nome')
                        st.bar_chart(chart_data)
                        
                        # Configurar tabela AgGrid
                        gb = GridOptionsBuilder.from_dataframe(df)
                        gb.configure_pagination(paginationAutoPageSize=True)
                        gb.configure_column("Score", header_name="Score", sort="desc")
                        gb.configure_column("Adequado", header_name="Adequado", cellRenderer="agCheckboxCellRenderer")
                        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
                        gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                        
                        grid_options = gb.build()
                        
                        # Exibir tabela interativa
                        st.markdown("##### Tabela de Análises")
                        response = AgGrid(
                            df,
                            grid_options=grid_options,
                            enable_enterprise_modules=True,
                            update_mode=GridUpdateMode.SELECTION_CHANGED,
                            theme='streamlit',
                            height=300
                        )
                    else:
                        st.info("Nenhuma análise encontrada para exibir.")
                        response = None
                
                # Obter análises selecionadas
                if response:
                    raw_selected = response.get('selected_rows', []) if response else []
                    
                    # Debug temporário
                    with st.expander("🔍 Debug - Seleções", expanded=False):
                        st.write(f"Linhas retornadas pelo AgGrid: {len(raw_selected)}")
                        if raw_selected:
                            st.write("Primeira linha selecionada:")
                            st.json(raw_selected[0])
                    
                    selected_rows_ids = [row.get('ID') for row in raw_selected]
                    
                    # Buscar dados completos das análises selecionadas
                    selected_rows = []
                    for analise in st.session_state.analyses_data:
                        if analise.get('analise_id') in selected_rows_ids:
                            selected_rows.append({
                                'ID': analise.get('analise_id'),
                                'Nome': analise.get('nome_aluno'),
                                'Score': analise.get('score'),
                                'Adequado': analise.get('adequado'),
                                'Matérias Restantes': analise.get('materias_restantes'),
                                'id_ementa': analise.get('ementa_fk'),
                                'Análise': analise.get('texto_analise', '')
                            })
                else:
                    # Se há apenas uma análise, usar ela automaticamente
                    if len(st.session_state.analyses_data) == 1:
                        analise = st.session_state.analyses_data[0]
                        selected_rows = [{
                            'ID': analise.get('analise_id'),
                            'Nome': analise.get('nome_aluno'),
                            'Score': analise.get('score'),
                            'Adequado': analise.get('adequado'),
                            'Matérias Restantes': analise.get('materias_restantes'),
                            'id_ementa': analise.get('ementa_fk'),
                            'Análise': analise.get('texto_analise', '')
                        }]
                    else:
                        selected_rows = []
                
                # Mostrar preview das análises selecionadas
                if selected_rows and len(selected_rows) > 0:
                    if len(selected_rows) == 1:
                        st.success(f"1 análise pronta para ação: **{selected_rows[0]['Nome']}**")
                    else:
                        nomes = [row['Nome'] for row in selected_rows]
                        st.success(f"{len(selected_rows)} análises selecionadas: {', '.join(nomes)}")
                    
                    # Mostrar comentários das análises selecionadas
                    st.markdown("---")
                    st.markdown("##### 💬 Comentários das Análises Selecionadas")
                    
                    comentarios_exibidos = False
                    for row in selected_rows:
                        analise_id = row.get('ID', 0)
                        analise_completa = database.get_analise_by_id(analise_id)
                        comentario = analise_completa.get('comentario', '') if analise_completa else ''
                        
                        if comentario:
                            comentarios_exibidos = True
                            with st.container():
                                st.markdown(f"**📝 {row['Nome']}:**")
                                st.info(comentario)
                                st.markdown("---")
                    
                    if not comentarios_exibidos:
                        st.info("Nenhum comentário adicionado às análises selecionadas ainda.")
                        st.markdown("---")
                
                # Botões de ação
                st.markdown("##### Ações")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Botão de Comentário
                    if selected_rows and len(selected_rows) > 0:
                        # Usar o ID da primeira análise selecionada
                        analise_id_btn = selected_rows[0].get('ID', 0)
                        comentario_key = f"comentario_btn_{analise_id_btn}"
                        
                        if st.button("💬 Comentário", use_container_width=True, key=comentario_key):
                            # Inicializar estado de edição de comentário para todas as análises selecionadas
                            for row in selected_rows:
                                analise_id = row.get('ID', 0)
                                st.session_state[f'editing_comentario_{analise_id}'] = True
                                # Buscar comentário existente
                                analise_completa = database.get_analise_by_id(analise_id)
                                comentario_atual = analise_completa.get('comentario', '') if analise_completa else ''
                                st.session_state[f'comentario_text_{analise_id}'] = comentario_atual
                            st.rerun()
                    else:
                        if st.button("💬 Comentário", use_container_width=True, disabled=True):
                            pass
                        st.caption("Selecione uma análise")
                
                with col2:
                    if st.button("Deletar Análise", use_container_width=True):
                        if selected_rows:
                            for row in selected_rows:
                                analise_id = row.get('ID', 0)
                                if database.delete_analise(analise_id, st.session_state.user_data['prontuario']):
                                    st.success(f"Análise de {row['Nome']} deletada.")
                                    # Remover da lista de análises
                                    st.session_state.analyses_data = [
                                        a for a in st.session_state.analyses_data 
                                        if a.get('analise_id') != analise_id
                                    ]
                                    st.rerun()
                                else:
                                    st.error("Erro ao deletar análise")
                        else:
                            st.info("Selecione uma análise para deletar")
                
                with col3:
                    if st.button("Ver Análise Detalhada", use_container_width=True):
                        if selected_rows:
                            for row in selected_rows:
                                # Manter expander aberto se estiver editando comentário
                                analise_id_exp = row.get('ID')
                                editing_exp_key = f'editing_comentario_{analise_id_exp}'
                                is_editing = st.session_state.get(editing_exp_key, False)
                                with st.expander(f"Análise Detalhada - {row['Nome']}", expanded=True or is_editing):
                                    # Buscar dados completos do banco
                                    analise_completa = database.get_analise_by_id(row.get('ID'))
                                    
                                    if analise_completa:
                                        # Análise da IA
                                        st.markdown("**Análise:**")
                                        st.markdown(analise_completa.get('texto_analise', row.get('Análise', '')))
                                        st.markdown("---")
                                        
                                        # Dados estruturados se existirem
                                        if analise_completa.get('dados_estruturados_json'):
                                            try:
                                                dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                                
                                                st.markdown("**Dados Estruturados:**")
                                                student_info = dados_estruturados.get('student_info', {})
                                                
                                                col_a, col_b = st.columns(2)
                                                with col_a:
                                                    st.markdown(f"**Nome:** {student_info.get('nome', 'N/A')}")
                                                    st.markdown(f"**RA:** {student_info.get('ra', 'N/A')}")
                                                    st.markdown(f"**CPF:** {student_info.get('cpf', 'N/A')}")
                                                with col_b:
                                                    st.markdown(f"**Curso:** {student_info.get('curso', 'N/A')}")
                                                    st.markdown(f"**Data Matrícula:** {student_info.get('data_matricula', 'N/A')}")
                                                    
                                                with st.expander("🔍 Ver JSON Completo"):
                                                    st.json(dados_estruturados)
                                            except:
                                                pass
                                    else:
                                        st.markdown("**Resposta da IA:**")
                                        st.markdown(row.get('Análise', 'Análise não disponível'))
                        else:
                            st.info("📝 Nenhuma análise disponível")
                
                with col4:
                    if st.button("🧹 Limpar Análises", use_container_width=True):
                        if 'analyses_data' in st.session_state:
                            del st.session_state.analyses_data
                        st.success("Análises limpas!")
                        st.rerun()
                
                # Exibir análises selecionadas
                if selected_rows:
                    st.markdown("##### 👀 Análises Selecionadas")
                    for row in selected_rows:
                            analise_id = row.get('ID', 0)
                            
                            # Verificar se está editando comentário para esta análise
                            editing_key = f'editing_comentario_{analise_id}'
                            comentario_text_key = f'comentario_text_{analise_id}'
                            
                            # Buscar comentário existente
                            analise_completa = database.get_analise_by_id(analise_id)
                            comentario_atual = analise_completa.get('comentario', '') if analise_completa else ''
                            
                            # Manter expander aberto se estiver editando comentário
                            analise_id_exp = row.get('ID', 0)
                            editing_exp_key = f'editing_comentario_{analise_id_exp}'
                            is_editing = st.session_state.get(editing_exp_key, False)
                            with st.expander(f"{row['Nome']} - Score: {row['Score']} - {'Adequado' if row['Adequado'] else 'Não Adequado'}", expanded=is_editing):
                                st.markdown("**Resposta Completa da IA:**")
                                st.markdown(row['Análise'])
                                st.markdown("---")
                                st.markdown(f"**Score:** {row['Score']}/100")
                                st.markdown(f"**Matérias Restantes:** {row['Matérias Restantes']}")
                                status_msg = 'Adequado para o curso' if row['Adequado'] else 'Precisa de melhorias'
                                st.markdown(f"**Status:** {status_msg}")
                                
                                # Seção de comentário
                                st.markdown("---")
                                st.markdown("**💬 Comentário do Professor:**")
                                
                                # Se está editando comentário
                                if st.session_state.get(editing_key, False):
                                    # Inicializar texto do comentário se não existir
                                    if comentario_text_key not in st.session_state:
                                        st.session_state[comentario_text_key] = comentario_atual
                                    
                                    # Textbox para editar comentário
                                    novo_comentario = st.text_area(
                                        "Digite seu comentário sobre esta análise:",
                                        value=st.session_state[comentario_text_key],
                                        height=150,
                                        key=f"textarea_comentario_{analise_id}"
                                    )
                                    
                                    col_save, col_cancel, col_close = st.columns(3)
                                    with col_save:
                                        if st.button("💾 Salvar Comentário", use_container_width=True, key=f"save_comentario_{analise_id}"):
                                            # Função para atualizar comentário (com fallback se método não existir)
                                            def update_comentario(analise_id, comentario, professor_id):
                                                # Tentar usar o método se existir
                                                if hasattr(database, 'update_analise_comentario'):
                                                    return database.update_analise_comentario(analise_id, comentario, professor_id)
                                                
                                                # Fallback: atualizar diretamente usando o cliente Supabase
                                                try:
                                                    # Verificar se a análise existe e pertence ao professor
                                                    analise_data = database.get_analise_by_id(analise_id)
                                                    if not analise_data:
                                                        st.error(f"❌ Análise {analise_id} não encontrada")
                                                        return False
                                                    
                                                    if analise_data.get('professor_id') != professor_id:
                                                        st.error("❌ Professor não tem permissão para atualizar esta análise")
                                                        return False
                                                    
                                                    # Usar cliente Supabase diretamente
                                                    from core.config.supabase_config import supabase_config
                                                    client = supabase_config.get_client(use_service_role=True) or supabase_config.get_client()
                                                    
                                                    if not client:
                                                        st.error("❌ Nenhum cliente Supabase disponível!")
                                                        return False
                                                    
                                                    # Atualizar comentário
                                                    update_data = {
                                                        'comentario': comentario if comentario else None,
                                                        'updated_at': datetime.now().isoformat()
                                                    }
                                                    
                                                    response = client.table("analises").update(update_data).eq("analise_id", analise_id).eq("professor_id", professor_id).execute()
                                                    
                                                    if response.data and len(response.data) > 0:
                                                        return True
                                                    else:
                                                        st.error("⚠️ Nenhum dado retornado na atualização do comentário")
                                                        return False
                                                except Exception as e:
                                                    error_msg = str(e)
                                                    if 'column' in error_msg.lower() and 'comentario' in error_msg.lower():
                                                        st.error("❌ Coluna 'comentario' não existe na tabela 'analises'")
                                                        st.info("Execute no Supabase SQL Editor: ALTER TABLE analises ADD COLUMN comentario TEXT;")
                                                    else:
                                                        st.error(f"❌ Erro ao atualizar comentário: {error_msg}")
                                                    return False
                                            
                                            if update_comentario(
                                                analise_id, 
                                                novo_comentario, 
                                                st.session_state.user_data['prontuario']
                                            ):
                                                st.success("✅ Comentário salvo com sucesso!")
                                                st.session_state[editing_key] = False
                                                # Atualizar o comentário no session_state para evitar reconsulta
                                                if 'analyses_data' in st.session_state:
                                                    for analise in st.session_state.analyses_data:
                                                        if analise.get('analise_id') == analise_id:
                                                            analise['comentario'] = novo_comentario
                                                # Atualizar análise completa para mostrar novo comentário
                                                st.rerun()
                                            else:
                                                st.error("❌ Erro ao salvar comentário. Verifique os logs.")
                                    
                                    with col_cancel:
                                        if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_comentario_{analise_id}"):
                                            st.session_state[editing_key] = False
                                            st.session_state[comentario_text_key] = comentario_atual
                                            st.rerun()
                                    with col_close:
                                        if st.button("🚪 Fechar", use_container_width=True, key=f"close_edit_mode_{analise_id}"):
                                            st.session_state[editing_key] = False
                                            st.rerun()
                                else:
                                    # Exibir comentário existente ou mensagem
                                    if comentario_atual:
                                        st.info(f"📝 {comentario_atual}")
                                    else:
                                        st.info("Nenhum comentário adicionado ainda.")
                                    
                                    # Botão para editar comentário
                                    if st.button("✏️ Editar Comentário", key=f"edit_comentario_{analise_id}", use_container_width=True):
                                        st.session_state[editing_key] = True
                                        st.session_state[comentario_text_key] = comentario_atual
                                        st.rerun()