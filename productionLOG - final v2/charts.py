import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('production_data.csv')
df = df[df.apply(lambda row: len(row) == 4, axis=1)]
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
df = df.dropna(subset=['Data'])
df = df[~df['acao'].str.isnumeric()]
grouped = df.groupby('acao')

if not grouped.groups:
    print("Não há ações válidas para criar gráficos.")
else:
    fig, axes = plt.subplots(len(grouped), 1, figsize=(10, 6 * len(grouped)), sharex=True)

    for i, (name, group) in enumerate(grouped):
        ax = axes[i]
        ax.plot(group['Data'], group['Quantidade em estoque'], label='Quantidade em Estoque')
        ax.plot(group['Data'], group['Quantidade Produzida'], label='Quantidade Produzida')
        ax.set_ylabel('Quantidade')
        ax.set_title(f'Quantidade em Estoque e Produzida pelo agente: {name}')
        ax.legend()
        ax.grid(True)

    plt.xlabel('Data')
    plt.tight_layout()
    plt.show()
