import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import os
import random

parser = argparse.ArgumentParser(description="Statistics data to plot")
parser.add_argument("--basecallers", type=str,
                    required=True, help="Basecaller names")
parser.add_argument("--data", type=str,
                    required=True, help="Data to plot")
parser.add_argument("--data_low_mode", type=str,
                    required=True, help="Data low mode to plot")
parser.add_argument("--batch_size", type=str,
                    required=True, help="Batch size")
parser.add_argument("--file_size", type=str,
                    required=True, help="File size")

args = parser.parse_args()

basecallers = json.loads(args.basecallers)
data = json.loads(args.data)
data_low_mode = json.loads(args.data_low_mode)

x = np.arange(len(basecallers))
width = 0.35

colors = ['#FF5733', '#33FF57']

plt.figure(figsize=(10, 5))
plt.title(f'Basecalling with batch size {args.batch_size} and file size {args.file_size}MB')

plt.bar(x - width/2, data, width, label='Normal mode', color=colors[0])
plt.bar(x + width/2, data_low_mode, width, label='Low mode', color=colors[1])

plt.xlabel('Basecallers')
plt.ylabel('Execution Time [s]')
plt.xticks(x, basecallers)
plt.legend()

# Ensure the directory exists   
output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)

# Save the plot as a JPEG image
plt.savefig(os.path.join(output_dir, 'best_statistic_plot.jpg'), format='jpg')
