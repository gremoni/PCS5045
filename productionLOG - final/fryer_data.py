import csv
import matplotlib.pyplot as plt
from datetime import datetime

dates = []
quantities = []

with open('fryer_data.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        date = datetime.strptime(row['Data'], '%Y-%m-%d %H:%M:%S')
        quantity = int(row['Quantidade Produzida'])
        dates.append(date)
        quantities.append(quantity)

plt.figure(figsize=(10, 6))
plt.plot(dates, quantities, marker='o', linestyle='-')
plt.title('Produção ao longo do tempo')
plt.xlabel('Data e Hora')
plt.ylabel('Quantidade Produzida')
plt.grid(True)

plt.gcf().autofmt_xdate()
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()
