import matplotlib.pyplot as plt

exec(open('fryer_data.py').read())
exec(open('truck_chart.py').read())
exec(open('production_chart.py').read())
plt.figure(figsize=(15, 10))

plt.subplot(2, 2, 1)  # 2 linhas, 2 colunas, primeiro gráfico
plt.title('Produção ao longo do tempo')
plt.xlabel('Data e Hora')
plt.ylabel('Quantidade Produzida')

plt.subplot(2, 2, 2)
plt.title('Fritadeira')
plt.xlabel('Data e Hora')
plt.ylabel('Quantidade Produzida')

plt.subplot(2, 1, 2)
plt.title('Quantidade Entregue ao Longo do Tempo')
plt.xlabel('Timestamp')
plt.ylabel('Quantidade Entregue')

plt.tight_layout()
plt.show()
