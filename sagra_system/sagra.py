# Importação das bibliotecas necessárias
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
import duckdb
import yaml
import plotly.express as px
import plotly.graph_objects as go
from analise_dados import (
    gerar_relatorio_paciente,
    gerar_grafico_progresso,
    gerar_analise_estatistica,
    exportar_dados,
    fazer_backup
)

# Configuração da página
st.set_page_config(
    page_title="SAGRA - Sistema de Reabilitação",
    page_icon="🏉",
    layout="wide"
)

# Carrega configurações
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Conexão com o banco de dados
def get_db_connection():
    try:
        # Verifica se o arquivo de configuração existe
        if not os.path.exists('config.yaml'):
            st.error("Arquivo de configuração não encontrado!")
            return None
            
        # Carrega as configurações
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            
        # Remove o banco de dados existente se houver problemas
        if os.path.exists(config['database']['path']):
            try:
                conn = duckdb.connect(config['database']['path'])
                # Testa a conexão
                conn.execute("SELECT 1")
            except:
                os.remove(config['database']['path'])
                st.warning("Banco de dados corrompido. Criando novo banco...")
        
        # Conecta ao banco de dados
        conn = duckdb.connect(config['database']['path'])
        
        # Verifica se as tabelas existem
        tabelas = conn.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table'
        """).fetchall()
        
        tabelas_existentes = [t[0] for t in tabelas]
        tabelas_necessarias = ['fases_reabilitacao', 'pacientes', 'progresso']
        
        # Se alguma tabela necessária não existir, cria todas as tabelas
        if not all(tabela in tabelas_existentes for tabela in tabelas_necessarias):
            st.warning("Tabelas não encontradas. Criando estrutura do banco de dados...")
            with open('schema.sql', 'r') as f:
                sql_commands = f.read().split(';')
                for command in sql_commands:
                    if command.strip():
                        try:
                            conn.execute(command)
                        except Exception as e:
                            st.warning(f"Erro ao executar comando SQL: {str(e)}")
            
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        return None

# Função para obter o próximo ID disponível
def get_next_id(conn, table_name):
    try:
        result = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table_name}").fetchone()
        return int(result[0]) if result else 1
    except:
        return 1

# Função para verificar credenciais
def verificar_credenciais(username, password):
    credenciais = {
        "admin": "admin123",
        "user": "user123",
        "luiz": "luizao"
    }
    return username in credenciais and credenciais[username] == password

# Função para criar o botão de download
def get_binary_file_downloader_html(file_path, file_label='File'):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{os.path.basename(file_path)}">Clique aqui para baixar {file_label}</a>'

# Inicialização do estado da sessão
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'paciente_selecionado' not in st.session_state:
    st.session_state.paciente_selecionado = None

# Barra lateral para navegação
if st.session_state.autenticado:
    pagina = st.sidebar.radio(
        "Navegação",
        ["Dashboard", "Pacientes", "Protocolos", "Análise de Dados", "Relatórios", "Backup"]
    )
else:
    pagina = "Login"

# Página de Login
if pagina == "Login":
    st.title("SAGRA - Sistema de Reabilitação")
    st.write("Por favor, faça login para continuar")
    
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Login"):
        if verificar_credenciais(username, password):
            st.session_state.autenticado = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Credenciais inválidas")

# Página de Dashboard
elif pagina == "Dashboard":
    st.title("Dashboard")
    
    # Botão de logout
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
    
    # Conexão com o banco de dados
    conn = get_db_connection()
    
    # Estatísticas gerais
    col1, col2, col3 = st.columns(3)
    with col1:
        total_pacientes = conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
        st.metric("Total de Pacientes", total_pacientes)
    with col2:
        pacientes_ativos = conn.execute("SELECT COUNT(*) FROM progresso WHERE data_fim IS NULL").fetchone()[0]
        st.metric("Pacientes Ativos", pacientes_ativos)
    with col3:
        pacientes_concluidos = conn.execute("SELECT COUNT(*) FROM progresso WHERE data_fim IS NOT NULL").fetchone()[0]
        st.metric("Pacientes Concluídos", pacientes_concluidos)
    
    # Gráfico de progresso por fase
    st.subheader("Progresso por Fase")
    progresso_fases = conn.execute("""
        SELECT f.fase, COUNT(*) as total
        FROM progresso p
        JOIN fases_reabilitacao f ON p.fase = f.id
        GROUP BY f.fase
    """).fetchdf()
    
    fig = px.bar(progresso_fases, x='fase', y='total', title='Pacientes por Fase')
    st.plotly_chart(fig)
    
    # Lista de pacientes recentes
    st.subheader("Pacientes Recentes")
    pacientes_recentes = conn.execute("""
        SELECT p.nome, p.data_cirurgia, f.fase, pr.status
        FROM pacientes p
        JOIN progresso pr ON p.id = pr.paciente_id
        JOIN fases_reabilitacao f ON pr.fase = f.id
        ORDER BY pr.data_inicio DESC
        LIMIT 5
    """).fetchdf()
    
    st.dataframe(pacientes_recentes)

# Página de Pacientes
elif pagina == "Pacientes":
    st.title("Gerenciamento de Pacientes")
    
    # Botão de logout
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
    
    # Conexão com o banco de dados
    conn = get_db_connection()
    
    # Formulário de cadastro de paciente
    with st.expander("Cadastrar Novo Paciente"):
        with st.form("form_paciente"):
            nome = st.text_input("Nome do Paciente")
            data_cirurgia = st.date_input("Data da Cirurgia")
            data_cadastro = st.date_input("Data de Cadastro", value=datetime.now())
            
            if st.form_submit_button("Cadastrar"):
                try:
                    # Obtém o próximo ID disponível
                    next_id = get_next_id(conn, 'pacientes')
                    
                    # Insere o novo paciente
                    conn.execute("""
                        INSERT INTO pacientes (id, nome, data_cirurgia, data_cadastro)
                        VALUES (?, ?, ?, ?)
                    """, (next_id, nome, data_cirurgia, data_cadastro))
                    st.success("Paciente cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao cadastrar paciente: {str(e)}")
    
    # Lista de pacientes
    st.subheader("Lista de Pacientes")
    pacientes = conn.execute("SELECT * FROM pacientes").fetchdf()
    st.dataframe(pacientes)
    
    # Seleção de paciente para detalhes
    if not pacientes.empty:
        paciente_selecionado = st.selectbox(
            "Selecione um paciente para ver detalhes",
            pacientes['nome'].tolist()
        )
        
        if paciente_selecionado:
            paciente_id = pacientes[pacientes['nome'] == paciente_selecionado]['id'].iloc[0]
            st.session_state.paciente_selecionado = paciente_id
            
            # Detalhes do paciente
            st.subheader(f"Detalhes do Paciente: {paciente_selecionado}")
            progresso_paciente = conn.execute("""
                SELECT f.fase, p.data_inicio, p.data_fim, p.status, p.observacoes
                FROM progresso p
                JOIN fases_reabilitacao f ON p.fase = f.id
                WHERE p.paciente_id = ?
                ORDER BY p.data_inicio
            """, (int(paciente_id),)).fetchdf()
            
            st.dataframe(progresso_paciente)
            
            # Formulário para atualizar progresso
            with st.expander("Atualizar Progresso"):
                with st.form("form_progresso"):
                    fase = st.selectbox(
                        "Fase",
                        [f"{f['id']} - {f['nome']}" for f in config['protocolo']['fases']]
                    )
                    data_inicio = st.date_input("Data de Início")
                    status = st.selectbox("Status", ["Em Andamento", "Concluído"])
                    observacoes = st.text_area("Observações")
                    
                    if st.form_submit_button("Atualizar"):
                        try:
                            fase_id = int(fase.split(" - ")[0])
                            next_id = get_next_id(conn, 'progresso')
                            
                            conn.execute("""
                                INSERT INTO progresso (id, paciente_id, fase, data_inicio, status, observacoes)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (next_id, int(paciente_id), fase_id, data_inicio, status, observacoes))
                            st.success("Progresso atualizado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao atualizar progresso: {str(e)}")

