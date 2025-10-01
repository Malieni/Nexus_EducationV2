"""
Configuração do Supabase para o projeto Nexus Education
"""
import os
from supabase import create_client, Client
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class SupabaseConfig:
    """Configuração e cliente do Supabase"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Verificar se as credenciais estão configuradas
        if not self.url or not self.anon_key:
            print("⚠️ Variáveis de ambiente do Supabase não configuradas!")
            print("📝 Configure SUPABASE_URL e SUPABASE_ANON_KEY no arquivo .env")
            print("🔄 Usando modo offline (sem Supabase)")
            self.client = None
            self.service_client = None
            self.offline_mode = True
            return
        
        try:
            self.client: Client = create_client(self.url, self.anon_key)
            self.service_client: Optional[Client] = None
            self.offline_mode = False
            
            if self.service_role_key:
                self.service_client = create_client(self.url, self.service_role_key)
                print("✅ Supabase configurado com service role")
            else:
                print("⚠️ SUPABASE_SERVICE_ROLE_KEY não configurada - algumas funcionalidades podem não funcionar")
                
        except Exception as e:
            print(f"❌ Erro ao inicializar Supabase: {e}")
            print("🔄 Usando modo offline")
            self.client = None
            self.service_client = None
            self.offline_mode = True
    
    def get_client(self, use_service_role: bool = False) -> Optional[Client]:
        """Retorna o cliente do Supabase"""
        if self.offline_mode:
            return None
            
        if use_service_role and self.service_client:
            return self.service_client
        return self.client
    
    def test_connection(self) -> bool:
        """Testa a conexão com o Supabase"""
        if self.offline_mode:
            print("🔄 Modo offline - Supabase não está configurado")
            return False
            
        try:
            # Tentar fazer uma consulta simples
            response = self.client.table("professores").select("prontuario").limit(1).execute()
            return True
        except Exception as e:
            print(f"Erro ao conectar com Supabase: {e}")
            return False

# Instância global da configuração
supabase_config = SupabaseConfig()
