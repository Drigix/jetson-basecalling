from flask import Flask, request, render_template
import subprocess
import json

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
        
        generate_plot(batch_size, mode)
        
        return render_template('statistic.html',
                               current_basecalling_metrics_plot='current_basecalling_metrics_plot', 
                               basecaller_name=basecaller_name, 
                               batch_size=batch_size,
                               jetson_mode=mode,
                               execution_time=current_time,
                               best_time_sacall=best_time_sacall,
                               best_time_rodan=best_time_rodan,
                               best_time_chiron=best_time_chiron)
    except subprocess.CalledProcessError as e:
        return f'Error: {e}', 500

def generate_plot(batch_size, mode):
        global file_size, current_time, best_time_sacall, best_time_rodan, best_time_chiron, best_sacall_metrics, best_rodan_metrics, best_chiron_metrics, best_low_mode_sacall_metrics, best_low_mode_rodan_metrics, best_low_mode_chiron_metrics
        
        basecallers = ['SACall', 'RODAN', 'Chiron']
        file_size = 0
        
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
        data_low_mode = []
        data_avg = []
        data_avg_low_mode = []
        
        result = find_data_in_db('SACALL_STATS', '/jetson-basecalling/RODAN/execution_statistic.csv', batch_size, 0)
    
        parsed_json = json.loads(result)
        process_parsed_json(parsed_json, data, "sacall", mode, 0) 
        process_avg_parsed_json(parsed_json, data_avg)
        
        result = find_data_in_db('SACALL_STATS', '/jetson-basecalling/RODAN/execution_statistic.csv', batch_size, 1)
        parsed_json = json.loads(result)
        process_parsed_json(parsed_json, data_low_mode, "sacall", mode, 1)
        process_avg_parsed_json(parsed_json, data_avg_low_mode)
        
        result = find_data_in_db('RODAN_STATS', '/jetson-basecalling/RODAN/execution_statistic.csv', batch_size, 0)
        parsed_json = json.loads(result)
        process_parsed_json(parsed_json, data, "rodan", mode, 0)
        process_avg_parsed_json(parsed_json, data_avg)
        
        result = find_data_in_db('RODAN_STATS', '/jetson-basecalling/RODAN/execution_statistic.csv', batch_size, 1)
        parsed_json = json.loads(result)
        process_parsed_json(parsed_json, data_low_mode, "rodan", mode, 1)
        process_avg_parsed_json(parsed_json, data_avg_low_mode)
        
        result = find_data_in_db('CHIRON_STATS', '/jetson-basecalling/RODAN/execution_statistic.csv', batch_size, 0)
        parsed_json = json.loads(result)
        process_parsed_json(parsed_json, data, "chiron", mode, 0)
        process_avg_parsed_json(parsed_json, data_avg)
        
        result = find_data_in_db('CHIRON_STATS', '/jetson-basecalling/RODAN/execution_statistic.csv', batch_size, 1)
        parsed_json = json.loads(result)
        process_parsed_json(parsed_json, data_low_mode, "chiron", mode, 1)
        process_avg_parsed_json(parsed_json, data_avg_low_mode)
        
        generate_plot_command = [
            'python3', '../metrics/templates/call_statistic.py',
            '--basecallers', json.dumps(basecallers),
            '--data', json.dumps(data),
            '--data_low_mode', json.dumps(data_low_mode),
            '--batch_size', str(batch_size),
            '--file_size', str(file_size)
        ]
        result = subprocess.check_output(generate_plot_command, universal_newlines=True)
        
        generete_avg_execution(basecallers, file_size, batch_size, data_avg, data_avg_low_mode)
        
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
        
        generate_plot_command = [
            'python3', '../metrics/templates/call_avg_metrics.py',
            '--basecallers', json.dumps(basecallers),
            '--data_sacall', json.dumps(best_low_mode_sacall_metrics),
            '--data_rodan', json.dumps(best_low_mode_rodan_metrics),
            '--data_chiron', json.dumps(best_low_mode_chiron_metrics),
            '--batch_size', str(batch_size),
            '--file_size', str(file_size),
            '--plot_name', 'avg_metrics_low_mode_plot.jpg'
        ]
        result = subprocess.check_output(generate_plot_command, universal_newlines=True)
        
        generate_samples_per_second_statistic(basecallers, file_size, data, data_low_mode, data_avg, data_avg_low_mode, batch_size)

