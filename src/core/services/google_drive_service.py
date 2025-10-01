"""
Serviço para integração com Google Drive
"""
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import streamlit as st

class GoogleDriveService:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        self.service = None
        self.folder_id = '1goUGHzHcPoVEVFurFSVFTSAEBtflpLWD'  # ID da pasta no Drive
        
    def authenticate(self):
        """Autentica com o Google Drive"""
        creds = None
        
        # Verificar se existe token.json
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar token: {str(e)}")
                # Remover token inválido
                os.remove('token.json')
                creds = None
        
        # Se não há credenciais válidas, solicitar login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    st.success("✅ Token renovado com sucesso!")
                except Exception as e:
                    st.warning(f"⚠️ Erro ao renovar token: {str(e)}")
                    # Remover token inválido e solicitar nova autenticação
                    if os.path.exists('token.json'):
                        os.remove('token.json')
                    creds = None
            
            if not creds or not creds.valid:
                # Verificar se existe credentials.json
                if not os.path.exists('credentials.json'):
                    st.error("❌ Arquivo credentials.json não encontrado!")
                    st.info("""
                    Para usar o Google Drive, você precisa:
                    1. Criar um projeto no Google Cloud Console
                    2. Habilitar a API do Google Drive
                    3. Baixar o arquivo credentials.json
                    4. Colocar o arquivo na raiz do projeto
                    """)
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    st.success("✅ Autenticação realizada com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro na autenticação: {str(e)}")
                    return False
            
            # Salvar credenciais para próxima execução
            try:
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                st.error(f"❌ Erro ao salvar token: {str(e)}")
                return False
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            return True
        except Exception as e:
            st.error(f"❌ Erro ao criar serviço do Drive: {str(e)}")
            return False
    
    def upload_file(self, file_path: str, file_name: str, mime_type: str = 'application/pdf') -> str:
        """Faz upload de um arquivo para o Google Drive"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Metadados do arquivo
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id]
            }
            
            # Upload do arquivo
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            st.error(f"❌ Erro ao fazer upload: {str(e)}")
            return None
    
    def download_file(self, file_id: str, file_name: str) -> bytes:
        """Baixa um arquivo do Google Drive"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue()
            
        except Exception as e:
            st.error(f"❌ Erro ao baixar arquivo: {str(e)}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """Deleta um arquivo do Google Drive"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao deletar arquivo: {str(e)}")
            return False
    
    def list_files(self) -> list:
        """Lista arquivos na pasta do Drive"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            results = self.service.files().list(
                q=f"'{self.folder_id}' in parents",
                fields="files(id, name, createdTime, size)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            st.error(f"❌ Erro ao listar arquivos: {str(e)}")
            return []
    
    def get_file_info(self, file_id: str) -> dict:
        """Obtém informações de um arquivo específico"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, createdTime, size, webViewLink"
            ).execute()
            
            return file_info
            
        except Exception as e:
            st.error(f"❌ Erro ao obter informações do arquivo: {str(e)}")
            return None
