from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/sacall/', defaults={'input_path': None, 'batch_size': None}, methods=['GET'])
@app.route('/sacall/<path:input_path>/<int:batch_size>', methods=['GET'])
def run_script(input_path, batch_size):
    try:
        if input_path is None or batch_size is None:
            # Scripts with default parameters
            command = ['bash', 'run_basecalling.sh', "/jetson-basecalling/test_sample/small/", str(128)]
            msg = 'Running default script'
        else:
            # Scripts with pass parameters
            command = ['bash', 'run_basecalling.sh', input_path, str(batch_size)]
            msg = f'Running script with input: {input_path}, batch size: {batch_size}'
        
        subprocess.run(command, check=True)
        return msg
    except subprocess.CalledProcessError as e:
        return f'Error: {e}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001)