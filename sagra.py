# SAGRA - Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas
# Autor: Anselmo Borges, Pedro Bala Pascal, Luis Eduardo dos Santos
# Data: 16/03/2025
# Descrição: Sistema para acompanhamento e gerenciamento da reabilitação de atletas
#            de rugby após cirurgia de reconstrução do LCA.

# Importação das bibliotecas necessárias
import streamlit as st
import os

# Configuração da página Streamlit
st.set_page_config(
    page_title="SAGRA - Reabilitação LCA",
    page_icon="🏉",
    layout="wide"
)

# Credenciais (em um ambiente real, isso deveria estar em um arquivo de configuração seguro)
CREDENTIALS = {
    "admin": "admin123",
    "user": "user123",
    "luiz": "luizao"
}

# Função de autenticação
def check_password():
    """Retorna `True` se o usuário tiver a senha correta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        st.title("Login SAGRA")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            if username in CREDENTIALS and password == CREDENTIALS[username]:
                st.session_state["password_correct"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        return False
    
    return True

# Verifica a autenticação
if not check_password():
    st.stop()

# Título principal
st.title('SAGRA - Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas')

# Verifica se a pasta existe
if not os.path.exists('planilhas_originais'):
    st.error("Diretório 'planilhas_originais' não encontrado!")
    os.makedirs('planilhas_originais')
    st.info("Diretório 'planilhas_originais' foi criado. Por favor, adicione os arquivos de protocolo.")
else:
    # Lista todos os arquivos Excel
    arquivos_excel = [f for f in os.listdir('planilhas_originais') if f.endswith(('.xlsx', '.xls'))]
    
    if not arquivos_excel:
        st.error("Nenhum arquivo Excel encontrado no diretório 'planilhas_originais'!")
        st.info("Por favor, adicione os arquivos de protocolo no formato Excel (.xlsx ou .xls)")
    else:
        st.success(f"Encontrados {len(arquivos_excel)} protocolos disponíveis")
        
        # Mostra a lista de protocolos
        st.subheader("Protocolos Disponíveis")
        
        # Organiza os protocolos em colunas
        col1, col2 = st.columns(2)
        
        for i, arquivo in enumerate(arquivos_excel):
            caminho_arquivo = os.path.join('planilhas_originais', arquivo)
            nome_protocolo = os.path.splitext(arquivo)[0]
            
            # Alterna entre as colunas
            with col1 if i % 2 == 0 else col2:
                with st.expander(nome_protocolo):
                    st.write(f"Arquivo: {arquivo}")
                    with open(caminho_arquivo, 'rb') as f:
                        st.download_button(
                            label="📥 Baixar Planilha",
                            data=f,
                            file_name=arquivo,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    st.info("""
                    Para visualizar o arquivo:
                    1. Clique no botão 'Baixar Planilha' acima
                    2. O arquivo será baixado para seu computador
                    3. Abra o arquivo com Excel ou outro programa compatível
                    """) 