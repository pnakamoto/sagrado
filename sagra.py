# SAGRA - Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas
# Autor: Anselmo Borges, Pedro Bala Pascal, Luis Eduardo dos Santos
# Data: 16/03/2025
# Descrição: Sistema para acompanhamento e gerenciamento da reabilitação de atletas
#            de rugby após cirurgia de reconstrução do LCA.

# Importação das bibliotecas necessárias
import streamlit as st
import duckdb
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import pandas as pd

# Configuração da página Streamlit
st.set_page_config(
    page_title="SAGRA - Reabilitação LCA",
    page_icon="🏉",
    layout="wide"
)

# Função de autenticação
def check_password():
    """Retorna `True` se o usuário tiver a senha correta."""
    def password_entered():
        """Verifica se a senha está correta."""
        if st.session_state["username"] in st.session_state["credentials"]:
            if st.session_state["password"] == st.session_state["credentials"][st.session_state["username"]]:
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Não armazena a senha
            else:
                st.session_state["password_correct"] = False

    # Retorna `True` se o usuário tiver a senha correta.
    if "password_correct" not in st.session_state:
        # Primeira execução, mostra o formulário de login
        st.text_input("Usuário", on_change=password_entered, key="username")
        st.text_input("Senha", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("Usuário ou senha incorretos")
        return False
    return st.session_state["password_correct"]

# Credenciais (em um ambiente real, isso deveria estar em um arquivo de configuração seguro)
if "credentials" not in st.session_state:
    st.session_state["credentials"] = {
        "admin": "admin123",
        "user": "user123"
    }

# Verifica a autenticação
if not check_password():
    st.stop()

def carregar_protocolos():
    """Carrega todos os protocolos de lesões da pasta planilhas_originais"""
    protocolos = {}
    if not os.path.exists('planilhas_originais'):
        st.error("Diretório 'planilhas_originais' não encontrado!")
        os.makedirs('planilhas_originais')
        return protocolos
    
    arquivos_excel = [f for f in os.listdir('planilhas_originais') if f.endswith(('.xlsx', '.xls'))]
    
    if not arquivos_excel:
        st.error("Nenhum arquivo Excel encontrado no diretório 'planilhas_originais'!")
        return protocolos
    
    st.info(f"Encontrados {len(arquivos_excel)} arquivos Excel para processar")
    
    for arquivo in arquivos_excel:
        try:
            caminho_arquivo = os.path.join('planilhas_originais', arquivo)
            st.write(f"Tentando carregar: {arquivo}")
            
            # Tentar ler o arquivo
            df = pd.read_excel(caminho_arquivo)
            
            # Verificar se o DataFrame tem dados
            if df.empty:
                st.warning(f"Arquivo {arquivo} está vazio!")
                continue
                
            # Verificar se tem pelo menos 2 colunas
            if len(df.columns) < 2:
                st.warning(f"Arquivo {arquivo} não tem colunas suficientes!")
                continue
            
            # Verificar se as colunas têm dados numéricos
            if not pd.to_numeric(df.iloc[:, 0], errors='coerce').notna().any():
                st.warning(f"Primeira coluna do arquivo {arquivo} não contém números válidos!")
                continue
                
            if not pd.to_numeric(df.iloc[:, 1], errors='coerce').notna().any():
                st.warning(f"Segunda coluna do arquivo {arquivo} não contém números válidos!")
                continue
            
            nome_protocolo = os.path.splitext(arquivo)[0]
            protocolos[nome_protocolo] = df
            st.success(f"Protocolo {nome_protocolo} carregado com sucesso!")
            
        except Exception as e:
            st.error(f"Erro ao carregar protocolo {arquivo}: {str(e)}")
            st.error("Detalhes do erro:", exc_info=True)
    
    if not protocolos:
        st.error("Nenhum protocolo foi carregado com sucesso!")
    else:
        st.success(f"Total de protocolos carregados: {len(protocolos)}")
    
    return protocolos

def processar_dados_protocolo(df, data_inicio):
    """Processa os dados do protocolo para gerar datas e valores"""
    try:
        st.write("Iniciando processamento dos dados do protocolo...")
        
        # Mostrar informações sobre o DataFrame
        st.write(f"Formato do DataFrame: {df.shape}")
        st.write("Primeiras linhas do DataFrame:")
        st.dataframe(df.head())
        
        # Remover linhas com valores NaN
        df = df.dropna()
        st.write(f"Linhas após remover NaN: {len(df)}")
        
        # Verificar se há dados suficientes
        if len(df) < 2:
            st.error("A planilha não contém dados suficientes para gerar o gráfico")
            return None
        
        # Tentar converter as colunas para números
        try:
            dias = pd.to_numeric(df.iloc[:, 0], errors='coerce')
            valores = pd.to_numeric(df.iloc[:, 1], errors='coerce')
        except Exception as e:
            st.error(f"Erro ao converter colunas para números: {str(e)}")
            return None
        
        # Remover linhas com valores inválidos
        dados_validos = pd.DataFrame({
            'Dias': dias,
            'Valor': valores
        }).dropna()
        
        st.write(f"Linhas com dados válidos: {len(dados_validos)}")
        
        # Verificar se há dados válidos após a filtragem
        if len(dados_validos) < 2:
            st.error("Não há dados válidos suficientes após a filtragem")
            return None
        
        # Gerar datas baseadas na data de início
        datas = [data_inicio + timedelta(days=int(dia)) for dia in dados_validos['Dias']]
        
        resultado = pd.DataFrame({
            'Data': datas,
            'Valor': dados_validos['Valor']
        })
        
        st.write("Dados processados com sucesso!")
        st.write("Primeiras linhas do resultado:")
        st.dataframe(resultado.head())
        
        return resultado
        
    except Exception as e:
        st.error(f"Erro ao processar dados do protocolo: {str(e)}")
        st.error("Detalhes do erro:", exc_info=True)
        st.error("Verifique se a planilha está no formato correto: primeira coluna com dias (números) e segunda coluna com valores (números)")
        return None

# Carregar protocolos apenas uma vez
protocolos = carregar_protocolos()

# Título principal
st.title('SAGRA - Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas')

# Barra lateral para seleção de protocolo
with st.sidebar:
    st.subheader('Seleção de Protocolo')
    protocolo_selecionado = st.selectbox(
        'Escolha o Protocolo de Lesão',
        options=[''] + list(protocolos.keys()),
        key='protocolo_sidebar'
    )
    
    if protocolo_selecionado:
        st.success(f'Protocolo selecionado: {protocolo_selecionado}')

# Inicialização do banco de dados
def init_database():
    """Inicializa a conexão com o banco de dados DuckDB"""
    if not os.path.exists('SAGRA.db'):
        st.error("Banco de dados SAGRA.db não encontrado. Verifique se o arquivo existe no diretório do projeto.")
        st.stop()
    return duckdb.connect('SAGRA.db')

# Inicializa a conexão com o banco de dados
conn = init_database()

# Interface para entrada de dados do atleta
nome_atleta = st.text_input('Nome do Atleta')

# Seletor de data da cirurgia (padrão: 140 dias atrás)
data_cirurgia = st.date_input(
    "Data da Cirurgia",
    value=(datetime.now().date() - timedelta(days=140)),
    min_value=datetime(2023, 1, 1).date(),
    max_value=datetime.now().date()
)

# Processamento principal após inserção dos dados básicos
if nome_atleta and data_cirurgia:
    # Registra ou atualiza o paciente
    try:
        # Registra ou atualiza o paciente
        conn.execute("""
            INSERT INTO pacientes (nome, data_cirurgia)
            VALUES (?, ?)
            ON CONFLICT (nome) DO UPDATE SET
                data_cirurgia = excluded.data_cirurgia
            RETURNING id
        """, [nome_atleta, data_cirurgia])
        
        # Obtém o ID do paciente
        paciente_id = conn.execute("""
            SELECT id FROM pacientes WHERE nome = ?
        """, [nome_atleta]).fetchone()[0]
    except Exception as e:
        st.error(f"Erro ao registrar paciente: {str(e)}")
        st.stop()
    
    # Função auxiliar para extrair número de dias do período
    def extrair_dias(periodo):
        """
        Extrai o número de dias de um período especificado no formato 'X a Y dias' ou 'após X dias'
        Args:
            periodo (str): String contendo o período
        Returns:
            int: Número de dias do período
        """
        if 'após' in periodo:
            return int(periodo.split(' ')[1])
        else:
            dias = periodo.split(' a ')
            return int(dias[-1].split(' ')[0])
    
    # Busca as fases do banco de dados
    fases_df = conn.execute("""
        SELECT * FROM fases_reabilitacao
        ORDER BY id
    """).df()
    
    # Cálculo das datas de cada fase
    dados_fases = []
    data_atual = data_cirurgia
    
    # Processamento de cada fase
    for _, row in fases_df.iterrows():
        dias = extrair_dias(row['periodo_aproximado'])
        
        # Cálculo das datas de início e fim de cada fase
        if row['fase'] == 'Fase 1':
            data_inicio = data_atual
            data_fim = data_inicio + timedelta(days=dias)
        elif row['fase'] == 'Alta':
            data_inicio = data_cirurgia + timedelta(days=240)
            data_fim = data_inicio + timedelta(days=30)
        else:
            data_inicio = data_atual + timedelta(days=1)
            data_fim = data_inicio + timedelta(days=dias - 1)
        
        # Processamento dos tratamentos
        tratamentos = row['tratamentos'].split(',') if row['tratamentos'] else []
        
        # Montagem do dicionário de dados da fase
        dados_fases.append({
            'Fase': row['fase'],
            'Data Início': data_inicio.strftime('%d/%m/%Y'),
            'Data Fim': data_fim.strftime('%d/%m/%Y'),
            'Duração (dias)': dias if row['fase'] != 'Alta' else 'Contínuo',
            'Atividades': row['atividades_liberadas'],
            'Testes': row['testes_especificos'],
            'Tratamentos': tratamentos,
            'Preparacao_Fisica': row['preparacao_fisica'],
            'tecnicas_rugby': row['tecnicas_rugby']
        })
        data_atual = data_fim
    
    # Exibição das informações do paciente
    st.subheader(f'Cronograma de Reabilitação para: {nome_atleta}')
    
    # Cálculo e exibição de datas importantes
    data_alta = data_cirurgia + timedelta(days=240)
    col1, col2 = st.columns(2)
    with col1:
        st.info(f'**Data da Cirurgia:** {data_cirurgia.strftime("%d/%m/%Y")}')
    with col2:
        st.info(f'**Previsão de Alta:** {data_alta.strftime("%d/%m/%Y")}')
    
    # Exibição da tabela de fases
    st.subheader('Cronograma Detalhado:')
    st.dataframe(
        dados_fases,
        column_config={
            "Fase": st.column_config.TextColumn("Fase"),
            "Data Início": st.column_config.TextColumn("Início"),
            "Data Fim": st.column_config.TextColumn("Fim"),
            "Duração (dias)": st.column_config.TextColumn("Dias"),
            "Atividades": st.column_config.TextColumn("Atividades Liberadas", width="large"),
            "Testes": st.column_config.TextColumn("Testes Específicos", width="medium")
        }
    )
    
    # Seção de detalhamento das fases
    st.subheader('Detalhamento das Fases:')
    for fase in dados_fases:
        with st.expander(f"{fase['Fase']} ({fase['Data Início']} a {fase['Data Fim']})"):
            col1, col2, col3 = st.columns(3)
            
            # Coluna 1: Atividades e Testes
            with col1:
                st.write("**Atividades Liberadas:**")
                st.write(fase['Atividades'])
                st.write("**Testes Específicos:**")
                st.write(fase['Testes'] if fase['Testes'] != '-' else "Nenhum teste específico nesta fase")
            
            # Coluna 2: Tratamentos
            with col2:
                st.write("**Tratamentos e Exercícios:**")
                for tratamento in fase['Tratamentos']:
                    st.write(f"- {tratamento.strip()}")
            
            # Coluna 3: Preparação Física
            with col3:
                st.write("**Preparação Física:**")
                for exercicio in fase['Preparacao_Fisica'].split(','):
                    status = exercicio.strip()
                    if '(Completo)' in status:
                        st.success(f"- {status}")
                    elif '(Restrição)' in status:
                        st.error(f"- {status}")
                    elif '(Progressão)' in status or 'Progressão' in status:
                        st.warning(f"- {status}")
                    else:
                        st.write(f"- {status}")
    
    # Seção de progresso do tratamento
    st.subheader('Progresso do Tratamento')
    dias_desde_cirurgia = (datetime.now().date() - data_cirurgia).days
    progresso = min(100, (dias_desde_cirurgia / 240) * 100)
    
    # Barra de progresso
    st.progress(progresso / 100)
    st.write(f"Progresso: {progresso:.1f}% ({dias_desde_cirurgia} dias desde a cirurgia)")
    
    # Identificação da fase atual
    fase_atual = None
    for fase in dados_fases:
        data_inicio = datetime.strptime(fase['Data Início'], '%d/%m/%Y').date()
        data_fim = datetime.strptime(fase['Data Fim'], '%d/%m/%Y').date()
        if data_inicio <= datetime.now().date() <= data_fim:
            fase_atual = fase
            st.success(f"**Fase Atual:** {fase['Fase']}")
            
            # Registra progresso no banco de dados
            conn.execute("""
                INSERT INTO progresso (paciente_id, fase, data_inicio, data_fim, status)
                VALUES (?, ?, ?, ?, 'Em andamento')
                ON CONFLICT (paciente_id, fase, data_inicio) DO UPDATE
                SET status = 'Em andamento',
                    data_fim = excluded.data_fim
            """, [paciente_id, fase['Fase'], data_inicio, data_fim])
            
            break

    # Relatório detalhado de acompanhamento
    st.subheader('Relatório de Acompanhamento Detalhado')
    
    # Métricas gerais
    semana_atual = dias_desde_cirurgia // 7
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Semana Atual", f"{semana_atual}ª semana")
    with col2:
        st.metric("Dias Pós-Cirurgia", f"{dias_desde_cirurgia} dias")
    with col3:
        st.metric("Progresso Total", f"{progresso:.1f}%")
    
    # Gráfico de evolução das atividades
    st.subheader('Evolução das Atividades')
    data_referencia = data_cirurgia + timedelta(days=dias_desde_cirurgia)
    fases_ate_agora = [f for f in dados_fases if datetime.strptime(f['Data Fim'], '%d/%m/%Y').date() <= data_referencia]
    
    # Gráfico de linha do tempo
    fig_timeline = go.Figure()
    for fase in fases_ate_agora:
        fig_timeline.add_trace(go.Scatter(
            x=[fase['Data Início'], fase['Data Fim']],
            y=[fase['Fase'], fase['Fase']],
            mode='lines',
            line=dict(color='green', width=20),
            name=fase['Fase']
        ))
    
    fig_timeline.update_layout(
        title='Linha do Tempo das Fases',
        xaxis_title='Data',
        yaxis_title='Fase',
        showlegend=False
    )
    st.plotly_chart(fig_timeline)
    
    # Resumo das atividades atuais
    if fase_atual:
        st.subheader('Resumo das Atividades Atuais')
        
        # Exibição do resumo em colunas
        col1, col2 = st.columns(2)
        with col1:
            st.write("**🏃 Atividades Liberadas**")
            st.info(fase_atual['Atividades'])
            st.write("**🎯 Objetivos da Fase**")
            st.success(f"- Fase: {fase_atual['Fase']}\n- Duração: {fase_atual['Duração (dias)']} dias")
        with col2:
            st.write("**📊 Testes e Avaliações**")
            st.warning(fase_atual['Testes'] if fase_atual['Testes'] != '-' else "Nenhum teste específico nesta fase")
        
        # Análise dos exercícios de preparação física
        st.subheader('Status dos Exercícios de Preparação Física')
        exercicios = fase_atual['Preparacao_Fisica'].split(',')
        status_exercicios = {
            'Completo': len([ex for ex in exercicios if '(Completo)' in ex]),
            'Em Progressão': len([ex for ex in exercicios if '(Progressão)' in ex or 'Progressão' in ex]),
            'Com Restrição': len([ex for ex in exercicios if '(Restrição)' in ex])
        }
        
        # Gráfico de pizza dos status dos exercícios
        fig_pizza = px.pie(
            values=list(status_exercicios.values()),
            names=list(status_exercicios.keys()),
            title='Distribuição dos Exercícios por Status',
            color_discrete_map={
                'Completo': 'green',
                'Em Progressão': 'orange',
                'Com Restrição': 'red'
            }
        )
        st.plotly_chart(fig_pizza)
        
        # Seção de técnicas de rugby
        st.subheader('Técnicas de Rugby - Status Atual')
        tecnicas = fase_atual['tecnicas_rugby'].split(',')
        
        # Organização das técnicas por categorias
        categorias = {
            'Tackle': [],
            'Passe': [],
            'Scrum': [],
            'Ruck/Maul': [],
            'Treinamento': [],
            'Outros': []
        }
        
        # Processamento e categorização das técnicas
        for tecnica in tecnicas:
            nome, status = tecnica.split(':')
            status = int(status)
            
            # Determinação da categoria
            if 'Tackle' in nome:
                categoria = 'Tackle'
            elif 'Passe' in nome:
                categoria = 'Passe'
            elif 'Scrum' in nome:
                categoria = 'Scrum'
            elif 'Ruck' in nome or 'Maul' in nome:
                categoria = 'Ruck/Maul'
            elif 'treinamento' in nome.lower() or 'treino' in nome.lower():
                categoria = 'Treinamento'
            else:
                categoria = 'Outros'
            
            # Formatação do status
            if status == 1:
                status_text = "🔴 Proibido"
            elif status == 2:
                status_text = "🟡 Moderado"
            else:
                status_text = "🟢 Liberado"
            
            categorias[categoria].append(f"{nome.strip()}: {status_text}")
        
        # Exibição das técnicas por categoria
        col1, col2 = st.columns(2)
        with col1:
            st.write("**🏈 Técnicas de Tackle**")
            for tecnica in categorias['Tackle']:
                st.write(f"- {tecnica}")
            
            st.write("**🤾 Técnicas de Passe**")
            for tecnica in categorias['Passe']:
                st.write(f"- {tecnica}")
            
            st.write("**👥 Técnicas de Scrum**")
            for tecnica in categorias['Scrum']:
                st.write(f"- {tecnica}")
        
        with col2:
            st.write("**💪 Ruck e Maul**")
            for tecnica in categorias['Ruck/Maul']:
                st.write(f"- {tecnica}")
            
            st.write("**🏃 Treinamento**")
            for tecnica in categorias['Treinamento']:
                st.write(f"- {tecnica}")
            
            if categorias['Outros']:
                st.write("**⚡ Outras Técnicas**")
                for tecnica in categorias['Outros']:
                    st.write(f"- {tecnica}")
        
        # Gráfico de evolução das técnicas
        st.subheader('Evolução das Técnicas')
        status_count = {
            'Proibido': len([t for t in tecnicas if t.split(':')[1] == '1']),
            'Moderado': len([t for t in tecnicas if t.split(':')[1] == '2']),
            'Liberado': len([t for t in tecnicas if t.split(':')[1] == '3'])
        }
        
        # Gráfico de barras dos status das técnicas
        fig_tecnicas = px.bar(
            x=list(status_count.keys()),
            y=list(status_count.values()),
            title='Distribuição do Status das Técnicas',
            labels={'x': 'Status', 'y': 'Quantidade de Técnicas'},
            color=list(status_count.keys()),
            color_discrete_map={
                'Proibido': 'red',
                'Moderado': 'orange',
                'Liberado': 'green'
            }
        )
        st.plotly_chart(fig_tecnicas)
        
        # Recomendações finais
        st.subheader('Recomendações e Próximos Passos')
        st.write("""
        **Pontos de Atenção:**
        - Continue seguindo rigorosamente o protocolo de exercícios
        - Mantenha o acompanhamento regular com a equipe de reabilitação
        - Observe qualquer sinal de dor ou desconforto anormal
        
        **Próximos Objetivos:**
        - Progredir nos exercícios marcados como 'Em Progressão'
        - Preparar-se para os próximos testes e avaliações
        - Manter o fortalecimento muscular e ganho de resistência
        """)

# Modificar a seção de gráficos após a seleção do protocolo
if protocolo_selecionado:
    st.subheader(f'Análise do Protocolo: {protocolo_selecionado}')
    
    # Processar dados do protocolo
    df_protocolo = protocolos[protocolo_selecionado]
    dados_processados = processar_dados_protocolo(df_protocolo, data_cirurgia)
    
    if dados_processados is not None and len(dados_processados) > 0:
        # Converter datas para datetime
        dados_processados['Data'] = pd.to_datetime(dados_processados['Data'])
        
        # Criar figura usando go.Figure em vez de px.line
        fig_protocolo = go.Figure()
        
        # Adicionar linha principal
        fig_protocolo.add_trace(go.Scatter(
            x=dados_processados['Data'],
            y=dados_processados['Valor'],
            mode='lines+markers',
            name='Evolução'
        ))
        
        # Adicionar linha vertical para data atual usando shapes
        data_atual = datetime.now()
        fig_protocolo.add_shape(
            type="line",
            x0=data_atual,
            y0=dados_processados['Valor'].min(),
            x1=data_atual,
            y1=dados_processados['Valor'].max(),
            line=dict(
                color="red",
                width=1,
                dash="dash"
            ),
            name="Data Atual"
        )
        
        # Adicionar anotação para a data atual
        fig_protocolo.add_annotation(
            x=data_atual,
            y=dados_processados['Valor'].max(),
            text="Data Atual",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        )
        
        # Configurar o layout do gráfico
        fig_protocolo.update_layout(
            title=f'Evolução do Protocolo {protocolo_selecionado}',
            xaxis_title="Data",
            yaxis_title="Valor do Indicador",
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig_protocolo)
        
        # Métricas do protocolo
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Valor Atual",
                f"{dados_processados['Valor'].iloc[-1]:.2f}"
            )
        with col2:
            st.metric(
                "Valor Inicial",
                f"{dados_processados['Valor'].iloc[0]:.2f}"
            )
        with col3:
            variacao = ((dados_processados['Valor'].iloc[-1] - dados_processados['Valor'].iloc[0]) / 
                       dados_processados['Valor'].iloc[0] * 100)
            st.metric(
                "Variação Total",
                f"{variacao:.1f}%"
            )
        
        # Tabela de dados
        st.subheader('Dados Detalhados do Protocolo')
        st.dataframe(dados_processados)
    else:
        st.error("Não foi possível processar os dados do protocolo. Verifique o formato da planilha.") 