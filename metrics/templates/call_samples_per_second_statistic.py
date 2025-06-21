import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import os

parser = argparse.ArgumentParser(description="Statistics data to plot")
parser.add_argument("--basecallers", type=str, required=True, help="Basecaller names (JSON list)")
parser.add_argument("--file_size", type=float, required=True, help="File size (integer)")
parser.add_argument("--data", type=str, required=True, help="Data to plot (JSON dictionary)")
parser.add_argument("--mode", type=str, required=True, help="Jetson mode (e.g., 'normal' or 'low_mode')")
parser.add_argument("--plot_name", type=str,
                    required=True, help="Plot name")
args = parser.parse_args()

try:
    basecallers = json.loads(args.basecallers)
    data = json.loads(args.data)
    file_size = args.file_size
    mode = args.mode
    plot_name = args.plot_name
except (json.JSONDecodeError, ValueError) as e:
    print(f"Error parsing input arguments: {e}")
    exit(1)

batch_sizes = [16, 32, 64, 128, 140]

try:
    samples_per_second = {
        bs: [0 if data[str(bs)][i] == 0 else file_size / (2 * data[str(bs)][i]) for i in range(len(basecallers))]
        for bs in batch_sizes
    }
except KeyError as e:
    print(f"Missing data for batch size or basecaller: {e}")
    exit(1)
except ZeroDivisionError:
    print("Execution time cannot be zero.")
    exit(1)

x = np.arange(len(basecallers))
width = 0.8 / len(batch_sizes) 

fig, ax = plt.subplots(figsize=(10, 6))

for i, bs in enumerate(batch_sizes):
    ax.bar(x + i * width - (len(batch_sizes) - 1) * width / 2, samples_per_second[bs], width, label=f'Batch Size {bs}')

ax.set_xlabel('Basecallers')
ax.set_ylabel('Samples per Second')
ax.set_title(f'Samples per Second ({mode} mode)')
ax.set_xticks(x + width)
ax.set_xticklabels(basecallers)
ax.legend()

# Ensure the directory exists
output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)

# Save the plot as a JPEG image
plt.savefig(os.path.join(output_dir, plot_name), format='jpg')