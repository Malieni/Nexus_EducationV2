import re
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

class GroqClient:
    def __init__(self, model_id='llama-3.1-8b-instant', api_key=None) -> None:
        self.model_id = model_id
        
        # Obter a chave da API das variáveis de ambiente ou parâmetro
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "A chave da API do Groq deve ser fornecida. "
                "Configure a variável de ambiente GROQ_API_KEY ou passe api_key como parâmetro. "
                "Obtenha sua chave em: https://console.groq.com/keys"
            )
        
        self.client = ChatGroq(model=self.model_id, api_key=self.api_key)
    
    def generate_response(self, prompt):
        response = self.client.invoke(prompt)
        return response.content

    def resume_ementa(self, ementa):
        prompt = f'''
            **Solicitação de Resumo de Ementa Acadêmica em Markdown:**
            
            # Ementa acadêmica do aluno para resumir:
            
            {ementa}

            Por favor, gere um resumo da ementa acadêmica fornecida, formatado em Markdown, seguindo rigorosamente o modelo abaixo. **Não adicione seções extras, tabelas ou qualquer outro tipo de formatação diferente da especificada.** Preencha cada seção com as informações relevantes, garantindo que o resumo seja preciso e focado no histórico acadêmico.

            **Formato de Output Esperado:**

            ```markdown
            ## Nome Completo
            nome_completo aqui

            ## Disciplinas Cursadas
            disciplinas cursadas aqui

            ## Formação Acadêmica
            formação acadêmica aqui

        '''
            
        result_raw = self.generate_response(prompt)
        
        try:
            result = result_raw.split('```markdown')[1]
        except:
            result = result_raw
        
        return result

    def generate_score(self, ementa, curso, max_attempts=10):
        prompt = f'''
            **Objetivo:** Avaliar uma ementa acadêmica de um aluno em relação ao curso específico do professor e calcular a pontuação final. A nota máxima é 10.0.

            **Instruções:**

            1. **Disciplinas Cursadas (Peso: 30%)**: Avalie a relevância das disciplinas cursadas pelo aluno em relação ao curso do professor, considerando a carga-horária e o conteúdo.
            2. **Adequação Curricular (Peso: 35%)**: Verifique o alinhamento do histórico acadêmico do aluno com os requisitos do curso do professor.
            3. **Formação Acadêmica (Peso: 10%)**: Avalie a relevância da formação acadêmica do aluno para o curso do professor.
            4. **Pontos Fortes Acadêmicos (Peso: 25%)**: Avalie os pontos fortes do histórico acadêmico do aluno em relação ao curso.
            5. **Matérias Faltantes (Desconto de até 10%)**: Avalie a gravidade das disciplinas faltantes em relação ao curso: matérias obrigatórias não cursadas e carga-horária insuficiente.
            
            Ementa acadêmica do aluno:
            
            {ementa}
            
            Curso do professor para análise:
            
            {curso}

            **Output Esperado:**
            ```
            Pontuação Final: x.x
            ```

            **Atenção:** Seja rigoroso ao atribuir as notas. A nota máxima é 10.0, e o output deve conter apenas "Pontuação Final: x.x".
        
        '''

        for attempt in range(max_attempts):
            result_raw = self.generate_response(prompt)
            score = self.extract_score_from_result(result_raw)

            if score is not None:
                return score


    def extract_score_from_result(self, result_raw):
        
        pattern = r"(?i)Pontuação Final[:\s]*([\d,.]+(?:/\d{1,2})?)"

        match = re.search(pattern,result_raw)
        if match:
            score_str = match.group(1)
            
            if '/' in score_str:
                score_str = score_str.split('/')[0]
            
            try:
                # Limpar a string e tentar converter para float
                score_str = score_str.strip().replace(',', '.')
                
                # Verificar se é apenas um ponto ou string vazia
                if not score_str or score_str == '.' or score_str == '':
                    return None
                
                return float(score_str)
            except (ValueError, TypeError):
                return None
                
        return None

    def generate_opinion(self, ementa, curso, max_attempts=10):
        prompt = f'''
            Por favor, analise a ementa acadêmica do aluno em relação ao curso do professor e crie uma análise crítica e detalhada. A sua análise deve incluir os seguintes pontos:
            Você deve pensar como um coordenador acadêmico que está analisando o histórico escolar de um aluno que solicitou transferência ou ingresso no curso ministrado pelo professor.
            
            Formate a resposta de forma profissional, coloque títulos grandes nas seções.

            1. **Pontos de Alinhamento Acadêmico**: Identifique e discuta os aspectos da ementa acadêmica que estão diretamente alinhados com os requisitos do curso. Inclua exemplos específicos de disciplinas cursadas, carga-horária adequada, ou formação acadêmica que se alinha com o que o curso do professor exige.

            2. **Pontos de Desalinhamento Curricular**: Destaque e discuta as áreas onde o aluno não atende aos requisitos acadêmicos do curso. Isso pode incluir falta de disciplinas obrigatórias, ausência de pré-requisitos necessários, ou formação acadêmica que não corresponde às expectativas do curso.

            3. **Pontos de Atenção Acadêmica**: Identifique e discuta características do histórico acadêmico que merecem atenção especial. Isso pode incluir aspectos como frequência de mudanças de curso, lacunas no histórico escolar, ou padrões acadêmicos que podem influenciar o desempenho no curso, tanto de maneira positiva quanto negativa.

            Sua análise deve ser objetiva, baseada em evidências apresentadas na ementa acadêmica e na descrição do curso. Seja detalhado e forneça uma avaliação honesta dos pontos fortes e fracos do aluno em relação ao curso do professor.

            **Ementa Acadêmica do Aluno:**
            {ementa}

            **Descrição do Curso do Professor:**
            {curso}
            
            Você deve devolver essa análise crítica formatada como se fosse um relatório analítico acadêmico, deve estar formatado com títulos grandes em destaques
        '''
        
        return self.generate_response(prompt)