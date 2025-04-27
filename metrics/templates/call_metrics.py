import matplotlib.pyplot as plt
import os
import argparse
import json

parser = argparse.ArgumentParser(description="Insert data into Cosmos DB")
parser.add_argument("--data", type=str,
                    required=True, help="Data to plot")
parser.add_argument("--plot_name", type=str,
                    required=True, help="Plot name")

args = parser.parse_args()
data = json.loads(args.data)
time_data = []
cpu_data = []
ram_data = []

for metric in data:
    time_data.append(metric['time'])
    cpu_data.append(metric['cpu'])
    ram_data.append(metric['ram'])
        
# Generate bar plot for CPU and RAM usage over time
x = time_data
    
plt.figure(figsize=(10, 5))
    
plt.subplot(2, 1, 1)
plt.bar(x, cpu_data, color='blue')
plt.xlabel('Time')
plt.ylabel('CPU Usage')
plt.title('CPU Usage Over Time')
    
plt.subplot(2, 1, 2)
plt.bar(x, ram_data, color='green')
plt.xlabel('Time')
plt.ylabel('RAM Usage')
plt.title('RAM Usage Over Time')

plt.subplots_adjust(hspace=0.5)

# Ensure the directory exists
output_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(output_dir, exist_ok=True)

# Save the plot as a JPEG image
plt.savefig(os.path.join(output_dir, args.plot_name), format='jpg')
