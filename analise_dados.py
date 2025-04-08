import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import os
import shutil
import duckdb

def gerar_relatorio_paciente(paciente_id, conn):
    """Gera um relatório detalhado do progresso do paciente"""
    # Busca dados do paciente
    paciente = conn.execute(f"""
        SELECT nome, data_cirurgia, data_cadastro 
        FROM pacientes 
        WHERE id = {paciente_id}
    """).fetchone()
    
    progresso = conn.execute(f"""
        SELECT p.*, f.fase as nome_fase
        FROM progresso p
        JOIN fases_reabilitacao f ON p.fase = f.id
        WHERE p.paciente_id = {paciente_id}
        ORDER BY p.data_inicio
    """).fetchdf()
    
    # Cria o relatório
    relatorio = {
        "Dados do Paciente": {
            "Nome": paciente[0],
            "Data da Cirurgia": paciente[1],
            "Data de Cadastro": paciente[2]
        },
        "Progresso": progresso.to_dict('records')
    }
    
    return relatorio

def gerar_grafico_progresso(paciente_id, conn):
    """Gera gráficos de progresso do paciente"""
    progresso = conn.execute(f"""
        SELECT p.*, f.fase as nome_fase
        FROM progresso p
        JOIN fases_reabilitacao f ON p.fase = f.id
        WHERE p.paciente_id = {paciente_id}
        ORDER BY p.data_inicio
    """).fetchdf()
    
    # Gráfico de barras para fases
    fig_fases = px.bar(progresso, 
                      x='nome_fase', 
                      y='status',
                      title='Progresso por Fase',
                      color='status')
    
    # Gráfico de linha para tempo em cada fase
    progresso['duracao'] = (pd.to_datetime(progresso['data_fim']) - pd.to_datetime(progresso['data_inicio'])).dt.days
    fig_tempo = px.line(progresso,
                       x='nome_fase',
                       y='duracao',
                       title='Duração em Cada Fase')
    
    return fig_fases, fig_tempo

def gerar_analise_estatistica(conn):
    """Gera análise estatística de todos os pacientes"""
    # Tempo médio por fase
    tempo_fase = conn.execute("""
        SELECT f.fase, 
               AVG(DATEDIFF('day', p.data_inicio, p.data_fim)) as tempo_medio
        FROM progresso p
        JOIN fases_reabilitacao f ON p.fase = f.id
        WHERE p.data_fim IS NOT NULL
        GROUP BY f.fase
    """).fetchdf()
    
    # Taxa de sucesso por fase
    sucesso_fase = conn.execute("""
        SELECT f.fase,
               COUNT(CASE WHEN p.status = 'Concluído' THEN 1 END) * 100.0 / COUNT(*) as taxa_sucesso
        FROM progresso p
        JOIN fases_reabilitacao f ON p.fase = f.id
        GROUP BY f.fase
    """).fetchdf()
    
    return tempo_fase, sucesso_fase

def exportar_dados(conn, formato='excel'):
    """Exporta dados do banco para diferentes formatos"""
    # Busca todos os dados
    pacientes = conn.execute("SELECT * FROM pacientes").fetchdf()
    progresso = conn.execute("""
        SELECT p.*, f.fase as nome_fase
        FROM progresso p
        JOIN fases_reabilitacao f ON p.fase = f.id
    """).fetchdf()
    
    # Cria diretório de exportação se não existir
    if not os.path.exists('exportacoes'):
        os.makedirs('exportacoes')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if formato == 'excel':
        with pd.ExcelWriter(f'exportacoes/dados_{timestamp}.xlsx') as writer:
            pacientes.to_excel(writer, sheet_name='Pacientes', index=False)
            progresso.to_excel(writer, sheet_name='Progresso', index=False)
    elif formato == 'csv':
        pacientes.to_csv(f'exportacoes/pacientes_{timestamp}.csv', index=False)
        progresso.to_csv(f'exportacoes/progresso_{timestamp}.csv', index=False)
    
    return f'exportacoes/dados_{timestamp}.{formato}'

def fazer_backup(conn):
    """Realiza backup do banco de dados"""
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'backups/backup_{timestamp}.db'
    
    # Cria uma nova conexão para o backup
    backup_conn = duckdb.connect(backup_path)
    
    # Copia todas as tabelas
    backup_conn.execute("""
        CREATE TABLE pacientes AS SELECT * FROM conn.pacientes;
        CREATE TABLE progresso AS SELECT * FROM conn.progresso;
        CREATE TABLE fases_reabilitacao AS SELECT * FROM conn.fases_reabilitacao;
    """)
    
    backup_conn.close()
    return backup_path 