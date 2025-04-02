import pandas as pd
from datetime import datetime
import logging

def padronizar_data(data_str):
    """
    Converte uma string de data para o formato YYYY-MM-DD.
    Aceita múltiplos formatos de entrada.
    """
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

def padronizar_valor_monetario(valor):
    """
    Converte um valor monetário para float.
    Aceita formatos como 'R$ 1.234,56' ou '1234.56'.
    """
    try:
        if pd.isna(valor):
            return 0.0
        # Remove R$, pontos e espaços, substitui vírgula por ponto
        valor_limpo = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(valor_limpo)
    except:
        return 0.0

def padronizar_booleano(valor):
    """
    Converte valores como 'SIM', 'NÃO', 'S', 'N' para string padronizada.
    """
    if pd.isna(valor):
        return None
    
    valor = str(valor).strip().upper()
    if valor in ['SIM', 'S', 'TRUE', '1', 'T', 'YES', 'Y']:
        return 'SIM'
    elif valor in ['NÃO', 'NAO', 'N', 'FALSE', '0', 'F', 'NO']:
        return 'NÃO'
    return None

def padronizar_dataframe(df):
    """
    Padroniza todas as colunas do DataFrame conforme seus tipos.
    """
    # Colunas de data
    colunas_data = ['data_entrada', 'data_saida']
    
    # Colunas monetárias
    colunas_monetarias = [
        'valor_fechado',
        'taxa_plataforma',
        'taxa_admin',
        'taxa_reloc',
        'limpeza',
        'taxa_indicacao',
        'lucro'
    ]
    
    # Colunas booleanas
    colunas_booleanas = ['recebido']
    
    # Padronizar datas
    for coluna in colunas_data:
        if coluna in df.columns:
            df[coluna] = df[coluna].apply(padronizar_data)
    
    # Padronizar valores monetários
    for coluna in colunas_monetarias:
        if coluna in df.columns:
            df[coluna] = df[coluna].apply(padronizar_valor_monetario)
    
    # Padronizar booleanos
    for coluna in colunas_booleanas:
        if coluna in df.columns:
            df[coluna] = df[coluna].apply(padronizar_booleano)
    
    return df

def validar_dados(df):
    """
    Valida os dados do DataFrame antes de inserir no banco.
    Retorna True se os dados são válidos, False caso contrário.
    """
    try:
        # Verificar se todas as colunas necessárias existem
        colunas_obrigatorias = [
            'data_entrada',
            'data_saida',
            'valor_fechado',
            'recebido'
        ]
        
        for coluna in colunas_obrigatorias:
            if coluna not in df.columns:
                logging.error(f"Coluna obrigatória ausente: {coluna}")
                return False
        
        # Verificar se as datas são válidas
        for coluna in ['data_entrada', 'data_saida']:
            datas_invalidas = df[df[coluna].notna()][coluna].apply(
                lambda x: not isinstance(x, str) or len(x) != 10 or x[4] != '-' or x[7] != '-'
            )
            if datas_invalidas.any():
                logging.error(f"Datas inválidas encontradas na coluna {coluna}")
                return False
        
        # Verificar se os valores monetários são números
        colunas_monetarias = [
            'valor_fechado',
            'taxa_plataforma',
            'taxa_admin',
            'taxa_reloc',
            'limpeza',
            'taxa_indicacao',
            'lucro'
        ]
        
        for coluna in colunas_monetarias:
            if coluna in df.columns:
                valores_invalidos = df[df[coluna].notna()][coluna].apply(
                    lambda x: not isinstance(x, (int, float))
                )
                if valores_invalidos.any():
                    logging.error(f"Valores monetários inválidos encontrados na coluna {coluna}")
                    return False
        
        return True
    except Exception as e:
        logging.error(f"Erro durante a validação dos dados: {e}")
        return False 