from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/catcaller', methods=['GET'])
def run_script():
    try:
        subprocess.run(['bash', 'run_basecalling.sh'])
        return 'Run script'
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002)