from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/catcaller/', methods=['GET'])
def run_script():
    input_path = request.args.get('input_path', "/jetson-basecalling/test_sample/small/")
    signal_window_length = request.args.get('signal_window_length', 128)
    batch_size = request.args.get('batch_size', 128)
    
    try:
        command = ['bash', 'run_basecalling.sh', input_path, str(signal_window_length), str(batch_size)]
        subprocess.run(command, check=True)
        
        db_command = [
            'python3', '/jetson-basecalling/metrics/db/call_db.py',
            'CATCALLER_STATS',
            '/jetson-basecalling/CATCaller/execution_statistic.csv',
            '/jetson-basecalling/CATCaller/jetson_metrics.csv'
        ]
        subprocess.run(db_command, check=True)
        
        return f'Running script with input: {input_path}, batch size: {batch_size}'
    except subprocess.CalledProcessError as e:
        return f'Error: {e}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002)