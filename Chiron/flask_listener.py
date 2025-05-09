from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/chiron/', methods=['GET'])
def run_script():
    input_path = request.args.get('input_path', "/jetson-basecalling/test_sample/small/")
    batch_size = request.args.get('batch_size', 128)
    
    try:
        command = ['bash', 'run_basecalling.sh', input_path, str(batch_size)]
        subprocess.run(command, check=True)
        
        db_command = [
            'python3', '/jetson-basecalling/metrics/db/call_db.py',
            '--query_type', 'INSERT',
            '--container_name', 'CHIRON_STATS',
            '--execution_stat_file', '/jetson-basecalling/Chiron/execution_statistic.csv',
            '--jetson_metrics_file', '/jetson-basecalling/Chiron/jetson_metrics.csv'
        ]
        
        return f'Running script with input: {input_path}, batch size: {batch_size}'
    except subprocess.CalledProcessError as e:
        return f'Error: {e}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6003)