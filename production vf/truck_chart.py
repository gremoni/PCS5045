import csv
import matplotlib.pyplot as plt
timestamps = []
deliver_amounts = []

with open('truck_data.csv', 'r') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        timestamps.append(row['Data e Hora'])
        deliver_amounts.append(int(row['Quantidade Entregue']))

plt.figure(figsize=(10, 6))
#plt.plot(timestamps, deliver_amounts, marker='o', linestyle='-', color='b')
plt.bar(timestamps, deliver_amounts, color='b')
plt.title('Entrega de Quantidade ao Longo do Tempo')
plt.xlabel('Data e Hora')
plt.ylabel('Quantidade Entregue')
plt.xticks(rotation=45)
plt.grid(True)

plt.tight_layout()
plt.show()