def find_data_in_db(container_name, execution_stat_file, batch_size, mode):
    db_find_command = [
        'python3', '../metrics/db/call_db.py',
        '--query_type', 'FIND',
        '--container_name', container_name,
        '--execution_stat_file', execution_stat_file,
        '--batch_size', str(batch_size),
        '--jetson_mode', str(mode)
    ]
    result = subprocess.check_output(db_find_command, universal_newlines=True)
    return result

def process_parsed_json(parsed_json, data, table_key, current_mode, mode):
    global file_size, best_time_sacall, best_time_rodan, best_time_chiron, best_sacall_metrics, best_rodan_metrics, best_chiron_metrics, best_low_mode_sacall_metrics, best_low_mode_rodan_metrics, best_low_mode_chiron_metrics

    if parsed_json:
        data.append(parsed_json['execution_time'])
        file_size = parsed_json['file_size']
        best_time = parsed_json['execution_time']
        best_metrics = parsed_json['metrics']
    else:
        data.append(0)
        best_time = 0
        best_metrics = {}

    if table_key == "rodan":
        if int(current_mode) == mode:
            best_time_rodan = best_time
        if mode == 1:
            best_low_mode_rodan_metrics = best_metrics
        else:
            best_rodan_metrics = best_metrics
    elif table_key == "sacall":
        if int(current_mode) == mode:
            best_time_sacall = best_time
        if mode == 1:
            best_low_mode_sacall_metrics = best_metrics
        else:
            best_sacall_metrics = best_metrics
    elif table_key == "chiron":
        if int(current_mode) == mode:
            best_time_chiron = best_time
        if mode == 1:
            best_low_mode_chiron_metrics = best_metrics
        else:
            best_chiron_metrics = best_metrics

def process_avg_parsed_json(parsed_json, data):
    if parsed_json and 'avg_execution_time' in parsed_json:
        data.append(parsed_json['avg_execution_time'])
    else:
        data.append(0)
        
def generete_avg_execution(basecallers, file_size, batch_size, data_avg, data_avg_low_mode):
    generate_plot_command = [
            'python3', '../metrics/templates/call_avg_statistic.py',
            '--basecallers', json.dumps(basecallers),
            '--data', json.dumps(data_avg),
            '--data_low_mode', json.dumps(data_avg_low_mode),
            '--batch_size', str(batch_size),
            '--file_size', str(file_size)
    ]
    subprocess.check_output(generate_plot_command, universal_newlines=True)

def generate_samples_per_second_statistic(basecallers, file_size, current_data, current_data_low_mode, current_avg_data, current_avg_data_low_mode, batch_size):
    result = prepare_samples_per_second_data(current_data, current_data_low_mode, current_avg_data, current_avg_data_low_mode, batch_size)
    data = {
        "16": result["data_16"],
        "32": result["data_32"],
        "64": result["data_64"],
        "128": result["data_128"],
        "140": result["data_140"]
    }
    data_avg = {
        "16": result["data_16_avg"],
        "32": result["data_32_avg"],
        "64": result["data_64_avg"],
        "128": result["data_128_avg"],
        "140": result["data_140_avg"]
    }
    data_low_mode = {
        "16": result["data_16_low_mode"],
        "32": result["data_32_low_mode"],
        "64": result["data_64_low_mode"],
        "128": result["data_128_low_mode"],
        "140": result["data_140_low_mode"]
    }
    data_avg_low_mode = {
        "16": result["data_16_low_mode_avg"],
        "32": result["data_32_low_mode_avg"],
        "64": result["data_64_low_mode_avg"],
        "128": result["data_128_low_mode_avg"],
        "140": result["data_140_low_mode_avg"]
    }
    
    file_size_in_bytes = file_size * 1024 * 1024
    
    generate_plot_command = [
            'python3', '../metrics/templates/call_samples_per_second_statistic.py',
            '--basecallers', json.dumps(basecallers),
            '--data', json.dumps(data),
            '--file_size', str(file_size_in_bytes),
            '--mode', str(0),
            '--plot_name', 'samples_per_second_plot.jpg'
    ]
    subprocess.check_output(generate_plot_command, universal_newlines=True)
    
    generate_plot_command = [
            'python3', '../metrics/templates/call_samples_per_second_statistic.py',
            '--basecallers', json.dumps(basecallers),
            '--data', json.dumps(data_avg),
            '--file_size', str(file_size_in_bytes),
            '--mode', str(0),
            '--plot_name', 'avg_samples_per_second_plot.jpg'
    ]
    subprocess.check_output(generate_plot_command, universal_newlines=True)
    
    generate_plot_command = [
            'python3', '../metrics/templates/call_samples_per_second_statistic.py',
            '--basecallers', json.dumps(basecallers),
            '--data', json.dumps(data_low_mode),
            '--file_size', str(file_size_in_bytes),
            '--mode', str(1),
            '--plot_name', 'samples_per_second_low_mode_plot.jpg'
    ]
    subprocess.check_output(generate_plot_command, universal_newlines=True)
    
    generate_plot_command = [
            'python3', '../metrics/templates/call_samples_per_second_statistic.py',
            '--basecallers', json.dumps(basecallers),
            '--data', json.dumps(data_avg_low_mode),
            '--file_size', str(file_size_in_bytes),
            '--mode', str(1),
            '--plot_name', 'avg_samples_per_second_low_mode_plot.jpg'
    ]
    subprocess.check_output(generate_plot_command, universal_newlines=True)
    
