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
barWidth = 0.25
ram_bars = []
cpu_bars = []

parsed_basecallers = json.loads(args.basecallers)
parsed_data_sacall = json.loads(args.data_sacall)
parsed_data_rodan = json.loads(args.data_rodan)
parsed_data_chiron = json.loads(args.data_chiron)

# Validate and calculate averages for each dataset
for dataset in [parsed_data_sacall, parsed_data_rodan, parsed_data_chiron]:
    if not all(isinstance(item, dict) and 'ram' in item and 'cpu' in item for item in dataset):
        raise ValueError("Invalid data in dataset")
    rams = [item['ram'] for item in dataset]
    avg_ram = sum(rams) / len(rams) if rams else None
    ram_bars.append(avg_ram)
    cpus = [item['cpu'] for item in dataset]
    avg_cpu = sum(cpus) / len(cpus) if cpus else None
    cpu_bars.append(avg_cpu)

# Validate basecallers
# if len(args.basecallers) != len(ram_bars):
#     raise ValueError("Number of basecallers does not match the number of data groups", args.basecallers, ram_bars, cpu_bars)

# Bar positions
r = np.arange(len(ram_bars))
r2 = r + barWidth

# Plotting
fig, ax = plt.subplots(dpi=300)
ax.bar(r, ram_bars, color='#7f6d5f', width=barWidth, edgecolor='white', label='ram')
ax.bar(r2, cpu_bars, color='#557f2d', width=barWidth, edgecolor='white', label='cpu')

# Xticks
ax.set_xlabel('group', fontweight='bold')
ax.set_xticks(r + barWidth / 2)
ax.set_xticklabels(parsed_basecallers)

# Ensure the directory exists
output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)

# Save the plot as a JPEG image
plt.savefig(os.path.join(output_dir, args.plot_name), format='jpg')