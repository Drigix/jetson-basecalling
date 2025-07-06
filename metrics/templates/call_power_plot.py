import matplotlib.pyplot as plt
import numpy as np
import os

plt.style.use('_mpl-gallery')

base_path = '../../power_data'
devices = ['Chiron', 'RODAN', 'SACall']
batch_sizes = [16, 32, 64, 128, 140]

results = {device: [] for device in devices}

for device in devices:
    for batch in batch_sizes:
        file_path = os.path.join(base_path, device, f'{batch}.txt')
        
        with open(file_path, 'r') as f:
            data_points = []
            for line in f:
                line = line.strip()
                if line:
                    try:
                        value = float(line)
                        data_points.append(value)
                    except ValueError:
                        continue
        
        if data_points:
            avg = sum(data_points) / len(data_points)
            results[device].append(avg)

fig, ax = plt.subplots(figsize=(10, 6))

styles = ['o-', 's-', '^-']

for i, device in enumerate(devices):
    ax.plot(
        batch_sizes,
        results[device],
        styles[i],
        linewidth=2,
        markersize=8,
        label=device
    )

ax.set(
    xlim=(0, 150),
    xticks=batch_sizes,
    xlabel='Batch Size',
    ylabel='Average Power Consumption (W)',
    title='Power Consumption by Batch Size'
)
ax.legend()

ax.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()