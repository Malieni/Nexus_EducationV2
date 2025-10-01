#!/usr/bin/env python3
"""
Script de inicialização do Nexus Education
"""

import subprocess
import sys
import os

def check_poetry():
    """Verifica se Poetry está instalado"""
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_dependencies():
    """Instala dependências com Poetry"""
    print("📦 Instalando dependências...")
    try:
        subprocess.run(["poetry", "install"], check=True)
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências!")
        return False

def create_directories():
    """Cria diretórios necessários"""
    directories = [
        "src/data/database",
        "src/data/uploads",
        ".streamlit"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("📁 Diretórios criados!")

def run_app():
    """Executa a aplicação"""
    print("🚀 Iniciando Nexus Education...")
    try:
        subprocess.run(["poetry", "run", "streamlit", "run", "src/app/app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada pelo usuário")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar aplicação: {e}")

def main():
    """Função principal"""
    print("🎓 Nexus Education - Sistema de Análise de Ementas Acadêmicas")
    print("=" * 60)
    
    # Verificar Poetry
    if not check_poetry():
        print("❌ Poetry não encontrado!")
        print("📖 Instale o Poetry: https://python-poetry.org/docs/#installation")
        sys.exit(1)
    
    # Criar diretórios
    create_directories()
    
    # Instalar dependências
    if not install_dependencies():
        sys.exit(1)
    
    # Executar aplicação
    run_app()

if __name__ == "__main__":
    main()
