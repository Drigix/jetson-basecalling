import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
import json

plt.style.use('seaborn-v0_8-darkgrid')

parser = argparse.ArgumentParser()
parser.add_argument("--basecallers", type=str, required=True)
parser.add_argument("--data_sacall", type=str, required=True)
parser.add_argument("--data_rodan", type=str, required=True)
parser.add_argument("--data_chiron", type=str, required=True)
parser.add_argument("--file_size", type=str, required=True)
parser.add_argument("--batch_size", type=str, required=True)
parser.add_argument("--plot_name", type=str, required=True)
args = parser.parse_args()

# Load data
parsed_basecallers = json.loads(args.basecallers)
sacall = json.loads(args.data_sacall)
rodan = json.loads(args.data_rodan)
chiron = json.loads(args.data_chiron)

# Extract and align data to shortest list
def extract(data):
    return [item for item in data if 'ram' in item and 'cpu' in item]

sacall_data = extract(sacall)
rodan_data = extract(rodan)
chiron_data = extract(chiron)

min_len = min(len(sacall_data), len(rodan_data), len(chiron_data))

def trim_and_extract(metric):
    return (
        [item[metric] for item in sacall_data[:min_len]],
        [item[metric] for item in rodan_data[:min_len]],
        [item[metric] for item in chiron_data[:min_len]]
    )

ram_sacall, ram_rodan, ram_chiron = trim_and_extract('ram')
cpu_sacall, cpu_rodan, cpu_chiron = trim_and_extract('cpu')

# Convert RAM from MB to GB
ram_sacall = np.array(ram_sacall) / 1024
ram_rodan = np.array(ram_rodan) / 1024
ram_chiron = np.array(ram_chiron) / 1024

# Create time axis assuming ~5s intervals
x = np.arange(0, min_len * 5, 5)

# Plot RAM usage
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
ax.plot(x, ram_sacall, label='SACall')
ax.plot(x, ram_rodan, label='RODAN')
ax.plot(x, ram_chiron, label='Chiron')
ax.set_title('Basecalling RAM Usage with file size: {} and batch size: {}'.format(args.file_size, args.batch_size))
ax.set_xlabel('Time (s)')
ax.set_ylabel('RAM (GB)')
ax.set_ylim(0, 4)
ax.legend()
plt.tight_layout()

output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)
plt.savefig(os.path.join(output_dir, f"{args.plot_name}_ram.jpg"))
plt.close()

# Plot CPU usage
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
ax.plot(x, cpu_sacall, label='SACall')
ax.plot(x, cpu_rodan, label='RODAN')
ax.plot(x, cpu_chiron, label='Chiron')
ax.set_title('Basecalling CPU Usage with file size: {} and batch size: {}'.format(args.file_size, args.batch_size))
ax.set_xlabel('Time (s)')
ax.set_ylabel('CPU (%)')
ax.set_ylim(0, 100)
ax.legend()
plt.tight_layout()

plt.savefig(os.path.join(output_dir, f"{args.plot_name}_cpu.jpg"))
plt.close()