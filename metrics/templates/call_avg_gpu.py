import numpy as np
import os
import csv

base_path = '../../gpu_data'
devices = ['Chiron', 'RODAN', 'SACall']
batch_sizes = [16, 32, 64, 128, 140]

results = {device: [] for device in devices}

for device in devices:
    for batch in batch_sizes:
        file_path = os.path.join(base_path, device, f'0.64_{batch}.txt')
        
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
            

output_dir = os.path.join(os.path.dirname(__file__), 'static', 'data')
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, 'gpu_usage_results.csv')

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['model', 'batch_size', 'gpu_usage_avg'])
    
    for device_idx, device in enumerate(devices):
        for batch_idx, batch in enumerate(batch_sizes):
            if batch_idx < len(results[device]):
                writer.writerow([device, batch, results[device][batch_idx]])