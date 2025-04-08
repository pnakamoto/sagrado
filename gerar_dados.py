import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Função para gerar dados de exemplo
def gerar_dados_exemplo(tipo, n_dias=30):
    # Data inicial
    data_inicial = datetime.now() - timedelta(days=n_dias)
    
    # Gera datas
    datas = [data_inicial + timedelta(days=i) for i in range(n_dias)]
    
    # Gera valores baseados no tipo de análise
    if tipo == "forca_muscular":
        # Valores crescentes com alguma variação
        valores = np.linspace(50, 100, n_dias) + np.random.normal(0, 5, n_dias)
    elif tipo == "amplitude_de_movimento":
        # Valores crescentes com menos variação
        valores = np.linspace(30, 90, n_dias) + np.random.normal(0, 3, n_dias)
    elif tipo == "dor":
        # Valores decrescentes (menos dor com o tempo)
        valores = np.linspace(8, 2, n_dias) + np.random.normal(0, 1, n_dias)
    else:  # edema
        # Valores decrescentes (menos edema com o tempo)
        valores = np.linspace(6, 1, n_dias) + np.random.normal(0, 0.5, n_dias)
    
    # Cria o DataFrame
    df = pd.DataFrame({
        'Data': datas,
        'Valor': valores
    })
    
    # Salva o arquivo
    df.to_excel(f'dados_atletas/dados_{tipo}.xlsx', index=False)

# Gera dados para cada tipo
tipos = ["forca_muscular", "amplitude_de_movimento", "dor", "edema"]
for tipo in tipos:
    gerar_dados_exemplo(tipo)
    print(f"Dados gerados para {tipo}") 