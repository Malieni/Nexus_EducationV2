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
database = SupabaseDatabase()
# Para operações administrativas (cadastro), usar service role
from core.config.supabase_config import supabase_config
database.client = supabase_config.get_client(use_service_role=True)

# Inicializa o serviço do Google Drive
drive_service = GoogleDriveService()

# Configura a página do Streamlit
st.set_page_config(
    layout="wide", 
    page_title="Nexus Education", 
    page_icon="🎓",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .course-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .course-card h4 {
        margin: 0 0 0.5rem 0;
        color: #2c3e50;
    }
    .course-card p {
        margin: 0;
        color: #7f8c8d;
    }
    .discipline-item {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.25rem 0;
    }
    .discipline-item:hover {
        background-color: #f8f9fa;
    }
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f9f9f9;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Função para verificar se o usuário está logado
def is_logged_in():
    return 'user_logged_in' in st.session_state and st.session_state.user_logged_in

# Função para lidar com erros de token do Google Drive
def handle_drive_token_error():
    """Lida com erros de token do Google Drive"""
    st.error("🔑 Token do Google Drive expirado!")
    
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
        if st.button("🔄 Renovar Token", type="primary"):
            try:
                # Tentar renovar o token
                if drive_service.authenticate():
                    st.success("✅ Token renovado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Falha ao renovar token. Tente a opção manual.")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
        
        if st.button("🚫 Processar Sem Drive"):
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

# Função para validar email
def is_valid_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

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
        
        # Criar professor - remover cursos dos dados do professor
        professor_info = {
            'prontuario': professor_data['prontuario'],
            'nome': professor_data['nome'],
            'email_educacional': professor_data['email_educacional'],
            'senha': professor_data['senha']
        }
        
        professor = Professor(**professor_info)
        database.create_professor(convert_datetime_for_json(professor.model_dump()))
        
        # Cadastrar cursos do professor
        for curso_data in professor_data.get('cursos', []):
            # Verificar se curso já existe
            existing_curso = database.get_curso_by_codigo(curso_data['codigo_curso'])
            if not existing_curso:
                # Criar curso
                curso = Cursos(**curso_data)
                database.create_curso(convert_datetime_for_json(curso.model_dump()))
            
            # Associar professor ao curso
            database.create_professor_curso_relationship(
                professor_data['prontuario'],
                curso_data['codigo_curso']
            )
            
            # Cadastrar disciplinas do curso
            for disciplina_data in curso_data.get('disciplinas', []):
                # Verificar se disciplina já existe
                existing_disciplina = database.get_disciplina_by_id(disciplina_data['id_disciplina'])
                if not existing_disciplina:
                    # Criar disciplina
                    disciplina = Disciplinas(**disciplina_data)
                    database.create_disciplina(convert_datetime_for_json(disciplina.model_dump()))
                
                # Associar disciplina ao curso
                database.create_curso_disciplina_relationship(
                    curso_data['codigo_curso'],
                    disciplina_data['id_disciplina']
                )
        
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

# Função para upload de PDFs
def upload_pdfs(course_code: str, professor_prontuario: str) -> List[Dict]:
    uploaded_files = st.file_uploader(
        "Selecione os PDFs (Ementa + Histórico Escolar)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Mínimo 1 PDF, máximo 5 PDFs por lote"
    )
    
    if uploaded_files:
        if len(uploaded_files) < 1:
            st.error("Selecione pelo menos 1 PDF!")
            return []
        
        if len(uploaded_files) > 5:
            st.error("Máximo 5 PDFs por lote!")
            return []
        
        # Verificar se Google Drive está configurado
        drive_available = os.path.exists('credentials.json')
        
        if not drive_available:
            st.warning("⚠️ Google Drive não configurado. Arquivos serão salvos apenas localmente.")
        
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
                        with st.spinner(f"📤 Enviando {uploaded_file.name} para o Google Drive..."):
                            drive_id = drive_service.upload_file(
                                file_path, 
                                uploaded_file.name, 
                                'application/pdf'
                            )
                        
                        if drive_id:
                            st.success(f"✅ {uploaded_file.name} enviado para o Google Drive!")
                        else:
                            st.warning(f"⚠️ Falha ao enviar {uploaded_file.name} para o Google Drive")
                    except Exception as e:
                        error_msg = str(e)
                        if "invalid_grant" in error_msg or "Token has been expired" in error_msg:
                            st.error(f"🔑 Token do Google Drive expirado para {uploaded_file.name}")
                            handle_drive_token_error()
                            return []  # Parar processamento
                        else:
                            st.warning(f"⚠️ Erro ao enviar {uploaded_file.name} para o Google Drive: {error_msg}")
                            st.info("💡 Continuando com processamento local...")
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
                ementa_result = database.create_ementa(ementa_dict)
                
                if ementa_result and 'id_ementa' in ementa_result:
                    ementa_id = ementa_result['id_ementa']
                    ementas_data.append({
                        'id_ementa': ementa_id,
                        'nome_arquivo': uploaded_file.name,
                        'caminho': file_path,
                        'drive_id': drive_id
                    })
                else:
                    st.error(f"❌ Erro ao criar registro da ementa para {uploaded_file.name}")
                    continue
                
            except Exception as e:
                st.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")
        
        return ementas_data
    
    return []

# Função para análise real com IA
def process_analysis_with_ai(ementa_id: int, course_code: str, professor_prontuario: str) -> List[Dict]:
    """Processa análise real usando IA"""
    
    try:
        # Inicializar cliente de IA
        ai_client = GroqClient()
    except ValueError as e:
        st.error(f"❌ Erro de configuração da API: {str(e)}")
        st.info("💡 Para configurar a chave da API do Groq:")
        st.info("1. Acesse https://console.groq.com/keys")
        st.info("2. Crie uma conta e obtenha sua chave da API")
        st.info("3. Configure a variável de ambiente GROQ_API_KEY ou crie um arquivo .env")
        return []
    
    try:
        # Verificar se ementa_id é válido
        if not ementa_id or ementa_id is None:
            st.error("❌ ID da ementa inválido! Verifique se o upload foi realizado corretamente.")
            return []
        
        # Buscar dados da ementa
        ementa_data = database.get_ementa_by_id(ementa_id)
        if not ementa_data:
            st.error(f"❌ Ementa {ementa_id} não encontrada no banco de dados!")
            return []
        
        # Buscar dados do curso
        curso_data = database.get_curso_by_codigo(course_code)
        if not curso_data:
            st.error(f"Curso {course_code} não encontrado!")
            return []
        
        # Se a ementa tem drive_id, baixar do Google Drive
        if ementa_data.get('drive_id') and not ementa_data['drive_id'].startswith('local_'):
            with st.spinner("📥 Baixando ementa do Google Drive..."):
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
                        st.success("⚡ Extração rápida + IA para estruturação")
                    elif extraction_method == "docling":
                        st.info("✨ Usando Docling para extração estruturada")
                    elif extraction_method == "pymupdf_fast":
                        st.info("⚡ Extração rápida com PyMuPDF")
                    elif extraction_method == "pymupdf_fallback":
                        st.warning("⚠️ Fallback para PyMuPDF simples")
                    
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
                    st.success("⚡ Extração rápida + IA para estruturação")
                elif extraction_method == "docling":
                    st.info("✨ Usando Docling para extração estruturada")
                elif extraction_method == "pymupdf_fast":
                    st.info("⚡ Extração rápida com PyMuPDF")
                elif extraction_method == "pymupdf_fallback":
                    st.warning("⚠️ Fallback para PyMuPDF simples")
            else:
                st.error("Arquivo da ementa não encontrado!")
                return []
        
        if not texto_ementa.strip():
            st.error("Não foi possível extrair texto da ementa!")
            return []
        
        # Gerar resumo da ementa
        with st.spinner("🤖 Gerando resumo da ementa..."):
            resumo_ementa = ai_client.resume_ementa(texto_ementa)
        
        # Gerar score da análise
        with st.spinner("📊 Calculando score da análise..."):
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
        with st.spinner("📝 Gerando análise detalhada..."):
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
            
            # Debug removido para produção
            
            # Salvar no banco com relacionamento ao curso
            analise_result = database.create_analise(analise_dict, curso_codigo=course_code)
            
            if analise_result:
                analise_id = analise_result.get('analise_id')
                analise_data['analise_id'] = analise_id
                st.success(f"✅ Análise salva com ID: {analise_id} e vinculada ao curso {course_code}")
            else:
                st.error("❌ Falha ao salvar análise no banco de dados")
                analise_data['analise_id'] = None
                
        except Exception as e:
            st.error(f"❌ Erro ao salvar análise: {str(e)}")
            import traceback
            st.error(f"Detalhes do erro: {traceback.format_exc()}")
            analise_data['analise_id'] = None
        
        return [analise_data]
    
    except Exception as e:
        st.error(f"❌ Erro ao processar análise: {str(e)}")
        return []

# ==================== INTERFACE PRINCIPAL ====================

# Cabeçalho principal
st.markdown("""
<div class="main-header">
    <h1>🎓 Nexus Education</h1>
    <p>Sistema de Análise de Ementas Acadêmicas</p>
</div>
""", unsafe_allow_html=True)

# Verificar se usuário está logado
if not is_logged_in():
    # ==================== PÁGINA DE LOGIN ====================
    
    st.markdown("### 🔐 Acesso ao Sistema")
    
    # Tabs para Login e Cadastro
    # Se show_login_tab estiver definido, mostrar login primeiro
    if st.session_state.get('show_login_tab', False):
        tab1, tab2 = st.tabs(["Login", "Cadastro"])
        # Limpar o flag após usar
        del st.session_state['show_login_tab']
    else:
        tab1, tab2 = st.tabs(["Login", "Cadastro"])
    
    with tab1:
        st.markdown("""
        <div class="login-container">
            <h3 style="text-align: center;">Login</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar mensagem se foi redirecionado do cadastro
        if st.session_state.get('show_login_tab', False):
            st.success("🎉 Cadastro realizado com sucesso! Agora faça login com suas credenciais.")
        
        with st.form("login_form"):
            login_field = st.text_input("Email ou Prontuário", placeholder="seu.email@universidade.edu ou SP1234567")
            senha = st.text_input("Senha", type="password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_submitted = st.form_submit_button("Entrar", use_container_width=True)
            with col2:
                google_login = st.form_submit_button("Login com Google", use_container_width=True)
        
        if login_submitted:
            if login_field and senha:
                # Detectar automaticamente se é email ou prontuário e autenticar
                professor = authenticate_professor_unified(login_field, senha)
                if professor:
                    st.session_state.user_logged_in = True
                    st.session_state.user_data = professor
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
        
        if google_login:
            st.info("🚧 Login com Google será implementado em breve!")
    
    with tab2:
        st.markdown("""
        <div class="login-container">
            <h3 style="text-align: center;">Cadastrar</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("register_form"):
            st.markdown("#### Dados Pessoais")
            nome = st.text_input("Nome Completo", placeholder="Seu nome completo")
            prontuario = st.text_input("Prontuário", placeholder="SP3456789", max_chars=9)
            email = st.text_input("Email Educacional", placeholder="seu.email@universidade.edu")
            senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar Senha", type="password")
            
            st.markdown("#### Cursos que Leciona")
            st.markdown("Adicione os cursos que você leciona:")
            
            # Interface para adicionar cursos
            if 'cursos_temp' not in st.session_state:
                st.session_state.cursos_temp = []
            
            # Formulário para adicionar curso
            with st.container():
                st.markdown("**➕ Adicionar Novo Curso**")
                col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                codigo_curso = st.text_input("Código do Curso", placeholder="Ex: ENG001", key="new_course_code")
            with col2:
                nome_curso = st.text_input("Nome do Curso", placeholder="Ex: Engenharia de Software", key="new_course_name")
            with col3:
                if st.form_submit_button("➕ Adicionar", key="add_course"):
                    if codigo_curso and nome_curso:
                        # Verificar se código já existe
                        codigo_existe = any(curso['codigo_curso'] == codigo_curso for curso in st.session_state.cursos_temp)
                        if codigo_existe:
                            st.error("Código do curso já existe!")
                        else:
                            curso_data = {
                                'codigo_curso': codigo_curso.upper(),
                                'nome': nome_curso,
                                'descricao_curso': f"Curso de {nome_curso}",
                                'disciplinas': []
                            }
                            st.session_state.cursos_temp.append(curso_data)
                            st.success(f"✅ Curso {nome_curso} adicionado!")
                            st.rerun()
                    else:
                        st.error("Preencha todos os campos!")
            
            # Exibir cursos adicionados com melhor interface
            if st.session_state.cursos_temp:
                st.markdown("---")
                st.markdown("### 📚 Cursos Adicionados")
                
                for i, curso in enumerate(st.session_state.cursos_temp):
                    with st.container():
                        st.markdown(f"""
                        <div class="course-card">
                            <h4>🎓 {curso['codigo_curso']} - {curso['nome']}</h4>
                            <p><strong>Disciplinas:</strong> {len(curso['disciplinas'])} cadastradas</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botões de ação do curso
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col1:
                            if st.form_submit_button("🗑️ Remover Curso", key=f"remove_course_{i}"):
                                st.session_state.cursos_temp.pop(i)
                                st.success("Curso removido!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("📝 Gerenciar Disciplinas", key=f"manage_disc_{i}"):
                                if f"show_disc_{i}" not in st.session_state:
                                    st.session_state[f"show_disc_{i}"] = True
                                else:
                                    st.session_state[f"show_disc_{i}"] = not st.session_state[f"show_disc_{i}"]
                                st.rerun()
                        with col3:
                            if st.form_submit_button("📊 Ver Disciplinas", key=f"view_disc_{i}"):
                                st.session_state[f"show_disc_{i}"] = True
                                st.rerun()
            
                # Seção de gerenciamento de disciplinas
                for i, curso in enumerate(st.session_state.cursos_temp):
                    if st.session_state.get(f"show_disc_{i}", False):
                        st.markdown(f"---")
                        st.markdown(f"### 📖 Disciplinas - {curso['nome']} ({curso['codigo_curso']})")
                        
                        # Listar disciplinas existentes
                        if curso['disciplinas']:
                            st.markdown("**Disciplinas Cadastradas:**")
                            for j, disciplina in enumerate(curso['disciplinas']):
                                st.markdown(f"""
                                <div class="discipline-item">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <strong>📚 {disciplina['id_disciplina']} - {disciplina['nome']}</strong><br>
                                            <small>⏰ {disciplina['carga_horaria']} horas</small>
                                        </div>
                                        <div>
                                            <button onclick="editDiscipline({i}, {j})" style="margin-right: 5px;">✏️</button>
                                            <button onclick="deleteDiscipline({i}, {j})">🗑️</button>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Botões de ação (mantidos para funcionalidade)
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    if st.form_submit_button("✏️ Editar", key=f"edit_disc_{i}_{j}"):
                                        st.session_state[f"editing_disc_{i}_{j}"] = True
                                        st.rerun()
                                with col2:
                                    if st.form_submit_button("🗑️ Remover", key=f"delete_disc_{i}_{j}"):
                                        curso['disciplinas'].pop(j)
                                        st.success(f"Disciplina {disciplina['nome']} removida!")
                                        st.rerun()
                        else:
                            st.info("Nenhuma disciplina cadastrada para este curso.")
                        
                        # Formulário para adicionar disciplina
                        st.markdown("**➕ Adicionar Nova Disciplina**")
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            id_disciplina = st.text_input(f"ID Disciplina", key=f"disc_id_{i}", placeholder="Ex: DISC001")
                        with col2:
                            nome_disciplina = st.text_input(f"Nome Disciplina", key=f"disc_nome_{i}", placeholder="Ex: Programação I")
                        with col3:
                            carga_horaria = st.number_input(f"Carga Horária", min_value=1, max_value=200, key=f"disc_carga_{i}", value=60)
                        with col4:
                            if st.form_submit_button("➕ Adicionar", key=f"add_disc_{i}"):
                                if id_disciplina and nome_disciplina and carga_horaria:
                                    # Verificar se ID já existe neste curso
                                    id_existe = any(disc['id_disciplina'] == id_disciplina for disc in curso['disciplinas'])
                                    if id_existe:
                                        st.error("ID da disciplina já existe neste curso!")
                                    else:
                                        disciplina_data = {
                                            'id_disciplina': id_disciplina.upper(),
                                            'nome': nome_disciplina,
                                            'carga_horaria': carga_horaria
                                        }
                                        curso['disciplinas'].append(disciplina_data)
                                        st.success(f"✅ Disciplina {nome_disciplina} adicionada!")
                                        st.rerun()
                                else:
                                    st.error("Preencha todos os campos!")
                        
                        # Botão para fechar seção
                        if st.form_submit_button("❌ Fechar Gerenciamento", key=f"close_disc_{i}"):
                            st.session_state[f"show_disc_{i}"] = False
                            st.rerun()
            else:
                st.info("👆 Adicione pelo menos um curso para continuar.")
            
            # Resumo dos cursos e disciplinas
            if st.session_state.cursos_temp:
                st.markdown("---")
                st.markdown("### 📊 Resumo do Cadastro")
                
                total_cursos = len(st.session_state.cursos_temp)
                total_disciplinas = sum(len(curso['disciplinas']) for curso in st.session_state.cursos_temp)
                total_horas = sum(sum(disc['carga_horaria'] for disc in curso['disciplinas']) for curso in st.session_state.cursos_temp)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📚 Cursos", total_cursos)
                with col2:
                    st.metric("📖 Disciplinas", total_disciplinas)
                with col3:
                    st.metric("⏰ Total de Horas", f"{total_horas}h")
                with col4:
                    st.metric("📈 Média/Curso", f"{total_disciplinas/total_cursos:.1f}" if total_cursos > 0 else "0")
                
                # Lista resumida
                st.markdown("**Lista de Cursos e Disciplinas:**")
                for i, curso in enumerate(st.session_state.cursos_temp):
                    with st.expander(f"🎓 {curso['codigo_curso']} - {curso['nome']} ({len(curso['disciplinas'])} disciplinas)"):
                        if curso['disciplinas']:
                            for disciplina in curso['disciplinas']:
                                st.write(f"  📚 {disciplina['id_disciplina']} - {disciplina['nome']} ({disciplina['carga_horaria']}h)")
                        else:
                            st.write("  ℹ️ Nenhuma disciplina cadastrada")
            
            # Botão de cadastro
            if st.form_submit_button("Cadastrar", use_container_width=True):
                if nome and prontuario and email and senha and confirmar_senha:
                    if senha != confirmar_senha:
                        st.error("Senhas não coincidem!")
                    elif not is_valid_email(email):
                        st.error("Email inválido!")
                    elif len(prontuario) != 9:
                        st.error("Prontuário deve ter 9 dígitos!")
                    elif not st.session_state.cursos_temp:
                        st.error("Adicione pelo menos um curso!")
                    else:
                        professor_data = {
                            'prontuario': prontuario,
                            'nome': nome,
                            'email_educacional': email,
                            'senha': senha,
                            'cursos': st.session_state.cursos_temp
                        }
                        
                        if register_professor(professor_data):
                            st.success("🎉 Cadastro realizado com sucesso!")
                            st.info("🔄 Fazendo login automaticamente...")
                            st.session_state.cursos_temp = []
                            
                            # Fazer login automático após cadastro
                            professor = authenticate_professor(email, senha)
                            if professor:
                                st.session_state.user_logged_in = True
                                st.session_state.user_data = professor
                                st.success("✅ Login automático realizado! Bem-vindo ao sistema!")
                                st.rerun()
                            else:
                                st.error("❌ Erro no login automático. Faça login manualmente.")
                                st.session_state['show_login_tab'] = True
                                st.rerun()

else:
    # ==================== PÁGINA PRINCIPAL (HOME) ====================
    
    # Barra lateral com informações do usuário
    with st.sidebar:
        st.markdown(f"### 👋 Olá, {st.session_state.user_data['nome']}!")
        st.markdown(f"**Prontuário:** {st.session_state.user_data['prontuario']}")
        st.markdown(f"**Email:** {st.session_state.user_data['email_educacional']}")
        
        st.markdown("---")
        
        # Botão de Gerenciamento de Cursos
        if st.button("⚙️ Gerenciar Cursos e Disciplinas", use_container_width=True, type="primary"):
            st.session_state.show_gerenciar_cursos = True
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
    
    # Modal de Gerenciamento de Cursos
    if st.session_state.get('show_gerenciar_cursos', False):
        st.markdown("## ⚙️ Gerenciar Cursos e Disciplinas")
        
        # Buscar cursos do professor
        professor_cursos = database.get_professor_courses(st.session_state.user_data['prontuario'])
        
        if professor_cursos:
            for curso in professor_cursos:
                with st.expander(f"🎓 {curso['codigo_curso']} - {curso['nome']}", expanded=False):
                    st.markdown(f"**Código:** {curso['codigo_curso']}")
                    st.markdown(f"**Nome:** {curso['nome']}")
                    
                    # Buscar disciplinas do curso
                    disciplinas = database.get_course_disciplines(curso['codigo_curso'])
                    
                    st.markdown("---")
                    st.markdown("### 📚 Disciplinas")
                    
                    if disciplinas:
                        for disc in disciplinas:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.markdown(f"**{disc['id_disciplina']}** - {disc['nome']}")
                            with col2:
                                st.markdown(f"⏰ {disc['carga_horaria']}h")
                            with col3:
                                if st.button("🗑️", key=f"del_disc_{disc['id_disciplina']}", help="Remover disciplina"):
                                    if database.delete_disciplina(disc['id_disciplina']):
                                        st.success("Disciplina removida!")
                                        st.rerun()
                    else:
                        st.info("Nenhuma disciplina cadastrada para este curso.")
                    
                    # Adicionar nova disciplina
                    st.markdown("---")
                    st.markdown("**➕ Adicionar Nova Disciplina**")
                    
                    with st.form(key=f"add_disc_form_{curso['codigo_curso']}"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            new_disc_id = st.text_input("ID Disciplina", placeholder="Ex: DISC001")
                        with col2:
                            new_disc_nome = st.text_input("Nome", placeholder="Ex: Programação I")
                        with col3:
                            new_disc_carga = st.number_input("Horas", min_value=1, max_value=200, value=60)
                        
                        if st.form_submit_button("➕ Adicionar Disciplina"):
                            if new_disc_id and new_disc_nome:
                                # Criar disciplina
                                disciplina_obj = Disciplinas(
                                    id_disciplina=new_disc_id.upper(),
                                    nome=new_disc_nome,
                                    carga_horaria=new_disc_carga
                                )
                                
                                if database.create_disciplina(disciplina_obj.model_dump()):
                                    # Vincular ao curso
                                    database.add_disciplina_to_curso(curso['codigo_curso'], new_disc_id.upper())
                                    st.success(f"✅ Disciplina {new_disc_nome} adicionada!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao criar disciplina. Verifique se o ID já existe.")
                            else:
                                st.error("Preencha ID e Nome da disciplina!")
        else:
            st.info("Você ainda não possui cursos cadastrados.")
        
        st.markdown("---")
        if st.button("❌ Fechar Gerenciamento", use_container_width=True):
            st.session_state.show_gerenciar_cursos = False
            st.rerun()
        
        st.markdown("---")
    
    # Título principal
    st.markdown("### 🏠 Página Principal")
    st.markdown("**Comece a analisar requerimentos de alunos**")
    
    # Seleção de curso
    st.markdown("#### 📚 Selecione um Curso")
    professor_courses = database.get_professor_courses(st.session_state.user_data['prontuario'])
    
    if not professor_courses:
        st.warning("Você não possui cursos cadastrados. Entre em contato com o administrador.")
    else:
        course_options = [f"{curso['codigo_curso']} - {curso['nome']}" for curso in professor_courses]
        
        # Determinar o índice inicial baseado no curso selecionado anteriormente
        initial_index = None
        if 'selected_course' in st.session_state and st.session_state.selected_course:
            try:
                initial_index = next(i for i, option in enumerate(course_options) 
                                   if option.startswith(st.session_state.selected_course + " - "))
            except StopIteration:
                initial_index = None
                # Se não encontrar o curso anterior, limpar o estado
                if 'selected_course' in st.session_state:
                    del st.session_state.selected_course
        
        selected_course = st.selectbox(
            "Escolha o curso para análise:",
            course_options,
            index=initial_index
        )
        
        if selected_course:
            # Extrair código do curso selecionado
            course_code = selected_course.split(" - ")[0]
            
            # Verificar se o curso mudou e limpar dados do curso anterior
            if 'selected_course' in st.session_state and st.session_state.selected_course != course_code:
                # Limpar análises do curso anterior quando trocar de curso
                if 'analyses_data' in st.session_state:
                    del st.session_state.analyses_data
            
            # Atualizar o curso selecionado
            st.session_state.selected_course = course_code
            
            # Mostrar informações do curso selecionado
            curso_info = database.get_curso_by_codigo(course_code)
            if curso_info:
                st.markdown(f"### 📚 {curso_info['nome']}")
                st.markdown(f"**Código:** {curso_info['codigo_curso']}")
                st.markdown(f"**Descrição:** {curso_info['descricao_curso']}")
            else:
                st.error(f"❌ Erro: Não foi possível carregar informações do curso {course_code}")
                st.info("Tente selecionar o curso novamente.")
                
                # Debug temporário - remover em produção
                with st.expander("🔍 Debug - Informações do Curso"):
                    st.write(f"Course Code: {course_code}")
                    st.write(f"Professor Courses: {[c['codigo_curso'] for c in professor_courses]}")
                    st.write(f"Database Type: {type(database).__name__}")
                    st.write(f"Use Supabase: {getattr(database, 'use_supabase', 'N/A')}")
            
            # Seção: Disciplinas do Curso
            st.markdown("#### 📖 Disciplinas do Curso")
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
                st.info("📝 Nenhuma disciplina cadastrada para este curso.")
                st.markdown("""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <p><strong>💡 Dica:</strong> Para cadastrar disciplinas para este curso, acesse a seção de administração.</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Seção: Dashboard e Histórico completo do curso
            st.markdown("### 📊 Dashboard de Análises")
            st.markdown(f"**Curso:** {curso_info['nome']} ({course_code})")
            
            # Buscar todas as análises do curso selecionado feitas pelo professor logado (histórico)
            historico_analyses = database.get_analises_by_curso_and_professor_usando_relacionamento(course_code, st.session_state.user_data['prontuario'])
            
            if historico_analyses:
                # Criar DataFrame com histórico
                df_historico = pd.DataFrame(historico_analyses)
                
                # ==================== DASHBOARD COM GRÁFICOS ====================
                st.markdown("#### 📈 Visão Geral do Curso")
                
                # KPIs Principais
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("📊 Total de Análises", len(historico_analyses))
                
                with col2:
                    adequados_historico = len(df_historico[df_historico['adequado'] == True])
                    taxa_adequacao = (adequados_historico / len(historico_analyses) * 100) if len(historico_analyses) > 0 else 0
                    st.metric("✅ Adequados", f"{adequados_historico} ({taxa_adequacao:.0f}%)")
                
                with col3:
                    nao_adequados = len(historico_analyses) - adequados_historico
                    st.metric("❌ Não Adequados", nao_adequados)
                
                with col4:
                    score_medio_historico = df_historico['score'].mean()
                    st.metric("📊 Score Médio", f"{score_medio_historico:.1f}/100")
                
                with col5:
                    score_max_historico = df_historico['score'].max()
                    st.metric("🏆 Score Máximo", f"{score_max_historico}/100")
                
                st.markdown("---")
                
                # Linha 1: Gráficos de Status e Distribuição de Scores
                st.markdown("#### 📊 Análises Estatísticas")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Gráfico de Pizza - Status dos Alunos
                    st.markdown("##### 🎯 Status dos Alunos")
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
                    st.markdown("##### 📊 Distribuição de Scores")
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
                    st.markdown("##### 📦 Análise de Scores")
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
                    st.markdown("##### 📅 Evolução Temporal")
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
                    st.markdown("##### 🏆 Top 10 Melhores Scores")
                    top_alunos = df_historico.nlargest(10, 'score')[['nome_aluno', 'score', 'adequado']].copy()
                    top_alunos['Posição'] = range(1, len(top_alunos) + 1)
                    top_alunos['Status'] = top_alunos['adequado'].apply(lambda x: '✅' if x else '❌')
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
                st.markdown("#### 📈 Estatísticas Detalhadas")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📉 Score Mínimo", f"{df_historico['score'].min()}/100")
                    st.metric("📊 Mediana", f"{df_historico['score'].median():.1f}/100")
                
                with col2:
                    desvio_padrao = df_historico['score'].std()
                    st.metric("📏 Desvio Padrão", f"{desvio_padrao:.2f}")
                    q1 = df_historico['score'].quantile(0.25)
                    st.metric("📊 1º Quartil", f"{q1:.1f}/100")
                
                with col3:
                    q3 = df_historico['score'].quantile(0.75)
                    st.metric("📊 3º Quartil", f"{q3:.1f}/100")
                    scores_acima_70 = len(df_historico[df_historico['score'] >= 70])
                    st.metric("✅ Scores ≥ 70", f"{scores_acima_70} ({scores_acima_70/len(df_historico)*100:.0f}%)")
                
                with col4:
                    scores_abaixo_50 = len(df_historico[df_historico['score'] < 50])
                    st.metric("⚠️ Scores < 50", f"{scores_abaixo_50} ({scores_abaixo_50/len(df_historico)*100:.0f}%)")
                    amplitude = df_historico['score'].max() - df_historico['score'].min()
                    st.metric("📏 Amplitude", f"{amplitude}")
                
                st.markdown("---")
                
                # Histórico Completo em Tabela
                st.markdown("#### 📋 Histórico Completo de Análises")
                
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
                
                # Seção: Detalhes Automáticos ao Selecionar
                selected_rows = response_historico.get('selected_rows', []) if response_historico else []
                
                if selected_rows and len(selected_rows) == 1:
                    # Mostrar detalhes automaticamente quando uma linha é selecionada
                    row = selected_rows[0]
                    analise_completa = database.get_analise_by_id(row['ID'])
                    
                    if analise_completa:
                        st.markdown("---")
                        st.markdown(f"### 📋 Detalhes da Análise - {row['Nome do Aluno']}")
                        
                        # Cards com informações principais
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("📊 Score", f"{row['Score']}/100")
                        with col2:
                            st.metric("✅ Status", "Adequado" if analise_completa['adequado'] else "Não Adequado")
                        with col3:
                            if 'created_at' in analise_completa:
                                from datetime import datetime
                                data = datetime.fromisoformat(analise_completa['created_at'].replace('Z', '+00:00'))
                                st.metric("📅 Data", data.strftime('%d/%m/%Y'))
                        with col4:
                            metodo = "IA" if analise_completa.get('dados_estruturados_json') else "Regex"
                            st.metric("🔧 Método", metodo)
                        
                        # Análise da IA
                        with st.expander("🤖 Análise Completa da IA", expanded=True):
                            st.markdown(analise_completa['texto_analise'])
                        
                        # Dados Estruturados Extraídos
                        if analise_completa.get('dados_estruturados_json'):
                            try:
                                dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                
                                with st.expander("📊 Dados Estruturados Extraídos", expanded=True):
                                    # Informações do Aluno
                                    st.markdown("#### 👤 Informações do Aluno")
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
                                        st.markdown("#### 🔧 Informações da Extração")
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
                                        st.markdown("#### 📚 Disciplinas Extraídas")
                                        df_disciplines = pd.DataFrame(disciplines)
                                        st.dataframe(df_disciplines, use_container_width=True)
                                    
                                    # JSON Completo
                                    with st.expander("🔍 Ver JSON Completo"):
                                        st.json(dados_estruturados)
                                        
                            except Exception as e:
                                st.warning(f"Erro ao processar dados estruturados: {e}")
                        else:
                            st.info("💡 Esta análise foi processada antes da implementação do sistema de extração estruturada")
                
                # Seção: Ações das Análises
                st.markdown("---")
                st.markdown("### 🔍 Ações das Análises")
                st.markdown("Digite o ID da análise (visível na coluna ID da tabela acima) para visualizar detalhes ou excluir.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### 📄 Ver Detalhes da Análise")
                    analise_id_ver = st.number_input("ID da Análise:", min_value=1, step=1, key="id_ver_detalhes")
                    
                    if st.button("🔍 Buscar Detalhes", use_container_width=True, key="buscar_detalhes_historico"):
                        analise = database.get_analise_by_id(analise_id_ver)
                        
                        if analise:
                            with st.expander(f"📋 {analise['nome_aluno']} - Score: {analise['score']}/100", expanded=True):
                                st.markdown("**🤖 Análise da IA:**")
                                st.markdown(analise['texto_analise'])
                                st.markdown("---")
                                
                                # Dados estruturados se existirem
                                if analise.get('dados_estruturados_json'):
                                    try:
                                        dados_estruturados = json.loads(analise['dados_estruturados_json'])
                                        st.markdown("**📊 Dados Estruturados:**")
                                        student_info = dados_estruturados.get('student_info', {})
                                        
                                        col_a, col_b = st.columns(2)
                                        with col_a:
                                            st.markdown(f"**Nome:** {student_info.get('nome', 'N/A')}")
                                            st.markdown(f"**RA:** {student_info.get('ra', 'N/A')}")
                                            st.markdown(f"**CPF:** {student_info.get('cpf', 'N/A')}")
                                        with col_b:
                                            st.markdown(f"**Curso:** {student_info.get('curso', 'N/A')}")
                                            st.markdown(f"**Data:** {student_info.get('data_matricula', 'N/A')}")
                                        
                                        with st.expander("🔍 Ver JSON Completo"):
                                            st.json(dados_estruturados)
                                    except:
                                        pass
                                
                                # Informações adicionais
                                st.markdown("---")
                                st.markdown("**📌 Informações da Análise:**")
                                st.markdown(f"- **ID:** {analise['analise_id']}")
                                st.markdown(f"- **Status:** {'✅ Adequado' if analise['adequado'] else '❌ Não Adequado'}")
                                st.markdown(f"- **Matérias Restantes:** {analise.get('materias_restantes', 'N/A')}")
                                st.markdown(f"- **Data:** {analise.get('created_at', 'N/A')}")
                        else:
                            st.error(f"❌ Análise com ID {analise_id_ver} não encontrada!")
                
                with col2:
                    st.markdown("##### 🗑️ Excluir Análise")
                    
                    # Inicializar estado de confirmação
                    if 'confirmar_exclusao_id' not in st.session_state:
                        st.session_state.confirmar_exclusao_id = None
                    
                    analise_id_excluir = st.number_input("ID da Análise:", min_value=1, step=1, key="id_excluir")
                    
                    # Se não está em modo de confirmação
                    if st.session_state.confirmar_exclusao_id is None:
                        if st.button("🗑️ Excluir Análise", use_container_width=True, key="excluir_analise_historico", type="primary"):
                            # Buscar análise para confirmar
                            analise_confirmacao = database.get_analise_by_id(analise_id_excluir)
                            
                            if analise_confirmacao:
                                st.session_state.confirmar_exclusao_id = analise_id_excluir
                                st.session_state.confirmar_exclusao_nome = analise_confirmacao['nome_aluno']
                                st.rerun()
                            else:
                                st.error(f"❌ Análise com ID {analise_id_excluir} não encontrada!")
                    
                    # Se está em modo de confirmação
                    else:
                        st.warning(f"⚠️ Você está prestes a excluir a análise de **{st.session_state.confirmar_exclusao_nome}**")
                        st.warning(f"**ID: {st.session_state.confirmar_exclusao_id}**")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ Confirmar Exclusão", use_container_width=True, key="confirmar_exclusao_btn", type="primary"):
                                if database.delete_analise(st.session_state.confirmar_exclusao_id, st.session_state.user_data['prontuario']):
                                    st.success(f"✅ Análise ID {st.session_state.confirmar_exclusao_id} excluída com sucesso!")
                                    st.session_state.confirmar_exclusao_id = None
                                    st.session_state.confirmar_exclusao_nome = None
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao excluir análise. Você pode não ter permissão.")
                                    st.session_state.confirmar_exclusao_id = None
                                    st.session_state.confirmar_exclusao_nome = None
                        with col_b:
                            if st.button("❌ Cancelar", use_container_width=True, key="cancelar_exclusao_btn"):
                                st.session_state.confirmar_exclusao_id = None
                                st.session_state.confirmar_exclusao_nome = None
                                st.info("Exclusão cancelada.")
                                st.rerun()
            else:
                st.info("Nenhuma análise encontrada no histórico deste curso.")
            
            st.markdown("---")
            
            # Upload de PDFs
            st.markdown("#### 📄 Upload de Ementas")
            st.markdown("""
            <div class="upload-area">
                <p>📁 Arraste e solte seus PDFs aqui ou clique para selecionar</p>
                <p><small>Mínimo: 1 PDF | Máximo: 5 PDFs por lote</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            ementas_data = upload_pdfs(course_code, st.session_state.user_data['prontuario'])
            
            if ementas_data:
                st.success(f"✅ {len(ementas_data)} PDF(s) carregado(s) com sucesso!")
                
                # Botão para processar análises
                if st.button("🔍 Processar Análises com IA", use_container_width=True):
                    with st.spinner("Processando análises com IA..."):
                        all_analyses = []
                        valid_ementas = 0
                        
                        for ementa_data in ementas_data:
                            # Verificar se a ementa tem ID válido
                            if ementa_data.get('id_ementa') and ementa_data['id_ementa'] is not None:
                                analyses = process_analysis_with_ai(
                                    ementa_data['id_ementa'], 
                                    course_code, 
                                    st.session_state.user_data['prontuario']
                                )
                                all_analyses.extend(analyses)
                                valid_ementas += 1
                            else:
                                st.warning(f"⚠️ Pulando {ementa_data.get('nome_arquivo', 'arquivo')} - ID da ementa inválido")
                        
                        if valid_ementas > 0:
                            st.success(f"✅ Análises processadas com sucesso! {valid_ementas} ementa(s) processada(s).")
                            st.session_state.analyses_data = all_analyses
                        else:
                            st.error("❌ Nenhuma ementa válida para processar!")
            
            # Exibir análises se existirem
            if 'analyses_data' in st.session_state and st.session_state.analyses_data:
                st.markdown("#### 📊 Resultados das Análises")
                
                # Usar as análises recém-processadas
                curso_analyses = st.session_state.analyses_data
                
                if curso_analyses:
                    st.markdown("---")
                    st.markdown("### 📈 Estatísticas do Curso")
                    
                    # Criar DataFrame com todas as análises do curso
                    df_curso = pd.DataFrame(curso_analyses)
                    
                    # Gráfico de pizza por status
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### 🎯 Status dos Alunos")
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
                        st.markdown("##### 📊 Distribuição de Scores")
                        
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
                    st.markdown("##### 📋 Resumo Estatístico")
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
                    st.markdown("### 👥 Todos os Alunos Analisados no Curso")
                    
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
                    
                    # Detalhes automáticos ao selecionar (curso)
                    selected_rows_curso = response_curso.get('selected_rows', []) if response_curso else []
                    
                    if selected_rows_curso and len(selected_rows_curso) == 1:
                        row = selected_rows_curso[0]
                        analise_completa = database.get_analise_by_id(row['ID'])
                        
                        if analise_completa:
                            st.markdown("---")
                            st.markdown(f"### 📋 Detalhes da Análise - {row['Nome do Aluno']}")
                            
                            # Cards com informações principais
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("📊 Score", f"{row['Score']}/100")
                            with col2:
                                st.metric("✅ Status", "Adequado" if analise_completa['adequado'] else "Não Adequado")
                            with col3:
                                if 'created_at' in analise_completa:
                                    from datetime import datetime
                                    data = datetime.fromisoformat(analise_completa['created_at'].replace('Z', '+00:00'))
                                    st.metric("📅 Data", data.strftime('%d/%m/%Y'))
                            with col4:
                                metodo = "IA" if analise_completa.get('dados_estruturados_json') else "Regex"
                                st.metric("🔧 Método", metodo)
                            
                            # Análise da IA
                            with st.expander("🤖 Análise Completa da IA", expanded=True):
                                st.markdown(analise_completa['texto_analise'])
                            
                            # Dados Estruturados Extraídos
                            if analise_completa.get('dados_estruturados_json'):
                                try:
                                    dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                    
                                    with st.expander("📊 Dados Estruturados Extraídos", expanded=True):
                                        # Informações do Aluno
                                        st.markdown("#### 👤 Informações do Aluno")
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
                                            st.markdown("#### 🔧 Informações da Extração")
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
                                            st.markdown("#### 📚 Disciplinas Extraídas")
                                            df_disciplines = pd.DataFrame(disciplines)
                                            st.dataframe(df_disciplines, use_container_width=True)
                                        
                                        # JSON Completo
                                        with st.expander("🔍 Ver JSON Completo"):
                                            st.json(dados_estruturados)
                                            
                                except Exception as e:
                                    st.warning(f"Erro ao processar dados estruturados: {e}")
                            else:
                                st.info("💡 Esta análise foi processada antes da implementação do sistema de extração estruturada")
                    
                    st.markdown("---")
                
                # Seção: Estatísticas por Curso
                st.markdown("### 📊 Estatísticas por Curso")
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
                else:
                    st.info("Nenhuma análise encontrada no histórico deste curso.")
                
                st.markdown("---")
                
                # Seção: Detalhes e Ações das Análises
                if historico_analyses:
                    st.markdown("### 🔍 Detalhes e Ações das Análises")
                    st.markdown("Selecione uma ou mais análises na tabela acima e escolha uma ação:")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📄 Ver Detalhes Completos", use_container_width=True):
                            selected_rows = response_historico.get('selected_rows', []) if response_historico else []
                            if selected_rows:
                                for row in selected_rows:
                                    # Buscar análise completa
                                    analise_completa = database.get_analise_by_id(row['ID'])
                                    if analise_completa:
                                        with st.expander(f"📋 {row['Nome do Aluno']} - Score: {row['Score']}", expanded=True):
                                            st.markdown("**🤖 Análise da IA:**")
                                            st.markdown(analise_completa['texto_analise'])
                                            st.markdown("---")
                                            col_a, col_b = st.columns(2)
                                            with col_a:
                                                st.markdown(f"**📊 Score:** {row['Score']}/100")
                                                st.markdown(f"**✅ Status:** {row['Status']}")
                                            with col_b:
                                                st.markdown(f"**📚 Matérias Restantes:** {row['Matérias Restantes']}")
                                                if 'created_at' in analise_completa:
                                                    st.markdown(f"**📅 Data:** {analise_completa['created_at']}")
                                            
                                            # Mostrar dados estruturados se existirem
                                            if analise_completa.get('dados_estruturados_json'):
                                                with st.expander("📊 Dados Estruturados (Docling)"):
                                                    try:
                                                        dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                                        st.json(dados_estruturados)
                                                    except:
                                                        st.warning("Dados estruturados não disponíveis")
                            else:
                                st.info("Selecione pelo menos uma análise na tabela")
                    
                    with col2:
                        if st.button("📊 Comparar Análises", use_container_width=True):
                            selected_rows = response_historico.get('selected_rows', []) if response_historico else []
                            if len(selected_rows) >= 2:
                                st.markdown("##### 📊 Comparação de Análises")
                                df_compare = pd.DataFrame(selected_rows)
                                st.dataframe(df_compare[['Nome do Aluno', 'Score', 'Status']], use_container_width=True)
                                
                                # Gráfico de comparação
                                fig_compare = px.bar(
                                    df_compare,
                                    x='Nome do Aluno',
                                    y='Score',
                                    title="Comparação de Scores",
                                    color='Score',
                                    color_continuous_scale='RdYlGn'
                                )
                                st.plotly_chart(fig_compare, use_container_width=True)
                            else:
                                st.info("Selecione pelo menos 2 análises para comparar")
                    
                    with col3:
                        if st.button("📥 Exportar Selecionadas", use_container_width=True):
                            selected_rows = response_historico.get('selected_rows', []) if response_historico else []
                            if selected_rows:
                                df_export = pd.DataFrame(selected_rows)
                                csv = df_export.to_csv(index=False)
                                st.download_button(
                                    label="⬇️ Baixar CSV",
                                    data=csv,
                                    file_name=f"analises_{course_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                                st.success("Arquivo CSV pronto para download!")
                            else:
                                st.info("Selecione pelo menos uma análise para exportar")
                    
                # Seção removida: duplicação com histórico acima
                
                # Usar historico_analyses ao invés de buscar novamente
                minhas_analises = historico_analyses
                
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
                        if st.button("📄 Ver Análise Detalhada", use_container_width=True):
                            selected_rows = response_minhas.get('selected_rows', []) if response_minhas else []
                            if selected_rows:
                                for row in selected_rows:
                                    # Buscar análise completa
                                    analise_completa = database.get_analise_by_id(row['ID'])
                                    if analise_completa:
                                        st.markdown(f"##### 📋 Análise Detalhada - {row['Nome do Aluno']}")
                                        st.markdown("**Resposta da IA:**")
                                        st.markdown(analise_completa['texto_analise'])
                                        st.markdown("---")
                                        st.markdown(f"**📊 Score:** {row['Score']}/100")
                                        st.markdown(f"**📚 Matérias Restantes:** {row['Matérias Restantes']}")
                                        st.markdown(f"**✅ Status:** {'Adequado para o curso' if row['Adequado'] else 'Precisa de melhorias'}")
                                        st.markdown(f"**📅 Data:** {row['Data']}")
                            else:
                                st.info("Selecione uma análise para ver detalhes")
                    
                    with col2:
                        if st.button("🗑️ Deletar Análise", use_container_width=True):
                            selected_rows = response_minhas.get('selected_rows', []) if response_minhas else []
                            if selected_rows:
                                for row in selected_rows:
                                    analise_id = row['ID']
                                    if database.delete_analise(analise_id, st.session_state.user_data['prontuario']):
                                        st.success(f"✅ Análise de {row['Nome do Aluno']} deletada!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erro ao deletar análise")
                            else:
                                st.info("Selecione uma análise para deletar")
                    
                    with col3:
                        if st.button("📊 Estatísticas Detalhadas", use_container_width=True):
                            st.markdown("##### 📈 Estatísticas Detalhadas das Minhas Análises")
                            
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
                else:
                    st.info("Você ainda não realizou análises para este curso.")
                
                st.markdown("---")
                
                # Exibir resultado da análise de forma centralizada
                if len(st.session_state.analyses_data) == 1:
                    # Se há apenas uma análise, exibir de forma destacada
                    analise = st.session_state.analyses_data[0]
                    
                    # Container centralizado para o resultado
                    st.markdown("---")
                    st.markdown("### 🤖 Análise da IA")
                    
                    # Card com informações principais
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**👤 Aluno:** {analise['nome_aluno']}")
                    
                    with col2:
                        score_color = "🟢" if analise['score'] >= 70 else "🟡" if analise['score'] >= 50 else "🔴"
                        st.markdown(f"**📊 Score:** {score_color} {analise['score']}/100")
                    
                    with col3:
                        status = "✅ Adequado" if analise['adequado'] else "❌ Não Adequado"
                        st.markdown(f"**Status:** {status}")
                    
                    # Exibir o texto da análise de forma destacada
                    st.markdown("---")
                    st.markdown("### 📝 Análise Detalhada")
                    
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
                        st.markdown(f"**📚 Matérias Restantes:** {analise['materias_restantes']}")
                    
                    with col2:
                        st.markdown(f"**🆔 ID da Análise:** {analise['analise_id']}")
                
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
                
                # Se há múltiplas análises, exibir tabela resumida
                if len(st.session_state.analyses_data) > 1:
                    st.markdown("---")
                    st.markdown("### 📋 Resumo das Análises")
                    
                    # Exibir gráfico de barras
                    st.markdown("##### 📈 Gráfico de Pontuações")
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
                    st.markdown("##### 📊 Tabela de Análises")
                    response = AgGrid(
                        df,
                        grid_options=grid_options,
                        enable_enterprise_modules=True,
                        update_mode=GridUpdateMode.SELECTION_CHANGED,
                        theme='streamlit',
                        height=300
                    )
                else:
                    # Para análise única, não exibir tabela
                    response = None
                    selected_rows = []
                
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
                        st.success(f"✅ 1 análise pronta para ação: **{selected_rows[0]['Nome']}**")
                    else:
                        nomes = [row['Nome'] for row in selected_rows]
                        st.success(f"✅ {len(selected_rows)} análises selecionadas: {', '.join(nomes)}")
                
                # Botões de ação
                st.markdown("##### ⚙️ Ações")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("📥 Download Ementa", use_container_width=True):
                        # Verificar se há ementas selecionadas
                        if selected_rows:
                            for row in selected_rows:
                                # Buscar ementa no banco
                                ementa_data = database.get_ementa_by_id(row.get('id_ementa', 0))
                                if ementa_data and ementa_data.get('drive_id'):
                                    drive_id = ementa_data['drive_id']
                                    
                                    # Verificar se é do Google Drive
                                    if drive_id.startswith('local_'):
                                        st.warning("📂 Arquivo salvo apenas localmente")
                                    else:
                                        # Download do Google Drive
                                        with st.spinner("📥 Baixando do Google Drive..."):
                                            file_content = drive_service.download_file(
                                                drive_id, 
                                                f"ementa_{row['Nome']}.pdf"
                                            )
                                        
                                        if file_content:
                                            st.download_button(
                                                label=f"📄 Download {row['Nome']}.pdf",
                                                data=file_content,
                                                file_name=f"ementa_{row['Nome']}.pdf",
                                                mime="application/pdf",
                                                key=f"download_{row.get('ID', 0)}"
                                            )
                                            st.success("✅ Pronto para download!")
                                        else:
                                            st.error("❌ Erro ao baixar do Google Drive")
                                else:
                                    st.info("💡 Ementa não encontrada no banco de dados")
                        else:
                            st.info("📝 Nenhuma análise disponível")
                
                with col2:
                    if st.button("🗑️ Deletar Análise", use_container_width=True):
                        if selected_rows:
                            for row in selected_rows:
                                analise_id = row.get('ID', 0)
                                if database.delete_analise(analise_id, st.session_state.user_data['prontuario']):
                                    st.success(f"✅ Análise de {row['Nome']} deletada!")
                                    # Remover da lista de análises
                                    st.session_state.analyses_data = [
                                        a for a in st.session_state.analyses_data 
                                        if a.get('analise_id') != analise_id
                                    ]
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao deletar análise")
                        else:
                            st.info("Selecione uma análise para deletar")
                
                with col3:
                    if st.button("📄 Ver Análise Detalhada", use_container_width=True):
                        if selected_rows:
                            for row in selected_rows:
                                with st.expander(f"📋 Análise Detalhada - {row['Nome']}", expanded=True):
                                    # Buscar dados completos do banco
                                    analise_completa = database.get_analise_by_id(row.get('ID'))
                                    
                                    if analise_completa:
                                        # Análise da IA
                                        st.markdown("**🤖 Análise da IA:**")
                                        st.markdown(analise_completa.get('texto_analise', row.get('Análise', '')))
                                        st.markdown("---")
                                        
                                        # Dados estruturados se existirem
                                        if analise_completa.get('dados_estruturados_json'):
                                            try:
                                                dados_estruturados = json.loads(analise_completa['dados_estruturados_json'])
                                                
                                                st.markdown("**📊 Dados Estruturados:**")
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
                                        st.markdown("**🤖 Resposta da IA:**")
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
                        with st.expander(f"📄 {row['Nome']} - Score: {row['Score']} - {'✅ Adequado' if row['Adequado'] else '❌ Não Adequado'}"):
                            st.markdown("**🤖 Resposta Completa da IA:**")
                            st.markdown(row['Análise'])
                            st.markdown("---")
                            st.markdown(f"**📊 Score:** {row['Score']}/100")
                            st.markdown(f"**📚 Matérias Restantes:** {row['Matérias Restantes']}")
                            st.markdown(f"**✅ Status:** {'Adequado para o curso' if row['Adequado'] else 'Precisa de melhorias'}")
