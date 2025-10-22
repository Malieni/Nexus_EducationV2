"""
Sistema de banco de dados Supabase para o projeto Nexus Education
"""
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
from supabase import Client

from core.config.supabase_config import supabase_config

class SupabaseDatabase:
    """Classe para operações com banco de dados Supabase"""
    
    def __init__(self):
        # Verificar se Supabase está configurado
        if supabase_config.offline_mode:
            self._init_tinydb_fallback()
            return
            
        try:
            self.client: Client = supabase_config.get_client()
            self.service_client: Client = supabase_config.get_client(use_service_role=True)
            
            if self.service_client:
                # Marcar que estamos usando Supabase
                self.use_supabase = True
            else:
                self._init_tinydb_fallback()
                return
                
        except Exception as e:
            self._init_tinydb_fallback()
    
    def _init_tinydb_fallback(self):
        """Inicializa TinyDB como fallback quando Supabase não está disponível"""
        try:
            from core.database.database_separado import AnalyseDatabaseSeparado
            self.tinydb = AnalyseDatabaseSeparado()
            self.use_supabase = False
        except Exception as e:
            print(f"❌ Erro ao inicializar TinyDB: {e}")
            raise
    
    # ==================== AUTENTICAÇÃO E LOGIN ====================
    
    def get_professor_by_email(self, email_educacional: str) -> Optional[Dict]:
        """Busca professor por email educacional para autenticação"""
        if not self.use_supabase:
            return self.tinydb.get_professor_by_email(email_educacional)
            
        try:
            response = self.client.table("professores").select("*").eq("email_educacional", email_educacional).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar professor por email: {e}")
            return None
    
    def get_professor(self, prontuario: str) -> Optional[Dict]:
        """Busca professor por prontuário"""
        if not self.use_supabase:
            return self.tinydb.get_professor(prontuario)
            
        try:
            response = self.client.table("professores").select("*").eq("prontuario", prontuario).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar professor: {e}")
            return None
    
    def authenticate_professor(self, email_educacional: str, senha: str) -> Optional[Dict]:
        """Autentica professor por email e senha"""
        try:
            # Se a senha já está com hash (vem do app), usar diretamente
            # Se não, fazer hash (para compatibilidade)
            if len(senha) == 64:  # SHA256 hash tem 64 caracteres
                senha_hash = senha
            else:
                senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            
            response = self.client.table("professores").select("*").eq("email_educacional", email_educacional).eq("senha", senha_hash).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return None
    
    def authenticate_professor_by_prontuario(self, prontuario: str, senha: str) -> Optional[Dict]:
        """Autentica professor por prontuário e senha"""
        try:
            # Buscar professor por prontuário
            response = self.client.table("professores").select("*").eq("prontuario", prontuario).execute()
            
            if not response.data:
                return None
            
            professor = response.data[0]
            senha_armazenada = professor['senha']
            
            # Verificar se a senha armazenada é bcrypt ou SHA256
            if senha_armazenada.startswith('$2b$'):
                # Senha armazenada em bcrypt
                import bcrypt
                if bcrypt.checkpw(senha.encode('utf-8'), senha_armazenada.encode('utf-8')):
                    return professor
            else:
                # Senha armazenada em SHA256
                senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                if senha_hash == senha_armazenada:
                    return professor
            
            return None
        except Exception as e:
            print(f"Erro na autenticação por prontuário: {e}")
            return None
    
    def verify_email_exists(self, email_educacional: str) -> bool:
        """Verifica se email já existe para cadastro"""
        try:
            response = self.client.table("professores").select("prontuario").eq("email_educacional", email_educacional).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Erro ao verificar email: {e}")
            return False
    
    def verify_prontuario_exists(self, prontuario: str) -> bool:
        """Verifica se prontuário já existe para cadastro"""
        try:
            response = self.client.table("professores").select("prontuario").eq("prontuario", prontuario).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Erro ao verificar prontuário: {e}")
            return False
    
    def create_professor(self, professor_data: Dict) -> Optional[Dict]:
        """Cria um novo professor"""
        try:
            response = self.client.table("professores").insert(professor_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar professor: {e}")
            return None
    
    # ==================== CONFIGURAÇÕES DE PERFIL ====================
    
    def get_professor_profile(self, prontuario: str) -> Optional[Dict]:
        """Busca dados completos do perfil do professor"""
        try:
            # Buscar dados do professor
            professor = self.get_professor(prontuario)
            if not professor:
                return None
            
            # Buscar cursos associados ao professor
            cursos = self.get_professor_courses(prontuario)
            professor['cursos'] = cursos
            
            return professor
        except Exception as e:
            print(f"Erro ao buscar perfil do professor: {e}")
            return None
    
    def get_professor_courses(self, prontuario: str) -> List[Dict]:
        """Busca todos os cursos associados ao professor"""
        if not self.use_supabase:
            return self.tinydb.get_professor_courses(prontuario)
            
        try:
            response = self.client.table("professor_curso").select("curso_fk").eq("prontuario_professor", prontuario).execute()
            curso_codes = [rel['curso_fk'] for rel in response.data]
            
            cursos = []
            for codigo in curso_codes:
                curso = self.get_curso_by_codigo(codigo)
                if curso:
                    cursos.append(curso)
            
            return cursos
        except Exception as e:
            print(f"Erro ao buscar cursos do professor: {e}")
            return []
    
    def get_professor_disciplines(self, prontuario: str) -> List[Dict]:
        """Busca todas as disciplinas ministradas pelo professor"""
        try:
            # Primeiro busca os cursos do professor
            cursos_professor = self.get_professor_courses(prontuario)
            
            disciplinas = []
            for curso in cursos_professor:
                # Para cada curso, busca as disciplinas
                curso_disciplinas = self.get_curso_disciplines(curso['codigo_curso'])
                for disciplina in curso_disciplinas:
                    disciplina['curso'] = curso['nome']
                    disciplinas.append(disciplina)
            
            return disciplinas
        except Exception as e:
            print(f"Erro ao buscar disciplinas do professor: {e}")
            return []
    
    # ==================== CURSOS E DISCIPLINAS ====================
    
    def get_curso_by_codigo(self, codigo_curso: str) -> Optional[Dict]:
        """Busca curso por código"""
        if not self.use_supabase:
            return self.tinydb.get_curso_by_codigo(codigo_curso)
            
        try:
            response = self.client.table("cursos").select("*").eq("codigo_curso", codigo_curso).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar curso: {e}")
            return None
    
    def get_all_cursos(self) -> List[Dict]:
        """Busca todos os cursos cadastrados"""
        try:
            response = self.client.table("cursos").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar cursos: {e}")
            return []
    
    def create_curso(self, curso_data: Dict) -> Optional[Dict]:
        """Cria um novo curso"""
        try:
            response = self.client.table("cursos").insert(curso_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar curso: {e}")
            return None
    
    def get_curso_disciplines(self, codigo_curso: str) -> List[Dict]:
        """Busca todas as disciplinas de um curso"""
        if not self.use_supabase:
            return self.tinydb.get_curso_disciplines(codigo_curso)
            
        try:
            response = self.client.table("cursos_disciplina").select("disciplina_fk").eq("curso_fk", codigo_curso).execute()
            disciplina_ids = [rel['disciplina_fk'] for rel in response.data]
            
            disciplinas = []
            for disciplina_id in disciplina_ids:
                disciplina = self.get_disciplina_by_id(disciplina_id)
                if disciplina:
                    disciplinas.append(disciplina)
            
            return disciplinas
        except Exception as e:
            print(f"Erro ao buscar disciplinas do curso: {e}")
            return []
    
    def get_disciplina_by_id(self, id_disciplina: str) -> Optional[Dict]:
        """Busca disciplina por ID"""
        try:
            response = self.client.table("disciplinas").select("*").eq("id_disciplina", id_disciplina).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar disciplina: {e}")
            return None
    
    def get_all_disciplinas(self) -> List[Dict]:
        """Busca todas as disciplinas cadastradas"""
        try:
            response = self.client.table("disciplinas").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar disciplinas: {e}")
            return []
    
    def create_disciplina(self, disciplina_data: Dict) -> Optional[Dict]:
        """Cria uma nova disciplina"""
        try:
            response = self.client.table("disciplinas").insert(disciplina_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar disciplina: {e}")
            return None
    
    def get_curso_tags(self, codigo_curso: str) -> List[Dict]:
        """Busca todas as tags de um curso"""
        try:
            response = self.client.table("curso_tags").select("tag_fk").eq("curso_fk", codigo_curso).execute()
            tag_ids = [rel['tag_fk'] for rel in response.data]
            
            tags = []
            for tag_id in tag_ids:
                tag = self.get_tag_by_id(tag_id)
                if tag:
                    tags.append(tag)
            
            return tags
        except Exception as e:
            print(f"Erro ao buscar tags do curso: {e}")
            return []
    
    def get_tag_by_id(self, id_tag: int) -> Optional[Dict]:
        """Busca tag por ID"""
        try:
            response = self.client.table("tags").select("*").eq("id_tag", id_tag).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar tag: {e}")
            return None
    
    def get_all_tags(self) -> List[Dict]:
        """Busca todas as tags cadastradas"""
        try:
            response = self.client.table("tags").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar tags: {e}")
            return []
    
    def create_tag(self, tag_data: Dict) -> Optional[Dict]:
        """Cria uma nova tag"""
        try:
            response = self.client.table("tags").insert(tag_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar tag: {e}")
            return None
    
    # ==================== EMENTAS ====================
    
    def get_ementa_by_id(self, id_ementa: int) -> Optional[Dict]:
        """Busca ementa por ID"""
        try:
            response = self.client.table("ementas").select("*").eq("id_ementa", id_ementa).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar ementa: {e}")
            return None
    
    def get_ementa_by_drive_id(self, drive_id: str) -> Optional[Dict]:
        """Busca ementa por drive_id"""
        try:
            response = self.client.table("ementas").select("*").eq("drive_id", drive_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar ementa por drive_id: {e}")
            return None
    
    def create_ementa(self, ementa_data: Dict) -> Optional[Dict]:
        """Cria uma nova ementa"""
        try:
            response = self.client.table("ementas").insert(ementa_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar ementa: {e}")
            return None
    
    def get_ementa_disciplines(self, id_ementa: int) -> List[Dict]:
        """Busca todas as disciplinas associadas a uma ementa"""
        try:
            response = self.client.table("ementa_disciplina").select("disciplina_fk").eq("ementa_fk", id_ementa).execute()
            disciplina_ids = [rel['disciplina_fk'] for rel in response.data]
            
            disciplinas = []
            for disciplina_id in disciplina_ids:
                disciplina = self.get_disciplina_by_id(disciplina_id)
                if disciplina:
                    disciplinas.append(disciplina)
            
            return disciplinas
        except Exception as e:
            print(f"Erro ao buscar disciplinas da ementa: {e}")
            return []
    
    def get_ementa_complete(self, id_ementa: int) -> Optional[Dict]:
        """Busca ementa completa com suas disciplinas"""
        try:
            ementa_data = self.get_ementa_by_id(id_ementa)
            if not ementa_data:
                return None
            
            ementa_data['disciplinas'] = self.get_ementa_disciplines(id_ementa)
            return ementa_data
        except Exception as e:
            print(f"Erro ao buscar ementa completa: {e}")
            return None
    
    # ==================== ANÁLISES ====================
    
    def get_analise_by_id(self, analise_id: int) -> Optional[Dict]:
        """Busca análise por ID"""
        try:
            response = self.client.table("analises").select("*").eq("analise_id", analise_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar análise: {e}")
            return None
    
    def get_analises_by_ementa(self, ementa_fk: int) -> List[Dict]:
        """Busca todas as análises de uma ementa"""
        try:
            response = self.client.table("analises").select("*").eq("ementa_fk", ementa_fk).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar análises da ementa: {e}")
            return []
    
    def get_analises_by_professor(self, professor_id: str) -> List[Dict]:
        """Busca todas as análises feitas por um professor"""
        try:
            response = self.client.table("analises").select("*").eq("professor_id", professor_id).execute()
            print(f"Buscando análises para professor {professor_id}: {len(response.data)} encontradas")
            return response.data
        except Exception as e:
            print(f"Erro ao buscar análises do professor: {e}")
            return []
    
    def get_all_analises(self) -> List[Dict]:
        """Busca todas as análises (para debug)"""
        try:
            response = self.service_client.table("analises").select("*").execute()
            print(f"Total de análises no banco: {len(response.data)}")
            for analise in response.data:
                print(f"  - ID: {analise.get('analise_id')}, Professor: {analise.get('professor_id')}, Aluno: {analise.get('nome_aluno')}")
            return response.data
        except Exception as e:
            print(f"Erro ao buscar todas as análises: {e}")
            return []
    
    def get_analises_by_curso(self, codigo_curso: str) -> List[Dict]:
        """Busca todas as análises de um curso específico"""
        try:
            # Buscar professores do curso
            response = self.client.table("professor_curso").select("prontuario_professor").eq("curso_fk", codigo_curso).execute()
            professor_ids = [rel['prontuario_professor'] for rel in response.data]
            
            # Buscar análises dos professores
            all_analyses = []
            for professor_id in professor_ids:
                analyses = self.get_analises_by_professor(professor_id)
                all_analyses.extend(analyses)
            
            return all_analyses
        except Exception as e:
            print(f"Erro ao buscar análises do curso: {e}")
            return []
    
    def get_analises_by_curso_and_professor(self, codigo_curso: str, professor_id: str) -> List[Dict]:
        """Busca análises de um curso específico feitas por um professor específico"""
        try:
            print(f"Buscando análises para professor {professor_id} no curso {codigo_curso}")
            
            # Primeiro verificar se o professor leciona o curso
            curso_check = self.client.table("professor_curso").select("pc_id").eq("prontuario_professor", professor_id).eq("curso_fk", codigo_curso).execute()
            
            if not curso_check.data:
                print(f"Professor {professor_id} não leciona o curso {codigo_curso}")
                return []
            
            # Buscar análises do professor específico
            response = self.client.table("analises").select("*").eq("professor_id", professor_id).execute()
            
            if not response.data:
                print(f"Nenhuma análise encontrada para o professor {professor_id}")
                return []
            
            print(f"Encontradas {len(response.data)} análises para o professor {professor_id}")
            
            # Como o professor leciona o curso, todas as suas análises são válidas para este curso
            # (assumindo que ele só analisa ementas de cursos que leciona)
            print(f"Retornando {len(response.data)} análises para o curso {codigo_curso}")
            return response.data
            
        except Exception as e:
            print(f"Erro ao buscar análises do curso por professor: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []
    
    # ==================== MÉTODOS ANALISE_CURSO ====================
    
    def create_analise_curso_relacionamento(self, analise_id: int, curso_codigo: str) -> bool:
        """Cria relacionamento entre análise e curso"""
        try:
            print(f"\n{'='*60}")
            print(f"🔗 CRIANDO RELACIONAMENTO ANÁLISE-CURSO")
            print(f"{'='*60}")
            print(f"Análise ID: {analise_id}")
            print(f"Curso Código: {curso_codigo}")
            
            relacionamento_data = {
                'analise_fk': analise_id,
                'curso_fk': curso_codigo
            }
            
            print(f"Dados do relacionamento: {relacionamento_data}")
            print(f"Usando service_client: {self.service_client is not None}")
            
            # Usar service client para operações de escrita
            response = self.service_client.table("analise_curso").insert(relacionamento_data).execute()
            
            print(f"Status da resposta: {response.status_code if hasattr(response, 'status_code') else 'N/A'}")
            print(f"Dados retornados: {response.data}")
            
            if response.data and len(response.data) > 0:
                print(f"✅ Relacionamento criado com sucesso!")
                print(f"   ID do relacionamento: {response.data[0].get('id', 'N/A')}")
                print(f"{'='*60}\n")
                return True
            else:
                print(f"❌ Erro: Nenhum dado retornado")
                if hasattr(response, 'error') and response.error:
                    print(f"   Erro do Supabase: {response.error}")
                print(f"{'='*60}\n")
                return False
                
        except Exception as e:
            print(f"❌ ERRO ao criar relacionamento: {e}")
            import traceback
            print(f"Traceback completo:")
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            return False
    
    def get_analises_by_curso_usando_relacionamento(self, curso_codigo: str) -> List[Dict]:
        """Busca análises de um curso usando a tabela de relacionamento
        
        ATENÇÃO: Este método retorna TODAS as análises do curso, independentemente do professor.
        Para manter a privacidade dos dados, prefira usar get_analises_by_curso_and_professor_usando_relacionamento.
        """
        try:
            print(f"Buscando análises do curso {curso_codigo} usando relacionamento")
            
            # Query com JOIN usando a tabela de relacionamento
            # Especificar qual relacionamento usar com ementas para evitar ambiguidade
            response = self.client.table("analises").select(
                """
                *,
                analise_curso!inner(
                    curso_fk
                ),
                ementas!analises_ementa_fk_fkey(
                    file_name,
                    data_upload
                )
                """
            ).eq("analise_curso.curso_fk", curso_codigo).execute()
            
            if response.data:
                print(f"Encontradas {len(response.data)} análises para o curso {curso_codigo}")
                return response.data
            else:
                print(f"Nenhuma análise encontrada para o curso {curso_codigo}")
                return []
                
        except Exception as e:
            print(f"Erro ao buscar análises por curso usando relacionamento: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_analises_by_curso_and_professor_usando_relacionamento(self, curso_codigo: str, professor_id: str) -> List[Dict]:
        """Busca análises de um curso específico feitas por um professor usando relacionamento
        
        IMPORTANTE: Este método garante que apenas as análises do professor específico sejam retornadas.
        Use este método ao invés de get_analises_by_curso_usando_relacionamento para manter a privacidade dos dados.
        
        SEGURANÇA: Este método inclui validação de acesso do professor ao curso.
        """
        try:
            print(f"\n{'='*60}")
            print(f"🔍 BUSCANDO ANÁLISES")
            print(f"{'='*60}")
            print(f"Professor ID: {professor_id}")
            print(f"Código do Curso: {curso_codigo}")
            print(f"Usando tabela de relacionamento: analise_curso")
            
            # VALIDAÇÃO DE SEGURANÇA: Verificar se o professor tem acesso a este curso
            professor_cursos = self.get_professor_courses(professor_id)
            curso_codes = [curso['codigo_curso'] for curso in professor_cursos]
            
            if curso_codigo not in curso_codes:
                print(f"🚫 ACESSO NEGADO: Professor {professor_id} não tem permissão para acessar curso {curso_codigo}")
                print(f"📋 Cursos permitidos: {curso_codes}")
                return []
            
            print(f"✅ ACESSO AUTORIZADO: Professor tem permissão para acessar curso {curso_codigo}")
            
            # Query com JOIN usando a tabela de relacionamento
            # Especificar qual relacionamento usar com ementas para evitar ambiguidade
            response = self.client.table("analises").select(
                """
                *,
                analise_curso!inner(
                    curso_fk
                ),
                ementas!analises_ementa_fk_fkey(
                    file_name,
                    data_upload
                )
                """
            ).eq("analise_curso.curso_fk", curso_codigo).eq("professor_id", professor_id).execute()
            
            print(f"Status da resposta: {response.status_code if hasattr(response, 'status_code') else 'N/A'}")
            print(f"Dados retornados: {len(response.data) if response.data else 0} registros")
            
            if response.data:
                print(f"✅ Encontradas {len(response.data)} análises")
                for i, analise in enumerate(response.data[:3]):  # Mostrar primeiras 3
                    print(f"  {i+1}. ID: {analise.get('analise_id')} - Aluno: {analise.get('nome_aluno', 'N/A')}")
                print(f"{'='*60}\n")
                return response.data
            else:
                print(f"⚠️ Nenhuma análise encontrada")
                print(f"{'='*60}\n")
                return []
                
        except Exception as e:
            print(f"❌ ERRO ao buscar análises: {e}")
            import traceback
            print(f"Traceback completo:")
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            return []
    
    def get_cursos_com_analises_do_professor(self, professor_id: str) -> List[Dict]:
        """Lista todos os cursos que têm análises feitas por um professor"""
        try:
            print(f"Buscando cursos com análises do professor {professor_id}")
            
            # Query para buscar cursos distintos que têm análises do professor
            response = self.client.table("analise_curso").select(
                """
                curso_fk,
                cursos!inner(
                    codigo_curso,
                    nome,
                    descricao_curso
                ),
                analises!inner(
                    analise_id,
                    professor_id
                )
                """
            ).eq("analises.professor_id", professor_id).execute()
            
            if response.data:
                # Agrupar por curso e contar análises
                cursos_dict = {}
                for item in response.data:
                    curso_info = item['cursos']
                    curso_codigo = curso_info['codigo_curso']
                    
                    if curso_codigo not in cursos_dict:
                        cursos_dict[curso_codigo] = {
                            'codigo_curso': curso_codigo,
                            'nome': curso_info['nome'],
                            'descricao_curso': curso_info['descricao_curso'],
                            'total_analises': 0
                        }
                    cursos_dict[curso_codigo]['total_analises'] += 1
                
                cursos_lista = list(cursos_dict.values())
                print(f"Encontrados {len(cursos_lista)} cursos com análises do professor {professor_id}")
                return cursos_lista
            else:
                print(f"Nenhum curso com análises encontrado para o professor {professor_id}")
                return []
                
        except Exception as e:
            print(f"Erro ao buscar cursos com análises do professor: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_estatisticas_por_curso_do_professor(self, professor_id: str) -> List[Dict]:
        """Obtém estatísticas de análises por curso para um professor"""
        try:
            print(f"Buscando estatísticas por curso do professor {professor_id}")
            
            # Query para buscar análises agrupadas por curso
            response = self.client.table("analise_curso").select(
                """
                curso_fk,
                cursos!inner(
                    codigo_curso,
                    nome
                ),
                analises!inner(
                    analise_id,
                    score,
                    adequado,
                    professor_id
                )
                """
            ).eq("analises.professor_id", professor_id).execute()
            
            if response.data:
                # Agrupar por curso e calcular estatísticas
                cursos_dict = {}
                for item in response.data:
                    curso_info = item['cursos']
                    analise_info = item['analises']
                    curso_codigo = curso_info['codigo_curso']
                    
                    if curso_codigo not in cursos_dict:
                        cursos_dict[curso_codigo] = {
                            'codigo_curso': curso_codigo,
                            'nome': curso_info['nome'],
                            'total_analises': 0,
                            'scores': [],
                            'adequadas': 0,
                            'inadequadas': 0
                        }
                    
                    cursos_dict[curso_codigo]['total_analises'] += 1
                    cursos_dict[curso_codigo]['scores'].append(analise_info['score'])
                    
                    if analise_info['adequado']:
                        cursos_dict[curso_codigo]['adequadas'] += 1
                    else:
                        cursos_dict[curso_codigo]['inadequadas'] += 1
                
                # Calcular estatísticas finais
                estatisticas = []
                for curso_data in cursos_dict.values():
                    scores = curso_data['scores']
                    estatisticas.append({
                        'codigo_curso': curso_data['codigo_curso'],
                        'nome': curso_data['nome'],
                        'total_analises': curso_data['total_analises'],
                        'media_score': round(sum(scores) / len(scores), 2) if scores else 0,
                        'score_maximo': max(scores) if scores else 0,
                        'score_minimo': min(scores) if scores else 0,
                        'adequadas': curso_data['adequadas'],
                        'inadequadas': curso_data['inadequadas'],
                        'taxa_adequacao': f"{(curso_data['adequadas']/curso_data['total_analises'])*100:.1f}%" if curso_data['total_analises'] > 0 else "0%"
                    })
                
                # Ordenar por total de análises (decrescente)
                estatisticas.sort(key=lambda x: x['total_analises'], reverse=True)
                
                print(f"Estatísticas calculadas para {len(estatisticas)} cursos")
                return estatisticas
            else:
                print(f"Nenhuma estatística encontrada para o professor {professor_id}")
                return []
                
        except Exception as e:
            print(f"Erro ao buscar estatísticas por curso: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []
    
    def test_analises_table(self) -> bool:
        """Testa se a tabela analises existe e está acessível"""
        try:
            # Tentar buscar dados da tabela analises
            response = self.service_client.table("analises").select("*").limit(1).execute()
            print("✅ Tabela 'analises' existe e está acessível")
            return True
        except Exception as e:
            print(f"❌ Erro ao acessar tabela 'analises': {e}")
            # Verificar se é erro de tabela não encontrada
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                print("🔧 Tabela 'analises' não existe. Criando...")
                return self.create_analises_table()
            return False
    
    def create_analises_table(self) -> bool:
        """Cria a tabela analises se ela não existir"""
        try:
            # SQL para criar a tabela analises
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS analises (
                analise_id SERIAL PRIMARY KEY,
                nome_aluno VARCHAR(255) NOT NULL,
                ementa_fk INTEGER NOT NULL,
                adequado BOOLEAN NOT NULL,
                score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
                texto_analise TEXT NOT NULL,
                materias_restantes TEXT,
                professor_id VARCHAR(9) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            # Executar SQL usando RPC
            response = self.service_client.rpc('exec_sql', {'sql': create_table_sql}).execute()
            print("✅ Tabela 'analises' criada com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar tabela 'analises': {e}")
            # Tentar método alternativo - inserir um registro de teste
            try:
                test_data = {
                    'nome_aluno': 'Teste',
                    'ementa_fk': 1,
                    'adequado': True,
                    'score': 80,
                    'texto_analise': 'Teste',
                    'materias_restantes': 'Nenhuma',
                    'professor_id': 'TEST12345'
                }
                response = self.service_client.table("analises").insert(test_data).execute()
                print("✅ Tabela 'analises' existe (teste de inserção)")
                return True
            except Exception as e2:
                print(f"❌ Tabela 'analises' não existe e não pode ser criada: {e2}")
                return False
    
    def create_analise(self, analise_data: Dict, curso_codigo: str = None) -> Optional[Dict]:
        """Cria uma nova análise e opcionalmente vincula a um curso"""
        try:
            # Se não estamos usando Supabase, usar TinyDB
            if not self.use_supabase:
                return self._create_analise_tinydb(analise_data, curso_codigo)
            
            # Verificar se service_client está disponível
            if not self.service_client:
                print("❌ Service client não está disponível!")
                return None
            
            # Testar se a tabela existe
            if not self.test_analises_table():
                print("❌ Tabela 'analises' não existe ou não está acessível")
                return None
            
            # Validar dados obrigatórios
            required_fields = ['nome_aluno', 'ementa_fk', 'adequado', 'score', 'texto_analise', 'professor_id']
            for field in required_fields:
                if field not in analise_data:
                    print(f"❌ Campo obrigatório '{field}' não encontrado nos dados")
                    print(f"🔍 [DEBUG] Campos disponíveis: {list(analise_data.keys())}")
                    return None
            
            print(f"🔍 [DEBUG] Todos os campos obrigatórios estão presentes")
            
            # Limpar dados antes de inserir (remover campos None ou vazios)
            clean_data = {k: v for k, v in analise_data.items() if v is not None and v != ""}
            print(f"🔍 [DEBUG] Dados limpos para inserção: {clean_data}")
            
            # Usar service client para operações de escrita
            print(f"🔍 [DEBUG] Enviando requisição para Supabase...")
            response = self.service_client.table("analises").insert(clean_data).execute()
            
            print(f"🔍 [DEBUG] Resposta do Supabase: {response}")
            print(f"🔍 [DEBUG] Dados retornados: {response.data}")
            print(f"🔍 [DEBUG] Erro (se houver): {getattr(response, 'error', None)}")
            
            if response.data and len(response.data) > 0:
                analise_created = response.data[0]
                print(f"✅ Análise criada com sucesso: {analise_created}")
                
                # Se foi fornecido um código de curso, criar relacionamento
                if curso_codigo and analise_created.get('analise_id'):
                    print(f"🔍 [DEBUG] Criando relacionamento com curso {curso_codigo}")
                    relacionamento_success = self.create_analise_curso_relacionamento(analise_created['analise_id'], curso_codigo)
                    if relacionamento_success:
                        print(f"✅ Relacionamento criado com sucesso")
                    else:
                        print(f"⚠️ Falha ao criar relacionamento, mas análise foi salva")
                
                return analise_created
            else:
                print("❌ Nenhum dado retornado na criação da análise")
                print(f"🔍 [DEBUG] Response completa: {response}")
                if hasattr(response, 'error') and response.error:
                    print(f"❌ Erro do Supabase: {response.error}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao criar análise: {e}")
            import traceback
            print(f"🔍 [DEBUG] Traceback completo: {traceback.format_exc()}")
            return None
    
    def _create_analise_tinydb(self, analise_data: Dict, curso_codigo: str = None) -> Optional[Dict]:
        """Cria análise usando TinyDB como fallback"""
        try:
            # Adicionar campo prontuario_professor para compatibilidade com TinyDB
            if 'professor_id' in analise_data:
                analise_data['prontuario_professor'] = analise_data['professor_id']
            
            # Salvar análise no TinyDB
            analise_id = self.tinydb.analise.insert(analise_data)
            
            if analise_id:
                analise_data['analise_id'] = analise_id
                return analise_data
            else:
                return None
                
        except Exception as e:
            print(f"❌ Erro ao salvar análise no TinyDB: {e}")
            return None
    
    def get_analise_complete(self, analise_id: int) -> Optional[Dict]:
        """Busca análise completa com dados da ementa e professor"""
        try:
            analise_data = self.get_analise_by_id(analise_id)
            if not analise_data:
                return None
            
            # Buscar dados da ementa
            ementa_data = self.get_ementa_complete(analise_data['ementa_fk'])
            analise_data['ementa'] = ementa_data
            
            # Buscar dados do professor
            professor_data = self.get_professor(analise_data['professor_id'])
            analise_data['professor'] = professor_data
            
            return analise_data
        except Exception as e:
            print(f"Erro ao buscar análise completa: {e}")
            return None
    
    # ==================== RELACIONAMENTOS ====================
    
    def create_professor_curso_relationship(self, prontuario_professor: str, codigo_curso: str) -> bool:
        """Cria relacionamento entre professor e curso
        
        Retorna:
            bool: True se criou com sucesso, False se já existia ou houve erro
        """
        try:
            # Verificar se o relacionamento já existe
            existing = self.client.table("professor_curso").select("*").eq(
                "prontuario_professor", prontuario_professor
            ).eq("curso_fk", codigo_curso).execute()
            
            if existing.data:
                print(f"⚠️ Relacionamento já existe: Professor {prontuario_professor} já está associado ao curso {codigo_curso}")
                return False  # Relacionamento já existe, mas não é um erro
            
            # Criar novo relacionamento
            response = self.client.table("professor_curso").insert({
                "prontuario_professor": prontuario_professor,
                "curso_fk": codigo_curso
            }).execute()
            
            if response.data:
                print(f"✅ Relacionamento criado: Professor {prontuario_professor} associado ao curso {codigo_curso}")
                return True
            else:
                print(f"❌ Falha ao criar relacionamento: {prontuario_professor} -> {codigo_curso}")
                return False
                
        except Exception as e:
            print(f"Erro ao criar relacionamento professor-curso: {e}")
            return False
    
    def create_curso_disciplina_relationship(self, codigo_curso: str, id_disciplina: str) -> bool:
        """Cria relacionamento entre curso e disciplina"""
        try:
            response = self.client.table("cursos_disciplina").insert({
                "curso_fk": codigo_curso,
                "disciplina_fk": id_disciplina
            }).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Erro ao criar relacionamento curso-disciplina: {e}")
            return False
    
    def create_ementa_disciplina_relationship(self, id_ementa: int, id_disciplina: str) -> bool:
        """Cria relacionamento entre ementa e disciplina"""
        try:
            response = self.client.table("ementa_disciplina").insert({
                "ementa_fk": id_ementa,
                "disciplina_fk": id_disciplina
            }).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Erro ao criar relacionamento ementa-disciplina: {e}")
            return False
    
    def create_curso_tag_relationship(self, codigo_curso: str, id_tag: int) -> bool:
        """Cria relacionamento entre curso e tag"""
        try:
            response = self.client.table("curso_tags").insert({
                "curso_fk": codigo_curso,
                "tag_fk": id_tag
            }).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Erro ao criar relacionamento curso-tag: {e}")
            return False
    
    # ==================== MÉTODOS DE DELETE ====================
    
    def delete_analise(self, analise_id: int, professor_id: str) -> bool:
        """Deleta uma análise específica, verificando se o professor tem permissão"""
        try:
            # Verificar se a análise existe e pertence ao professor
            response = self.client.table("analises").select("*").eq("analise_id", analise_id).eq("professor_id", professor_id).execute()
            
            if not response.data:
                return False
            
            # Deletar a análise
            delete_response = self.client.table("analises").delete().eq("analise_id", analise_id).execute()
            return len(delete_response.data) > 0
        except Exception as e:
            print(f"Erro ao deletar análise: {e}")
            return False
    
    def delete_ementa(self, id_ementa: int, professor_id: str) -> bool:
        """Deleta uma ementa e todas suas análises relacionadas"""
        try:
            # Verificar se a ementa existe e pertence ao professor
            response = self.client.table("ementas").select("*").eq("id_ementa", id_ementa).eq("professor_id", professor_id).execute()
            
            if not response.data:
                return False
            
            # Deletar análises relacionadas
            self.client.table("analises").delete().eq("ementa_fk", id_ementa).execute()
            
            # Deletar relacionamentos ementa_disciplina
            self.client.table("ementa_disciplina").delete().eq("ementa_fk", id_ementa).execute()
            
            # Deletar a ementa
            delete_response = self.client.table("ementas").delete().eq("id_ementa", id_ementa).execute()
            return len(delete_response.data) > 0
        except Exception as e:
            print(f"Erro ao deletar ementa: {e}")
            return False
    
    # ==================== FILTRAGEM E BUSCA ====================
    
    def search_ementas_by_name(self, nome_disciplina: str) -> List[Dict]:
        """Busca ementas por nome da disciplina"""
        try:
            # Buscar disciplinas que contenham o nome
            response = self.client.table("disciplinas").select("id_disciplina").ilike("nome", f"%{nome_disciplina}%").execute()
            disciplina_ids = [disc['id_disciplina'] for disc in response.data]
            
            ementas = []
            for disciplina_id in disciplina_ids:
                ementas_disciplina = self.filter_ementas_by_disciplina(disciplina_id)
                ementas.extend(ementas_disciplina)
            
            # Remover duplicatas
            seen = set()
            unique_ementas = []
            for ementa in ementas:
                if ementa['id_ementa'] not in seen:
                    seen.add(ementa['id_ementa'])
                    unique_ementas.append(ementa)
            
            return unique_ementas
        except Exception as e:
            print(f"Erro ao buscar ementas por nome: {e}")
            return []
    
    def filter_ementas_by_disciplina(self, id_disciplina: str) -> List[Dict]:
        """Filtra ementas por disciplina"""
        try:
            response = self.client.table("ementa_disciplina").select("ementa_fk").eq("disciplina_fk", id_disciplina).execute()
            ementa_ids = [rel['ementa_fk'] for rel in response.data]
            
            ementas = []
            for ementa_id in ementa_ids:
                ementa_data = self.get_ementa_complete(ementa_id)
                if ementa_data:
                    ementas.append(ementa_data)
            
            return ementas
        except Exception as e:
            print(f"Erro ao filtrar ementas por disciplina: {e}")
            return []
    
    def get_recent_ementas(self, limit: int = 10) -> List[Dict]:
        """Busca ementas mais recentes"""
        try:
            response = self.client.table("ementas").select("*").order("data_upload", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar ementas recentes: {e}")
            return []