def prepare_samples_per_second_data(current_data, current_data_low_mode, current_avg_data, current_avg_data_low_mode, batch_size):
    data = {
        16: {"normal": [], "normal_avg": [], "low_mode": [], "low_mode_avg": []},
        32: {"normal": [], "normal_avg": [], "low_mode": [], "low_mode_avg": []},
        64: {"normal": [], "normal_avg": [], "low_mode": [], "low_mode_avg": []},
        128: {"normal": [], "normal_avg": [], "low_mode": [], "low_mode_avg": []},
        140: {"normal": [], "normal_avg": [], "low_mode": [], "low_mode_avg": []}
    }
    
    data[int(batch_size)]["normal"] = current_data
    data[int(batch_size)]["low_mode"] = current_data_low_mode
    data[int(batch_size)]["normal_avg"] = current_avg_data
    data[int(batch_size)]["low_mode_avg"] = current_avg_data_low_mode
    
    for bs in [16, 32, 64, 128, 140]:
        if bs == int(batch_size):
            continue
        
        for mode in [0, 1]:
            for table_key in ["SACALL_STATS", "RODAN_STATS", "CHIRON_STATS"]:
                result = find_data_in_db(table_key, '/jetson-basecalling/RODAN/execution_statistic.csv', bs, mode)
                parsed_json = json.loads(result)
                key = "normal" if mode == 0 else "low_mode"
                key_avg = "normal_avg" if mode == 0 else "low_mode_avg"
                if not parsed_json or 'execution_time' not in parsed_json:
                    execution_time = 0
                else:
                    execution_time = parsed_json.get('execution_time', 0)
                if not parsed_json or 'avg_execution_time' not in parsed_json:
                    avg_execution_time = 0
                else:
                    avg_execution_time = parsed_json.get('avg_execution_time', 0)
                data[bs][key].append(execution_time)
                data[bs][key_avg].append(avg_execution_time)
    
    return {
        "data_16": data[16]["normal"],
        "data_16_avg": data[16]["normal_avg"],
        "data_16_low_mode": data[16]["low_mode"],
        "data_16_low_mode_avg": data[16]["low_mode_avg"],
        "data_32": data[32]["normal"],
        "data_32_avg": data[32]["normal_avg"],
        "data_32_low_mode": data[32]["low_mode"],
        "data_32_low_mode_avg": data[32]["low_mode_avg"],
        "data_64": data[64]["normal"],
        "data_64_avg": data[64]["normal_avg"],
        "data_64_low_mode": data[64]["low_mode"],
        "data_64_low_mode_avg": data[64]["low_mode_avg"],
        "data_128": data[128]["normal"],
        "data_128_avg": data[128]["normal_avg"],
        "data_128_low_mode": data[128]["low_mode"],
        "data_128_low_mode_avg": data[128]["low_mode_avg"],
        "data_140": data[140]["normal"],
        "data_140_avg": data[140]["normal_avg"],
        "data_140_low_mode": data[140]["low_mode"],
        "data_140_low_mode_avg": data[140]["low_mode_avg"]
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6004)