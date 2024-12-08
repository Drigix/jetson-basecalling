import pandas as pd
import matplotlib.pyplot as plt

# Wczytanie danych z pliku CSV
data = pd.read_csv('jetson_metrics.csv')

# Grupowanie danych po rozmiarze pliku
grouped_data = data.groupby('file_size')

# Ustawienie rozmiaru wykresu
plt.figure(figsize=(12, 8))

# Tworzenie wykresów dla każdego rozmiaru pliku
for size, group in grouped_data:
    # Tworzymy wykresy dla CPU, GPU i Power AVG
    plt.plot(group['time'], group['cpu1'], label=f'CPU1 - {size} MB', marker='o')
    plt.plot(group['time'], group['cpu2'], label=f'CPU2 - {size} MB', marker='o')
    plt.plot(group['time'], group['cpu3'], label=f'CPU3 - {size} MB', marker='o')
    plt.plot(group['time'], group['cpu4'], label=f'CPU4 - {size} MB', marker='o')
    plt.plot(group['time'], group['gpu'], label=f'GPU - {size} MB', marker='o')
    # plt.plot(group['time'], group['ram'], label=f'RAM - {size} MB', marker='o')
    # plt.plot(group['time'], group['power_avg'], label=f'Power Avg - {size} MB', marker='x')

# Dodanie etykiet, tytułów i legendy
plt.xlabel('Time (s)')
plt.ylabel('Usage (%) / Power (W)')
plt.title('CPU, GPU Usage and Power Average Grouped by File Size')
plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1))  # Przenosimy legendę na prawo
plt.grid(True)
plt.tight_layout()  # Automatyczne dostosowanie układu wykresu

# Wyświetlenie wykresu
plt.show()