# Página de Análise de Dados
elif pagina == "Análise de Dados":
    st.title("Análise de Dados")
    
    # Botão de logout
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
    
    conn = get_db_connection()
    
    # Análise estatística
    st.subheader("Análise Estatística")
    tempo_fase, sucesso_fase = gerar_analise_estatistica(conn)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Tempo Médio por Fase")
        st.dataframe(tempo_fase)
    with col2:
        st.write("Taxa de Sucesso por Fase")
        st.dataframe(sucesso_fase)
    
    # Gráficos de análise
    st.subheader("Visualizações")
    
    fig_tempo = px.bar(tempo_fase, x='fase', y='tempo_medio', title='Tempo Médio por Fase')
    st.plotly_chart(fig_tempo)
    
    fig_sucesso = px.bar(sucesso_fase, x='fase', y='taxa_sucesso', title='Taxa de Sucesso por Fase')
    st.plotly_chart(fig_sucesso)

# Página de Relatórios
elif pagina == "Relatórios":
    st.title("Relatórios")
    
    # Botão de logout
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
    
    conn = get_db_connection()
    
    # Seleção de paciente para relatório
    pacientes = conn.execute("SELECT id, nome FROM pacientes").fetchdf()
    paciente_selecionado = st.selectbox(
        "Selecione um paciente para gerar relatório",
        pacientes['nome'].tolist()
    )
    
    if paciente_selecionado:
        paciente_id = pacientes[pacientes['nome'] == paciente_selecionado]['id'].iloc[0]
        
        # Gera relatório
        relatorio = gerar_relatorio_paciente(paciente_id, conn)
        
        # Exibe relatório
        st.subheader("Dados do Paciente")
        st.json(relatorio["Dados do Paciente"])
        
        st.subheader("Progresso")
        st.dataframe(pd.DataFrame(relatorio["Progresso"]))
        
        # Gráficos de progresso
        fig_fases, fig_tempo = gerar_grafico_progresso(paciente_id, conn)
        st.plotly_chart(fig_fases)
        st.plotly_chart(fig_tempo)
        
        # Botão para exportar relatório
        if st.button("Exportar Relatório"):
            exportar_dados(conn, formato='excel')
            st.success("Relatório exportado com sucesso!")

