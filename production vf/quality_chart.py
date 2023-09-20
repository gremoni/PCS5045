import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("QualityControl_data.csv")
fig, ax = plt.subplots(figsize=(12, 6))
soma_quantidade_processada = df.groupby("Acao")["Quantidade Processada"].sum()
soma_quantidade_processada.plot(kind="bar", ax=ax)
ax.set_title("Soma da Quantidade Processada por Ação")
ax.set_xlabel("Ação")
ax.set_ylabel("Soma da Quantidade Processada")
plt.tight_layout()
plt.show()
fig, ax = plt.subplots(figsize=(8, 8))
soma_quantidade_processada = df.groupby("Acao")["Quantidade Processada"].sum()
soma_quantidade_processada.plot(kind="pie", autopct='%1.1f%%', ax=ax)
ax.set_title("Porcentagem da Quantidade Processada por Ação")
plt.tight_layout()
plt.show()