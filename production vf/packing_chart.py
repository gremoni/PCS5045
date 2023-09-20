import csv
import matplotlib.pyplot as plt
import pandas as pd
df = pd.read_csv('packing_data.csv', parse_dates=['Data'])
df_packing = df[df['Atividade'] == 'PACKING']
df_boxing = df[df['Atividade'] == 'BOXING']
plt.figure(figsize=(12, 6))
plt.plot(df_packing['Data'], df_packing['Quantidade Processada'], label='Quantidade Processada (PACKING)', color='b')
plt.plot(df_boxing['Data'], df_boxing['Quantidade em Estoque'], label='Quantidade em Estoque (BOXING)', color='g')
plt.xlabel('Data e Hora')
plt.ylabel('Quantidade')
plt.title('Evolução da Quantidade Processada e em Estoque ao Longo do Tempo')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