# Página de Backup
elif pagina == "Backup":
    st.title("Backup do Sistema")
    
    # Botão de logout
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
    
    conn = get_db_connection()
    
    # Seção de backup
    st.subheader("Realizar Backup")
    if st.button("Fazer Backup Agora"):
        backup_path = fazer_backup(conn)
        st.success(f"Backup realizado com sucesso! Arquivo salvo em: {backup_path}")
    
    # Seção de exportação
    st.subheader("Exportar Dados")
    formato = st.selectbox("Formato de Exportação", ["excel", "csv"])
    if st.button("Exportar Dados"):
        export_path = exportar_dados(conn, formato)
        st.success(f"Dados exportados com sucesso! Arquivo salvo em: {export_path}")

# Página de Protocolos
elif pagina == "Protocolos":
    st.title("Protocolos de Reabilitação")
    
    # Botão de logout
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
    
    # Verifica se o diretório existe
    if not os.path.exists('planilhas_originais'):
        st.error("Diretório 'planilhas_originais' não encontrado!")
        os.makedirs('planilhas_originais')
        st.info("Diretório criado. Por favor, adicione os arquivos Excel necessários.")
    else:
        # Lista todos os arquivos Excel no diretório
        arquivos = [f for f in os.listdir('planilhas_originais') if f.endswith('.xlsx')]
        
        if not arquivos:
            st.error("Nenhum protocolo encontrado no diretório 'planilhas_originais'!")
        else:
            st.success(f"Encontrados {len(arquivos)} protocolos disponíveis!")
            
            # Divide os protocolos em duas colunas
            col1, col2 = st.columns(2)
            
            for i, arquivo in enumerate(arquivos):
                col = col1 if i % 2 == 0 else col2
                with col.expander(arquivo):
                    file_path = os.path.join('planilhas_originais', arquivo)
                    st.markdown(get_binary_file_downloader_html(file_path, arquivo), unsafe_allow_html=True)
                    st.info("Após baixar, abra o arquivo com o Excel ou outro programa compatível.")

