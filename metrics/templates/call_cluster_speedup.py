import matplotlib.pyplot as plt
import numpy as np
import os
import csv

plt.style.use('_mpl-gallery')

base_path = '../../cluster_scalability'
devices = ['Chiron', 'RODAN', 'SACall']

results = {device: {'nodes': [], 'speedup': []} for device in devices}

for device in devices:
    file_path = os.path.join(base_path, device, 'scalability_data.csv')

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results[device]['nodes'].append(int(row['nodes']))
            results[device]['speedup'].append(float(row['scalability_factor']))

# --- Plot: 1 row × 3 columns ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)

markers = ['o', 's', '^']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

max_nodes = max(max(results[d]['nodes']) for d in devices)
ideal_nodes = np.arange(1, max_nodes + 1)

for i, device in enumerate(devices):
    ax = axes[i]
    nodes = results[device]['nodes']
    speedup = results[device]['speedup']

    # Ideal speedup line
    ax.plot(ideal_nodes, ideal_nodes, 'k--', linewidth=1.5, alpha=0.5, label='Ideal speedup')

    # Model speedup
    ax.plot(nodes, speedup, marker=markers[i], color=colors[i],
            label=device, linewidth=2, markersize=8)

    ax.set_title(device, fontsize=14, fontweight='bold')
    ax.set_xlabel('Number of nodes', fontsize=12)
    ax.set_xticks(range(1, max_nodes + 1))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

# Wspólna etykieta Y tylko na pierwszym wykresie (sharey=True)
axes[0].set_ylabel('Speedup', fontsize=13)

# fig.suptitle('Cluster Scalability — Speedup vs Number of Nodes', fontsize=15, y=1.02)
plt.tight_layout()
output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)
plt.savefig(os.path.join(output_dir, 'scalability_plot.png'), dpi=150, bbox_inches='tight', format='jpg')
plt.show()