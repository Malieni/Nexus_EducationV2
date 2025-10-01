"""
Configurações do projeto Nexus Education
"""
import os

# Diretório base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Diretório de dados
DADOS_DIR = os.path.join(BASE_DIR, 'Dados')

# Criar diretório de dados se não existir
if not os.path.exists(DADOS_DIR):
    os.makedirs(DADOS_DIR)

# Caminhos dos arquivos de banco de dados
DATABASE_PATHS = {
    'professores': os.path.join(DADOS_DIR, 'professores.json'),
    'cursos': os.path.join(DADOS_DIR, 'cursos.json'),
    'disciplinas': os.path.join(DADOS_DIR, 'disciplinas.json'),
    'tags': os.path.join(DADOS_DIR, 'tags.json'),
    'ementas': os.path.join(DADOS_DIR, 'ementas.json'),
    'analises': os.path.join(DADOS_DIR, 'analises.json'),
    'professor_curso': os.path.join(DADOS_DIR, 'professor_curso.json'),
    'curso_tags': os.path.join(DADOS_DIR, 'curso_tags.json'),
    'cursos_disciplina': os.path.join(DADOS_DIR, 'cursos_disciplina.json'),
    'ementa_disciplina': os.path.join(DADOS_DIR, 'ementa_disciplina.json')
}

# Configurações de segurança
SECURITY_CONFIG = {
    'max_file_size': 5 * 1024 * 1024,  # 5MB
    'allowed_extensions': ['.pdf'],
    'max_files_per_upload': 5
}

# Configurações de ambiente
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG = ENVIRONMENT == 'development'

print(f"📁 Diretório de dados: {DADOS_DIR}")
print(f"🌍 Ambiente: {ENVIRONMENT}")
print(f"🐛 Debug: {DEBUG}")
