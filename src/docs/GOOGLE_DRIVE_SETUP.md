# 📁 Configuração do Google Drive

Para que os documentos sejam enviados automaticamente ao Google Drive, você precisa configurar a integração.

## 🔧 Passos para Configuração

### 1. Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Google Drive API**

### 2. Configurar Credenciais

1. Vá para **APIs & Services** > **Credentials**
2. Clique em **Create Credentials** > **OAuth client ID**
3. Selecione **Desktop application**
4. Baixe o arquivo JSON das credenciais
5. Renomeie o arquivo para `credentials.json`
6. Coloque o arquivo na raiz do projeto

### 3. Configurar Pasta no Google Drive

1. Crie uma pasta no Google Drive para armazenar as ementas
2. Copie o ID da pasta da URL (ex: `1goUGHzHcPoVEVFurFSVFTSAEBtflpLWD`)
3. Atualize o `folder_id` no arquivo `google_drive_service.py` (linha 15)

### 4. Primeira Execução

Na primeira vez que executar o aplicativo:

1. Execute: `poetry run streamlit run app.py`
2. Faça upload de um PDF
3. Será aberto o navegador para autenticação
4. Autorize o acesso ao Google Drive
5. O arquivo `token.json` será criado automaticamente

## 📋 Estrutura de Arquivos

```
Nexus_Education/
├── credentials.json          # Credenciais do Google (você precisa baixar)
├── token.json               # Token de autenticação (criado automaticamente)
├── google_drive_service.py  # Serviço de integração
└── app.py                   # Aplicação principal
```

## ✅ Verificação

Após a configuração, quando você fizer upload de PDFs:

- ✅ **Com Google Drive**: Arquivos serão enviados automaticamente
- ⚠️ **Sem Google Drive**: Arquivos serão salvos apenas localmente

## 🔒 Permissões Necessárias

O aplicativo solicita as seguintes permissões:

- `https://www.googleapis.com/auth/drive.file` - Upload de arquivos
- `https://www.googleapis.com/auth/drive.readonly` - Download de arquivos

## 🚨 Troubleshooting

### Erro: "credentials.json não encontrado"
- Baixe o arquivo de credenciais do Google Cloud Console
- Renomeie para `credentials.json`
- Coloque na raiz do projeto

### Erro: "Token expirado"
- Delete o arquivo `token.json`
- Execute o aplicativo novamente
- Faça nova autenticação

### Erro: "Pasta não encontrada"
- Verifique se o `folder_id` está correto
- Certifique-se de que a pasta existe no Google Drive
- Verifique as permissões da pasta

## 📞 Suporte

Se encontrar problemas:

1. Verifique se todos os arquivos estão no lugar correto
2. Confirme se a API do Google Drive está ativada
3. Teste a autenticação manualmente
4. Verifique os logs de erro no terminal
