import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
import json

parser = argparse.ArgumentParser(description="Insert data into Cosmos DB")
parser.add_argument("--basecallers", type=str,
                    required=True, help="Basecaller names")
parser.add_argument("--data_sacall", type=str,
                    required=True, help="SACall data to plot")
parser.add_argument("--data_rodan", type=str,
                    required=True, help="RODAN data to plot")
parser.add_argument("--data_chiron", type=str,
                    required=True, help="Chiron data to plot")
parser.add_argument("--batch_size", type=str,
                    required=True, help="Batch size")
parser.add_argument("--file_size", type=str,
                    required=True, help="File size")
parser.add_argument("--plot_name", type=str,
                    required=True, help="Plot name")
args = parser.parse_args()

# Data
ram_bars = []
cpu_bars = []

parsed_basecallers = json.loads(args.basecallers)
parsed_data_sacall = json.loads(args.data_sacall)
parsed_data_rodan = json.loads(args.data_rodan)
parsed_data_chiron = json.loads(args.data_chiron)

# Validate and calculate averages for each dataset
for dataset in [parsed_data_sacall, parsed_data_rodan, parsed_data_chiron]:
    if not dataset:
        ram_bars.append(0)
        cpu_bars.append(0)
        continue
    if not all(isinstance(item, dict) and 'ram' in item and 'cpu' in item for item in dataset):
        ram_bars.append(0)
        cpu_bars.append(0)
        continue
    rams = [item['ram'] for item in dataset if 'ram' in item]
    if rams:
        avg_ram = sum(rams) / len(rams)
        ram_bars.append(avg_ram)
    else:
        ram_bars.append(0)
    cpus = [item['cpu'] for item in dataset if 'cpu' in item]
    if cpus:
        avg_cpu = sum(cpus) / len(cpus)
        cpu_bars.append(avg_cpu)
    else:
        cpu_bars.append(0)

# Bar positions
r = np.arange(len(ram_bars))

# Ensure the directory exists
output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)

# Create subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), dpi=300)

# Plot RAM usage
ax1.bar(r, ram_bars, color='blue', width=0.5, edgecolor='white', label='RAM')
ax1.set_title('Average RAM Usage', fontweight='bold')
ax1.set_xlabel('Basecallers', fontweight='bold')
ax1.set_ylabel('RAM (MB)', fontweight='bold')
ax1.set_xticks(r)
ax1.set_xticklabels(parsed_basecallers)

# Plot CPU usage
ax2.bar(r, cpu_bars, color='green', width=0.5, edgecolor='white', label='CPU')
ax2.set_title('Average CPU Usage', fontweight='bold')
ax2.set_xlabel('Basecallers', fontweight='bold')
ax2.set_ylabel('CPU (%)', fontweight='bold')
ax2.set_xticks(r)
ax2.set_xticklabels(parsed_basecallers)

# Adjust layout
plt.tight_layout()

# Save the plot as a JPEG image
plt.savefig(os.path.join(output_dir, args.plot_name), format='jpg')