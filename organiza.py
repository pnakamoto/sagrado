import duckdb
import pandas as pd
from datetime import datetime
import logging
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def converter_data(data_str):
    try:
        if pd.isna(data_str):
            return None
        
        # Lista de formatos possíveis de data
        formatos = [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%y',
            '%Y/%m/%d'
        ]
        
        # Tentar cada formato até encontrar um que funcione
        for formato in formatos:
            try:
                return datetime.strptime(str(data_str).strip(), formato).strftime('%Y-%m-%d')
            except:
                continue
        
        logging.warning(f"Formato de data não reconhecido: {data_str}")
        return None
    except Exception as e:
        logging.error(f"Erro ao converter data {data_str}: {e}")
        return None

def padronizar_datas():
    conn = None
    try:
        # Conectar ao banco de dados
        logging.info("Conectando ao banco de dados DuckDB...")
        conn = duckdb.connect(database='airbnb.duckdb')
        
        # Ler os dados atuais
        logging.info("Lendo dados da tabela...")
        df = conn.execute("SELECT * FROM despesas_receitas").fetchdf()
        
        # Colunas de data para padronizar
        colunas_data = ['data_entrada', 'data_saida']
        
        # Criar uma nova tabela temporária com a estrutura correta
        logging.info("Criando tabela temporária...")
        conn.execute("""
            CREATE TEMP TABLE temp_despesas_receitas AS 
            SELECT * FROM despesas_receitas 
            WHERE 1=0
        """)
        
        # Converter cada coluna de data no DataFrame
        for coluna in colunas_data:
            if coluna in df.columns:
                logging.info(f"Padronizando formato da coluna {coluna}...")
                df[coluna] = df[coluna].apply(converter_data)
        
        # Inserir dados convertidos na tabela temporária
        logging.info("Inserindo dados na tabela temporária...")
        conn.execute("INSERT INTO temp_despesas_receitas SELECT * FROM df")
        
        # Alterar o tipo das colunas para DATE na tabela temporária
        for coluna in colunas_data:
            if coluna in df.columns:
                logging.info(f"Alterando tipo da coluna {coluna} para DATE...")
                conn.execute(f"ALTER TABLE temp_despesas_receitas ALTER COLUMN {coluna} TYPE DATE")
        
        # Substituir a tabela original pela temporária
        logging.info("Substituindo tabela original...")
        conn.execute("DROP TABLE despesas_receitas")
        conn.execute("ALTER TABLE temp_despesas_receitas RENAME TO despesas_receitas")
        
        # Verificar resultado
        logging.info("Verificando dados padronizados...")
        resultado = conn.execute("SELECT * FROM despesas_receitas").fetchdf()
        print("\nDados após padronização:")
        print(resultado)
        
        logging.info("Processo de padronização concluído com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro durante a padronização: {e}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except:
                pass

if __name__ == "__main__":
    padronizar_datas() 