import csv
import matplotlib.pyplot as plt
from datetime import datetime

timestamps = []
quantities_delivered = []

with open('truck_data.csv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    next(csv_reader)
    for row in csv_reader:
        timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        quantity = int(row[2])
        timestamps.append(timestamp)
        quantities_delivered.append(quantity)

plt.figure(figsize=(10, 6))
plt.plot(timestamps, quantities_delivered, marker='o', linestyle='-')
plt.title('Quantidade Entregue ao Longo do Tempo')
plt.xlabel('Timestamp')
plt.ylabel('Quantidade Entregue')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('truck_chart.png')

plt.show()
