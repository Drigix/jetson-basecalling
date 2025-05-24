from flask import Flask, request, render_template
import subprocess
import json
import matplotlib.pyplot as plt

app = Flask(__name__, template_folder='../metrics/templates',
            static_url_path='/rodan/static',
            static_folder='../metrics/templates/static')

@app.route('/rodan/', methods=['GET'])
def run_script():
    global current_time, best_time_sacall, best_time_rodan, best_time_chiron
    basecaller_name = "RODAN"
    input_path = request.args.get('input_path', "/jetson-basecalling/test_sample/small/")
    batch_size = request.args.get('batch_size', 128)
    mode = request.args.get('mode', 0)
    
    try:
        command = ['bash', 'run_basecalling.sh', input_path, str(batch_size), str(mode)]
        subprocess.run(command, check=True)
        
        db_command = [
            'python3', '/jetson-basecalling/metrics/db/call_db.py',
            '--query_type', 'INSERT',
            '--container_name', 'RODAN_STATS',
            '--execution_stat_file', '/jetson-basecalling/RODAN/execution_statistic.csv',
            '--jetson_metrics_file', '/jetson-basecalling/RODAN/jetson_metrics.csv'
        ]
        subprocess.run(db_command, check=True)
        
        # return f'Running script with input: {input_path}, batch size: {batch_size}'
        generate_plot(batch_size)
        
        return render_template('statistic.html',
                               current_basecalling_metrics_plot='current_basecalling_metrics_plot', 
                               basecaller_name=basecaller_name, 
                               batch_size=batch_size,
                               execution_time=current_time,
                               best_time_sacall=best_time_sacall,
                               best_time_rodan=best_time_rodan,
                               best_time_chiron=best_time_chiron)
    except subprocess.CalledProcessError as e:
        return f'Error: {e}', 500

def generate_plot(batch_size):
        global file_size, current_time, best_time_sacall, best_time_rodan, best_time_chiron
        # First generete metrics for current basecalling
        db_find_command = [
            'python3', '../metrics/db/call_db.py',
            '--query_type', 'FIND_CURRENT_EXECUTION_TIME',
            '--execution_stat_file', '/jetson-basecalling/RODAN/execution_statistic.csv'
        ]
        current_time = subprocess.check_output(db_find_command, universal_newlines=True)
        
        current_basecalling_metrics_data = []
        db_find_command = [
            'python3', '../metrics/db/call_db.py',
            '--query_type', 'FIND_CURRENT_METRICS',
            '--jetson_metrics_file', '/jetson-basecalling/RODAN/jetson_metrics.csv'
        ]
        result_metrics = subprocess.check_output(db_find_command, universal_newlines=True)
        parsed_json = json.loads(result_metrics)
        current_basecalling_metrics_data.extend(parsed_json)
        
        generate_plot_command = [
            'python3', '../metrics/templates/call_metrics.py',
            '--data', json.dumps(current_basecalling_metrics_data),
            '--plot_name', 'current_basecalling_metrics_plot.jpg'
        ]
        subprocess.check_output(generate_plot_command, universal_newlines=True)
        
        # Second generete execution for other basecalling
        data = []
        db_find_command = [
            'python3', '../metrics/db/call_db.py',
            '--query_type', 'FIND',
            '--container_name', 'SACALL_STATS',
            '--execution_stat_file', '/jetson-basecalling/RODAN/execution_statistic.csv',
            '--batch_size', str(batch_size)
        ]
        result = subprocess.check_output(db_find_command, universal_newlines=True)
    
        # Assuming the script returns JSON output
        parsed_json = json.loads(result)
        
        if parsed_json:
            data.append(parsed_json['execution_time'])
            file_size = parsed_json['file_size']
            best_time_sacall = parsed_json['execution_time']
            best_sacall_metrics = parsed_json['metrics']
        else:
            file_size = 0
            best_time_sacall = 0
            best_sacall_metrics = {}
            
        db_find_command = [
            'python3', '../metrics/db/call_db.py',
            '--query_type', 'FIND',
            '--container_name', 'RODAN_STATS',
            '--execution_stat_file', '/jetson-basecalling/RODAN/execution_statistic.csv',
            '--batch_size', str(batch_size)
        ]
        result = subprocess.check_output(db_find_command, universal_newlines=True)
    
        # Assuming the script returns JSON output
        parsed_json = json.loads(result)
        if parsed_json:
            data.append(parsed_json['execution_time'])
            file_size = parsed_json['file_size']
            best_time_rodan = parsed_json['execution_time']
            best_rodan_metrics = parsed_json['metrics']
        else:
            file_size = 0
            best_time_rodan = 0
            best_rodan_metrics = {}
            
        db_find_command = [
            'python3', '../metrics/db/call_db.py',
            '--query_type', 'FIND',
            '--container_name', 'CHIRON_STATS',
            '--execution_stat_file', '/jetson-basecalling/RODAN/execution_statistic.csv',
            '--batch_size', str(batch_size)
        ]
        result = subprocess.check_output(db_find_command, universal_newlines=True)
        
    
        # Assuming the script returns JSON output
        parsed_json = json.loads(result)
        if parsed_json:
            data.append(parsed_json['execution_time'])
            file_size = parsed_json['file_size']
            best_time_chiron = parsed_json['execution_time']
            best_chiron_metrics = parsed_json['metrics']
        else:
            file_size = 0
            best_time_chiron = 0
            best_chiron_metrics = {}
            
        basecallers = ['SACall', 'RODAN', 'Chiron']
        
        generate_plot_command = [
            'python3', '../metrics/templates/call_statistic.py',
            '--basecallers', json.dumps(basecallers),
            '--data', json.dumps(data),
            '--batch_size', str(batch_size),
            '--file_size', str(file_size)
        ]
        result = subprocess.check_output(generate_plot_command, universal_newlines=True)
        
        generate_plot_command = [
            'python3', '../metrics/templates/call_avg_metrics.py',
            '--basecallers', json.dumps(basecallers),
            '--data_sacall', json.dumps(best_sacall_metrics),
            '--data_rodan', json.dumps(best_rodan_metrics),
            '--data_chiron', json.dumps(best_chiron_metrics),
            '--batch_size', str(batch_size),
            '--file_size', str(file_size),
            '--plot_name', 'avg_metrics_plot.jpg'
        ]
        result = subprocess.check_output(generate_plot_command, universal_newlines=True)


def generate_metrics_plot(parsed_json):
    time_data = []
    cpu_data = []
    ram_data = []
    
    for metric in parsed_json['metrics']:
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
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6004)