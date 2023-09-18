import matplotlib.pyplot as plt
import csv
with open('slicer_stock_data.csv', 'r') as slicer_csv_file:
    slicer_reader = csv.reader(slicer_csv_file)
    next(slicer_reader)  # Ignora o cabeçalho
    slicer_data = list(slicer_reader)
with open('fryer_stock_data.csv', 'r') as fryer_csv_file:
    fryer_reader = csv.reader(fryer_csv_file)
    next(fryer_reader)  # Ignora o cabeçalho
    fryer_data = list(fryer_reader)
slicer_dates = [row[0] for row in slicer_data]
slicer_stock = [int(row[1]) for row in slicer_data]
fryer_dates = [row[0] for row in fryer_data]
fryer_stock = [int(row[1]) for row in fryer_data]
plt.figure(figsize=(12, 6))
plt.plot(slicer_dates, slicer_stock, label='Estoque do Slicer', marker='o', linestyle='-', color='blue')
plt.plot(fryer_dates, fryer_stock, label='Estoque do Fryer', marker='o', linestyle='-', color='red')
plt.xlabel('Data')
plt.ylabel('Estoque')
plt.title('Estoque do Slicer e do Fryer ao longo do Tempo')
plt.xticks(rotation=45)
plt.legend()

plt.tight_layout()
plt.show()
