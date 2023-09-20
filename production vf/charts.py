import pandas as pd
import csv
import matplotlib.pyplot as plt
from datetime import datetime

df = pd.read_csv('production_data.csv')
df = df[df.apply(lambda row: len(row) == 4, axis=1)]
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
df = df.dropna(subset=['Data'])
df = df[~df['Acao'].str.isnumeric()]
grouped = df.groupby('Acao')

if not grouped.groups:
    print("Não há ações válidas para criar gráficos.")
else:
    current_time_date = datetime.now().strftime('%Y-%m-%d')
    current_time_time = datetime.now().strftime('%H-%M-%S')

    for i, (name, group) in enumerate(grouped):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(group['Data'], group['Quantidade em estoque'], label='Quantidade em Estoque')
        ax.plot(group['Data'], group['Quantidade Produzida'], label='Quantidade Produzida')
        ax.set_ylabel('Quantidade')
        ax.set_title(f'Quantidade em Estoque e Produzida pelo agente: {name}')
        ax.legend()
        ax.grid(True)
        plt.xlabel('Dia - Horário')
        plt.tight_layout()
        plt.show()
