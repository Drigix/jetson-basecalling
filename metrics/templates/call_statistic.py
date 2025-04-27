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
parser.add_argument("--batch_size", type=str,
                    required=True, help="Batch size")
parser.add_argument("--file_size", type=str,
                    required=True, help="File size")

args = parser.parse_args()

basecallers = json.loads(args.basecallers)
data = json.loads(args.data)

x = np.array(basecallers)
y = np.array(data)

colors = ['#FF5733', '#33FF57', '#3357FF']

plt.figure(figsize=(10, 5))
plt.title('Basecalling with batch size ' + args.batch_size + ' and file size ' + args.file_size + 'MB')
plt.bar(x, y, color=colors)

plt.xlabel('Basecallers')
plt.ylabel('Execution Time [s]')

# Ensure the directory exists   
output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)

# Save the plot as a JPEG image
plt.savefig(os.path.join(output_dir, 'best_statistic_plot.jpg'), format='jpg')