# Página de Visualização de Dados
elif pagina == "Visualização de Dados":
    st.title("Visualização de Dados do Atleta")
    
    # Botão de logout
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
    
    # Código original para visualização de dados
    st.subheader("Selecione as datas para análise")
    
    # Seleção de datas
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data de Início", value=datetime.now())
    with col2:
        data_fim = st.date_input("Data de Fim", value=datetime.now())
    
    # Seleção do tipo de análise
    tipo_analise = st.selectbox(
        "Tipo de Análise",
        ["Força Muscular", "Amplitude de Movimento", "Dor", "Edema", "Todos os Dados"]
    )
    
    # Botão para carregar dados
    if st.button("Carregar Dados"):
        try:
            if tipo_analise == "Todos os Dados":
                # Carrega todos os arquivos de dados
                dados_combinados = pd.DataFrame()
                tipos = ["forca_muscular", "amplitude_de_movimento", "dor", "edema"]
                
                for tipo in tipos:
                    arquivo = f"dados_{tipo}.xlsx"
                    caminho_arquivo = os.path.join('dados_atletas', arquivo)
                    
                    if os.path.exists(caminho_arquivo):
                        df = pd.read_excel(caminho_arquivo)
                        df['Data'] = pd.to_datetime(df['Data'])
                        df['Tipo'] = tipo.replace('_', ' ').title()
                        dados_combinados = pd.concat([dados_combinados, df])
                
                if not dados_combinados.empty:
                    # Filtra os dados pelo período selecionado
                    dados_filtrados = dados_combinados[
                        (dados_combinados['Data'].dt.date >= data_inicio) & 
                        (dados_combinados['Data'].dt.date <= data_fim)
                    ]
                    
                    if not dados_filtrados.empty:
                        # Gráfico de linha para todos os tipos
                        st.subheader("Evolução de Todos os Parâmetros")
                        st.line_chart(dados_filtrados.pivot(index='Data', columns='Tipo', values='Valor'))
                        
                        # Gráfico de área para visualização do progresso
                        st.subheader("Progresso da Reabilitação")
                        st.area_chart(dados_filtrados.pivot(index='Data', columns='Tipo', values='Valor'))
                        
                        # Tabela de dados
                        st.subheader("Dados Detalhados")
                        st.dataframe(dados_filtrados)
                        
                        # Estatísticas por tipo
                        st.subheader("Estatísticas por Tipo de Análise")
                        tipos_unicos = dados_filtrados['Tipo'].unique()
                        for tipo in tipos_unicos:
                            dados_tipo = dados_filtrados[dados_filtrados['Tipo'] == tipo]
                            st.write(f"**{tipo}**")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Média", f"{dados_tipo['Valor'].mean():.2f}")
                            with col2:
                                st.metric("Máximo", f"{dados_tipo['Valor'].max():.2f}")
                            with col3:
                                st.metric("Mínimo", f"{dados_tipo['Valor'].min():.2f}")
                            with col4:
                                variacao = ((dados_tipo['Valor'].iloc[-1] - dados_tipo['Valor'].iloc[0]) / dados_tipo['Valor'].iloc[0]) * 100
                                st.metric("Variação %", f"{variacao:.2f}%")
                    else:
                        st.warning("Não há dados disponíveis para o período selecionado.")
                else:
                    st.error("Nenhum arquivo de dados encontrado.")
            else:
                # Carrega os dados do arquivo Excel correspondente
                arquivo = f"dados_{tipo_analise.lower().replace(' ', '_')}.xlsx"
                caminho_arquivo = os.path.join('dados_atletas', arquivo)
                
                if os.path.exists(caminho_arquivo):
                    df = pd.read_excel(caminho_arquivo)
                    df['Data'] = pd.to_datetime(df['Data'])
                    
                    # Filtra os dados pelo período selecionado
                    df_filtrado = df[(df['Data'].dt.date >= data_inicio) & (df['Data'].dt.date <= data_fim)]
                    
                    if not df_filtrado.empty:
                        # Gráfico de linha
                        st.subheader(f"Evolução da {tipo_analise}")
                        st.line_chart(df_filtrado.set_index('Data'))
                        
                        # Gráfico de barras
                        st.subheader(f"Distribuição da {tipo_analise}")
                        st.bar_chart(df_filtrado.set_index('Data'))
                        
                        # Gráfico de área
                        st.subheader(f"Progresso da {tipo_analise}")
                        st.area_chart(df_filtrado.set_index('Data'))
                        
                        # Tabela de dados
                        st.subheader("Dados Detalhados")
                        st.dataframe(df_filtrado)
                        
                        # Estatísticas
                        st.subheader("Estatísticas")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Média", f"{df_filtrado['Valor'].mean():.2f}")
                        with col2:
                            st.metric("Máximo", f"{df_filtrado['Valor'].max():.2f}")
                        with col3:
                            st.metric("Mínimo", f"{df_filtrado['Valor'].min():.2f}")
                        with col4:
                            variacao = ((df_filtrado['Valor'].iloc[-1] - df_filtrado['Valor'].iloc[0]) / df_filtrado['Valor'].iloc[0]) * 100
                            st.metric("Variação %", f"{variacao:.2f}%")
                            
                        # Análise de tendência
                        st.subheader("Análise de Tendência")
                        df_filtrado['Dia'] = range(len(df_filtrado))
                        coeficiente = df_filtrado['Valor'].corr(df_filtrado['Dia'])
                        if coeficiente > 0:
                            st.success(f"Tendência positiva (coeficiente: {coeficiente:.2f})")
                        elif coeficiente < 0:
                            st.warning(f"Tendência negativa (coeficiente: {coeficiente:.2f})")
                        else:
                            st.info("Sem tendência clara")
                            
                        # Recomendações baseadas nos dados
                        st.subheader("Recomendações")
                        if tipo_analise == "Força Muscular":
                            if df_filtrado['Valor'].mean() < 70:
                                st.warning("Força muscular abaixo do esperado. Recomenda-se intensificar os exercícios de fortalecimento.")
                            else:
                                st.success("Força muscular dentro do esperado. Continue com o protocolo atual.")
                        elif tipo_analise == "Amplitude de Movimento":
                            if df_filtrado['Valor'].mean() < 60:
                                st.warning("Amplitude de movimento limitada. Recomenda-se focar em exercícios de flexibilidade.")
                            else:
                                st.success("Amplitude de movimento adequada. Continue com o protocolo atual.")
                        elif tipo_analise == "Dor":
                            if df_filtrado['Valor'].mean() > 5:
                                st.warning("Nível de dor elevado. Recomenda-se ajustar a intensidade dos exercícios.")
                            else:
                                st.success("Nível de dor controlado. Continue com o protocolo atual.")
                        elif tipo_analise == "Edema":
                            if df_filtrado['Valor'].mean() > 3:
                                st.warning("Edema persistente. Recomenda-se intensificar a crioterapia e elevação do membro.")
                            else:
                                st.success("Edema controlado. Continue com o protocolo atual.")
                    else:
                        st.warning("Não há dados disponíveis para o período selecionado.")
                else:
                    st.error(f"Arquivo de dados não encontrado: {arquivo}")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}") 