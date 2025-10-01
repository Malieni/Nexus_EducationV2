from tinydb import TinyDB, Query
from typing import List, Dict, Optional
from datetime import datetime

class AnalyseDatabase(TinyDB):
    def __init__(self, db_path='db.json'):
        super().__init__(db_path)
        
        # Tabelas principais
        self.professor = self.table('professor')
        self.cursos = self.table('cursos')
        self.disciplinas = self.table('disciplinas')
        self.tags = self.table('tags')
        self.ementa = self.table('ementa')
        self.analise = self.table('analise')
        
        # Tabelas de relacionamento (N:N)
        self.professor_curso = self.table('professor_curso')
        self.curso_tags = self.table('curso_tags')
        self.cursos_disciplina = self.table('cursos_disciplina')
        self.ementa_disciplina = self.table('ementa_disciplina')
    
    # ==================== AUTENTICAÇÃO E LOGIN ====================
    
    def get_professor_by_email(self, email_educacional: str) -> Optional[Dict]:
        """Busca professor por email educacional para autenticação"""
        professor = Query()
        result = self.professor.search(professor.email_educacional == email_educacional)
        return result[0] if result else None
    
    def get_professor(self, prontuario: str) -> Optional[Dict]:
        """Busca professor por prontuário"""
        professor = Query()
        result = self.professor.search(professor.prontuario == prontuario)
        return result[0] if result else None
    
    def authenticate_professor(self, email_educacional: str, senha: str) -> Optional[Dict]:
        """Autentica professor por email e senha"""
        professor = Query()
        result = self.professor.search(
            (professor.email_educacional == email_educacional) & 
            (professor.senha == senha)
        )
        return result[0] if result else None
    
    def verify_email_exists(self, email_educacional: str) -> bool:
        """Verifica se email já existe para cadastro"""
        professor = Query()
        result = self.professor.search(professor.email_educacional == email_educacional)
        return len(result) > 0
    
    def verify_prontuario_exists(self, prontuario: str) -> bool:
        """Verifica se prontuário já existe para cadastro"""
        professor = Query()
        result = self.professor.search(professor.prontuario == prontuario)
        return len(result) > 0
    
    # ==================== CONFIGURAÇÕES DE PERFIL ====================
    
    def get_professor_profile(self, prontuario: str) -> Optional[Dict]:
        """Busca dados completos do perfil do professor"""
        professor = Query()
        professor_data = self.professor.search(professor.prontuario == prontuario)
        if not professor_data:
            return None
        
        # Buscar cursos associados ao professor
        professor_curso = Query()
        cursos_ids = self.professor_curso.search(professor_curso.prontuario_professor == prontuario)
        
        cursos = []
        for curso_rel in cursos_ids:
            curso_data = self.get_curso_by_codigo(curso_rel['curso_fk'])
            if curso_data:
                cursos.append(curso_data)
        
        professor_data[0]['cursos'] = cursos
        return professor_data[0]
    
    def get_professor_courses(self, prontuario: str) -> List[Dict]:
        """Busca todos os cursos associados ao professor"""
        professor_curso = Query()
        cursos_ids = self.professor_curso.search(professor_curso.prontuario_professor == prontuario)
        
        cursos = []
        for curso_rel in cursos_ids:
            curso_data = self.get_curso_by_codigo(curso_rel['curso_fk'])
            if curso_data:
                cursos.append(curso_data)
        
        return cursos
    
    def get_professor_disciplines(self, prontuario: str) -> List[Dict]:
        """Busca todas as disciplinas ministradas pelo professor"""
        # Primeiro busca os cursos do professor
        cursos_professor = self.get_professor_courses(prontuario)
        
        disciplinas = []
        for curso in cursos_professor:
            # Para cada curso, busca as disciplinas
            curso_disciplina = Query()
            disciplina_ids = self.cursos_disciplina.search(
                curso_disciplina.curso_fk == curso['codigo_curso']
            )
            
            for disc_rel in disciplina_ids:
                disciplina_data = self.get_disciplina_by_id(disc_rel['disciplina_fk'])
                if disciplina_data:
                    disciplina_data['curso'] = curso['nome']
                    disciplinas.append(disciplina_data)
        
        return disciplinas
    
    # ==================== CURSOS E DISCIPLINAS ====================
    
    def get_curso_by_codigo(self, codigo_curso: str) -> Optional[Dict]:
        """Busca curso por código"""
        curso = Query()
        result = self.cursos.search(curso.codigo_curso == codigo_curso)
        return result[0] if result else None
    
    def get_all_cursos(self) -> List[Dict]:
        """Busca todos os cursos cadastrados"""
        return self.cursos.all()
    
    def get_curso_disciplines(self, codigo_curso: str) -> List[Dict]:
        """Busca todas as disciplinas de um curso"""
        curso_disciplina = Query()
        disciplina_ids = self.cursos_disciplina.search(
            curso_disciplina.curso_fk == codigo_curso
        )
        
        disciplinas = []
        for disc_rel in disciplina_ids:
            disciplina_data = self.get_disciplina_by_id(disc_rel['disciplina_fk'])
            if disciplina_data:
                disciplinas.append(disciplina_data)
        
        return disciplinas
    
    def get_disciplina_by_id(self, id_disciplina: str) -> Optional[Dict]:
        """Busca disciplina por ID"""
        disciplina = Query()
        result = self.disciplinas.search(disciplina.id_disciplina == id_disciplina)
        return result[0] if result else None
    
    def get_all_disciplinas(self) -> List[Dict]:
        """Busca todas as disciplinas cadastradas"""
        return self.disciplinas.all()
    
    def get_curso_tags(self, codigo_curso: str) -> List[Dict]:
        """Busca todas as tags de um curso"""
        curso_tags = Query()
        tag_ids = self.curso_tags.search(curso_tags.curso_fk == codigo_curso)
        
        tags = []
        for tag_rel in tag_ids:
            tag_data = self.get_tag_by_id(tag_rel['tag_fk'])
            if tag_data:
                tags.append(tag_data)
        
        return tags
    
    def get_tag_by_id(self, id_tag: int) -> Optional[Dict]:
        """Busca tag por ID"""
        tag = Query()
        result = self.tags.search(tag.id_tag == id_tag)
        return result[0] if result else None
    
    def get_all_tags(self) -> List[Dict]:
        """Busca todas as tags cadastradas"""
        return self.tags.all()
    
    # ==================== EMENTAS ====================
    
    def get_ementa_by_id(self, id_ementa: int) -> Optional[Dict]:
        """Busca ementa por ID"""
        ementa = Query()
        result = self.ementa.search(ementa.id_ementa == id_ementa)
        return result[0] if result else None
    
    def get_ementa_by_drive_id(self, drive_id: str) -> Optional[Dict]:
        """Busca ementa por drive_id"""
        ementa = Query()
        result = self.ementa.search(ementa.drive_id == drive_id)
        return result[0] if result else None
    
    def get_ementa_disciplines(self, id_ementa: int) -> List[Dict]:
        """Busca todas as disciplinas associadas a uma ementa"""
        ementa_disciplina = Query()
        disciplina_ids = self.ementa_disciplina.search(
            ementa_disciplina.ementa_fk == id_ementa
        )
        
        disciplinas = []
        for disc_rel in disciplina_ids:
            disciplina_data = self.get_disciplina_by_id(disc_rel['disciplina_fk'])
            if disciplina_data:
                disciplinas.append(disciplina_data)
        
        return disciplinas
    
    def get_ementa_complete(self, id_ementa: int) -> Optional[Dict]:
        """Busca ementa completa com suas disciplinas"""
        ementa_data = self.get_ementa_by_id(id_ementa)
        if not ementa_data:
            return None
        
        ementa_data['disciplinas'] = self.get_ementa_disciplines(id_ementa)
        return ementa_data
    
    # ==================== ANÁLISES ====================
    
    def get_analise_by_id(self, analise_id: int) -> Optional[Dict]:
        """Busca análise por ID"""
        analise = Query()
        result = self.analise.search(analise.analise_id == analise_id)
        return result[0] if result else None
    
    def get_analises_by_ementa(self, ementa_fk: int) -> List[Dict]:
        """Busca todas as análises de uma ementa"""
        analise = Query()
        return self.analise.search(analise.ementa_fk == ementa_fk)
    
    def get_analises_by_professor(self, prontuario_professor: str) -> List[Dict]:
        """Busca todas as análises feitas por um professor"""
        analise = Query()
        return self.analise.search(analise.prontuario_professor == prontuario_professor)
    
    def get_analise_complete(self, analise_id: int) -> Optional[Dict]:
        """Busca análise completa com dados da ementa e professor"""
        analise_data = self.get_analise_by_id(analise_id)
        if not analise_data:
            return None
        
        # Buscar dados da ementa
        ementa_data = self.get_ementa_complete(analise_data['ementa_fk'])
        analise_data['ementa'] = ementa_data
        
        # Buscar dados do professor
        professor_data = self.get_professor(analise_data['prontuario_professor'])
        analise_data['professor'] = professor_data
        
        return analise_data
    
    # ==================== HISTÓRICO ====================
    
    def get_professor_history(self, prontuario_professor: str) -> List[Dict]:
        """Busca histórico completo de análises do professor"""
        analises = self.get_analises_by_professor(prontuario_professor)
        
        historico = []
        for analise in analises:
            analise_completa = self.get_analise_complete(analise['analise_id'])
            if analise_completa:
                historico.append(analise_completa)
        
        # Ordenar por data (mais recente primeiro)
        return sorted(historico, key=lambda x: x.get('data_analise', ''), reverse=True)
    
    def get_ementa_history(self, ementa_fk: int) -> List[Dict]:
        """Busca histórico de análises de uma ementa específica"""
        analises = self.get_analises_by_ementa(ementa_fk)
        
        historico = []
        for analise in analises:
            analise_completa = self.get_analise_complete(analise['analise_id'])
            if analise_completa:
                historico.append(analise_completa)
        
        return sorted(historico, key=lambda x: x.get('data_analise', ''), reverse=True)
    
    # ==================== FILTRAGEM AMPLA ====================
    
    def filter_ementas_by_curso(self, codigo_curso: str) -> List[Dict]:
        """Filtra ementas por curso"""
        # Buscar disciplinas do curso
        disciplinas_curso = self.get_curso_disciplines(codigo_curso)
        disciplina_ids = [disc['id_disciplina'] for disc in disciplinas_curso]
        
        # Buscar ementas que contenham essas disciplinas
        ementa_disciplina = Query()
        ementa_ids = []
        for disciplina_id in disciplina_ids:
            resultados = self.ementa_disciplina.search(
                ementa_disciplina.disciplina_fk == disciplina_id
            )
            for resultado in resultados:
                if resultado['ementa_fk'] not in ementa_ids:
                    ementa_ids.append(resultado['ementa_fk'])
        
        # Retornar ementas completas
        ementas = []
        for ementa_id in ementa_ids:
            ementa_data = self.get_ementa_complete(ementa_id)
            if ementa_data:
                ementas.append(ementa_data)
        
        return ementas
    
    def filter_ementas_by_disciplina(self, id_disciplina: str) -> List[Dict]:
        """Filtra ementas por disciplina"""
        ementa_disciplina = Query()
        ementa_ids = self.ementa_disciplina.search(
            ementa_disciplina.disciplina_fk == id_disciplina
        )
        
        ementas = []
        for rel in ementa_ids:
            ementa_data = self.get_ementa_complete(rel['ementa_fk'])
            if ementa_data:
                ementas.append(ementa_data)
        
        return ementas
    
    def filter_ementas_by_tag(self, tag_id: int) -> List[Dict]:
        """Filtra ementas por tag (através dos cursos)"""
        # Buscar cursos com essa tag
        curso_tags = Query()
        curso_ids = self.curso_tags.search(curso_tags.tag_fk == tag_id)
        
        ementas = []
        for curso_rel in curso_ids:
            ementas_curso = self.filter_ementas_by_curso(curso_rel['curso_fk'])
            ementas.extend(ementas_curso)
        
        # Remover duplicatas
        seen = set()
        unique_ementas = []
        for ementa in ementas:
            if ementa['id_ementa'] not in seen:
                seen.add(ementa['id_ementa'])
                unique_ementas.append(ementa)
        
        return unique_ementas
    
    def search_ementas_by_name(self, nome_disciplina: str) -> List[Dict]:
        """Busca ementas por nome da disciplina"""
        disciplina = Query()
        disciplinas = self.disciplinas.search(disciplina.nome.matches(f'.*{nome_disciplina}.*', flags='i'))
        
        ementas = []
        for disciplina_data in disciplinas:
            ementas_disciplina = self.filter_ementas_by_disciplina(disciplina_data['id_disciplina'])
            ementas.extend(ementas_disciplina)
        
        # Remover duplicatas
        seen = set()
        unique_ementas = []
        for ementa in ementas:
            if ementa['id_ementa'] not in seen:
                seen.add(ementa['id_ementa'])
                unique_ementas.append(ementa)
        
        return unique_ementas
    
    def get_recent_ementas(self, limit: int = 10) -> List[Dict]:
        """Busca ementas mais recentes"""
        all_ementas = self.ementa.all()
        # Ordenar por data_upload (mais recente primeiro)
        sorted_ementas = sorted(all_ementas, key=lambda x: x.get('data_upload', ''), reverse=True)
        return sorted_ementas[:limit]
    
    # ==================== MÉTODOS DE DELETE ====================
    
    def delete_analise(self, analise_id: int, prontuario_professor: str) -> bool:
        """
        Deleta uma análise específica, verificando se o professor tem permissão
        
        Args:
            analise_id: ID da análise a ser deletada
            prontuario_professor: Prontuário do professor que está tentando deletar
            
        Returns:
            bool: True se deletou com sucesso, False caso contrário
        """
        analise = Query()
        
        # Verificar se a análise existe e pertence ao professor
        analise_data = self.analise.search(
            (analise.analise_id == analise_id) & 
            (analise.prontuario_professor == prontuario_professor)
        )
        
        if not analise_data:
            return False
        
        # Deletar a análise
        result = self.analise.remove(analise.analise_id == analise_id)
        return len(result) > 0
    
    def delete_analise_by_ementa(self, ementa_fk: int, prontuario_professor: str) -> bool:
        """
        Deleta todas as análises de uma ementa específica, verificando permissão
        
        Args:
            ementa_fk: ID da ementa
            prontuario_professor: Prontuário do professor que está tentando deletar
            
        Returns:
            bool: True se deletou com sucesso, False caso contrário
        """
        analise = Query()
        
        # Verificar se existem análises da ementa feitas pelo professor
        analises = self.analise.search(
            (analise.ementa_fk == ementa_fk) & 
            (analise.prontuario_professor == prontuario_professor)
        )
        
        if not analises:
            return False
        
        # Deletar todas as análises da ementa feitas pelo professor
        result = self.analise.remove(
            (analise.ementa_fk == ementa_fk) & 
            (analise.prontuario_professor == prontuario_professor)
        )
        return len(result) > 0
    
    def delete_ementa(self, id_ementa: int, prontuario_professor: str) -> bool:
        """
        Deleta uma ementa e todas suas análises relacionadas
        
        Args:
            id_ementa: ID da ementa a ser deletada
            prontuario_professor: Prontuário do professor que está tentando deletar
            
        Returns:
            bool: True se deletou com sucesso, False caso contrário
        """
        # Verificar se a ementa existe
        ementa_data = self.get_ementa_by_id(id_ementa)
        if not ementa_data:
            return False
        
        # Deletar todas as análises relacionadas à ementa (feitas pelo professor)
        self.delete_analise_by_ementa(id_ementa, prontuario_professor)
        
        # Deletar relacionamentos ementa_disciplina
        ementa_disciplina = Query()
        self.ementa_disciplina.remove(ementa_disciplina.ementa_fk == id_ementa)
        
        # Deletar a ementa
        ementa = Query()
        result = self.ementa.remove(ementa.id_ementa == id_ementa)
        
        return len(result) > 0
    
    def delete_curso(self, codigo_curso: str, prontuario_professor: str) -> bool:
        """
        Deleta um curso e todos seus relacionamentos
        
        Args:
            codigo_curso: Código do curso a ser deletado
            prontuario_professor: Prontuário do professor que está tentando deletar
            
        Returns:
            bool: True se deletou com sucesso, False caso contrário
        """
        # Verificar se o professor tem permissão para deletar o curso
        professor_curso = Query()
        permission = self.professor_curso.search(
            (professor_curso.curso_fk == codigo_curso) & 
            (professor_curso.prontuario_professor == prontuario_professor)
        )
        
        if not permission:
            return False
        
        # Buscar todas as disciplinas do curso para deletar ementas relacionadas
        disciplinas_curso = self.get_curso_disciplines(codigo_curso)
        
        # Para cada disciplina, buscar e deletar ementas relacionadas
        for disciplina in disciplinas_curso:
            ementa_disciplina = Query()
            ementa_ids = self.ementa_disciplina.search(
                ementa_disciplina.disciplina_fk == disciplina['id_disciplina']
            )
            
            # Deletar ementas relacionadas à disciplina
            for ementa_rel in ementa_ids:
                self.delete_ementa(ementa_rel['ementa_fk'], prontuario_professor)
        
        # Deletar relacionamentos curso_tags
        curso_tags = Query()
        self.curso_tags.remove(curso_tags.curso_fk == codigo_curso)
        
        # Deletar relacionamentos cursos_disciplina
        cursos_disciplina = Query()
        self.cursos_disciplina.remove(cursos_disciplina.curso_fk == codigo_curso)
        
        # Deletar relacionamento professor_curso
        self.professor_curso.remove(
            (professor_curso.curso_fk == codigo_curso) & 
            (professor_curso.prontuario_professor == prontuario_professor)
        )
        
        # Deletar o curso (apenas se não houver mais professores associados)
        remaining_professors = self.professor_curso.search(professor_curso.curso_fk == codigo_curso)
        if not remaining_professors:
            curso = Query()
            result = self.cursos.remove(curso.codigo_curso == codigo_curso)
            return len(result) > 0
        
        return True
    
    def delete_all_analises_professor(self, prontuario_professor: str) -> bool:
        """
        Deleta todas as análises de um professor
        
        Args:
            prontuario_professor: Prontuário do professor
            
        Returns:
            bool: True se deletou com sucesso, False caso contrário
        """
        analise = Query()
        result = self.analise.remove(analise.prontuario_professor == prontuario_professor)
        return len(result) > 0
    
    def delete_professor_course_relationship(self, prontuario_professor: str, codigo_curso: str) -> bool:
        """
        Remove a associação entre um professor e um curso
        
        Args:
            prontuario_professor: Prontuário do professor
            codigo_curso: Código do curso
            
        Returns:
            bool: True se removeu com sucesso, False caso contrário
        """
        professor_curso = Query()
        result = self.professor_curso.remove(
            (professor_curso.prontuario_professor == prontuario_professor) & 
            (professor_curso.curso_fk == codigo_curso)
        )
        return len(result) > 0
    
    def delete_disciplina_from_curso(self, codigo_curso: str, id_disciplina: str, prontuario_professor: str) -> bool:
        """
        Remove uma disciplina de um curso
        
        Args:
            codigo_curso: Código do curso
            id_disciplina: ID da disciplina
            prontuario_professor: Prontuário do professor que está tentando deletar
            
        Returns:
            bool: True se removeu com sucesso, False caso contrário
        """
        # Verificar se o professor tem permissão para o curso
        professor_curso = Query()
        permission = self.professor_curso.search(
            (professor_curso.curso_fk == codigo_curso) & 
            (professor_curso.prontuario_professor == prontuario_professor)
        )
        
        if not permission:
            return False
        
        # Deletar ementas relacionadas à disciplina
        ementa_disciplina = Query()
        ementa_ids = self.ementa_disciplina.search(ementa_disciplina.disciplina_fk == id_disciplina)
        
        for ementa_rel in ementa_ids:
            self.delete_ementa(ementa_rel['ementa_fk'], prontuario_professor)
        
        # Remover relacionamento curso_disciplina
        cursos_disciplina = Query()
        result = self.cursos_disciplina.remove(
            (cursos_disciplina.curso_fk == codigo_curso) & 
            (cursos_disciplina.disciplina_fk == id_disciplina)
        )
        
        return len(result) > 0
    
    def delete_tag_from_curso(self, codigo_curso: str, tag_id: int, prontuario_professor: str) -> bool:
        """
        Remove uma tag de um curso
        
        Args:
            codigo_curso: Código do curso
            tag_id: ID da tag
            prontuario_professor: Prontuário do professor que está tentando deletar
            
        Returns:
            bool: True se removeu com sucesso, False caso contrário
        """
        # Verificar se o professor tem permissão para o curso
        professor_curso = Query()
        permission = self.professor_curso.search(
            (professor_curso.curso_fk == codigo_curso) & 
            (professor_curso.prontuario_professor == prontuario_professor)
        )
        
        if not permission:
            return False
        
        # Remover relacionamento curso_tags
        curso_tags = Query()
        result = self.curso_tags.remove(
            (curso_tags.curso_fk == codigo_curso) & 
            (curso_tags.tag_fk == tag_id)
        )
        
        return len(result) > 0
    
    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """
        Limpa dados órfãos (sem relacionamentos válidos)
        
        Returns:
            Dict com contagem de registros removidos por tabela
        """
        cleanup_stats = {
            'disciplinas_removidas': 0,
            'tags_removidas': 0,
            'ementas_removidas': 0
        }
        
        # Remover disciplinas sem curso
        disciplina = Query()
        curso_disciplina = Query()
        all_disciplinas = self.disciplinas.all()
        
        for disciplina_data in all_disciplinas:
            disciplina_id = disciplina_data['id_disciplina']
            has_curso = self.cursos_disciplina.search(curso_disciplina.disciplina_fk == disciplina_id)
            
            if not has_curso:
                self.disciplinas.remove(disciplina.id_disciplina == disciplina_id)
                cleanup_stats['disciplinas_removidas'] += 1
        
        # Remover tags sem curso
        tag = Query()
        curso_tags = Query()
        all_tags = self.tags.all()
        
        for tag_data in all_tags:
            tag_id = tag_data['id_tag']
            has_curso = self.curso_tags.search(curso_tags.tag_fk == tag_id)
            
            if not has_curso:
                self.tags.remove(tag.id_tag == tag_id)
                cleanup_stats['tags_removidas'] += 1
        
        # Remover ementas sem disciplinas
        ementa = Query()
        ementa_disciplina = Query()
        all_ementas = self.ementa.all()
        
        for ementa_data in all_ementas:
            ementa_id = ementa_data['id_ementa']
            has_disciplina = self.ementa_disciplina.search(ementa_disciplina.ementa_fk == ementa_id)
            
            if not has_disciplina:
                self.ementa.remove(ementa.id_ementa == ementa_id)
                cleanup_stats['ementas_removidas'] += 1
        
        return cleanup_stats
