#!/usr/bin/env python3
"""
Script para renovar o token do Google Drive
Execute este script quando o token expirar
"""

import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Escopos necessários para o Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly'
]

def renovar_token():
    """Renova o token do Google Drive"""
    print("🔄 RENOVANDO TOKEN DO GOOGLE DRIVE")
    print("=" * 50)
    
    creds = None
    
    # Verificar se existe token.json
    if os.path.exists('token.json'):
        print("📄 Token existente encontrado...")
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            print("✅ Token carregado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao carregar token: {str(e)}")
            print("🗑️ Removendo token inválido...")
            os.remove('token.json')
            creds = None
    
    # Verificar se as credenciais são válidas
    if not creds or not creds.valid:
        print("🔍 Verificando validade das credenciais...")
        
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Tentando renovar token expirado...")
            try:
                creds.refresh(Request())
                print("✅ Token renovado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao renovar token: {str(e)}")
                print("🗑️ Removendo token inválido...")
                if os.path.exists('token.json'):
                    os.remove('token.json')
                creds = None
        
        if not creds or not creds.valid:
            print("🔐 Iniciando nova autenticação...")
            
            # Verificar se existe credentials.json
            if not os.path.exists('credentials.json'):
                print("❌ Arquivo credentials.json não encontrado!")
                print("""
                Para renovar o token, você precisa:
                1. Ter o arquivo credentials.json na raiz do projeto
                2. Este arquivo deve ser baixado do Google Cloud Console
                3. Deve ter as credenciais OAuth2 configuradas
                """)
                return False
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                print("🌐 Abrindo navegador para autenticação...")
                print("📝 Siga as instruções no navegador para autorizar o acesso.")
                creds = flow.run_local_server(port=0)
                print("✅ Autenticação realizada com sucesso!")
            except Exception as e:
                print(f"❌ Erro na autenticação: {str(e)}")
                return False
        
        # Salvar o novo token
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            print("💾 Token salvo com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao salvar token: {str(e)}")
            return False
    
    # Testar o token
    try:
        from googleapiclient.discovery import build
        service = build('drive', 'v3', credentials=creds)
        
        # Fazer uma requisição simples para testar
        results = service.files().list(pageSize=1).execute()
        print("✅ Token testado com sucesso!")
        print("🎉 Renovação concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar token: {str(e)}")
        return False

def main():
    """Função principal"""
    print("🎓 NEXUS EDUCATION - RENOVAÇÃO DE TOKEN")
    print("=" * 50)
    
    if renovar_token():
        print("\n✅ Token renovado com sucesso!")
        print("🚀 Agora você pode usar o sistema normalmente.")
    else:
        print("\n❌ Falha na renovação do token.")
        print("🔧 Verifique se o arquivo credentials.json está correto.")
    
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()
