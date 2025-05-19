from flask import Flask, render_template, request, jsonify
from threading import Thread
import time
from moodle_db import get_questions_without_answers
import main as evaluator_main

app = Flask(__name__)

# Глобальные настройки
check_interval = 30  # секунд по умолчанию
active_thread = None

@app.route('/')
def index():
    questions_without_answers = get_questions_without_answers()
    return render_template('index.html', 
                         interval=check_interval,
                         questions_without_answers=questions_without_answers)

@app.route('/update_interval', methods=['POST'])
def update_interval():
    global check_interval
    new_interval = int(request.form.get('interval', 30))
    if new_interval > 0:
        check_interval = new_interval
        return jsonify({'status': 'success', 'new_interval': check_interval})
    return jsonify({'status': 'error', 'message': 'Invalid interval'})

@app.route('/start_evaluator', methods=['POST'])
def start_evaluator():
    global active_thread
    if active_thread is None or not active_thread.is_alive():
        active_thread = Thread(target=run_evaluator)
        active_thread.daemon = True
        active_thread.start()
        return jsonify({'status': 'success', 'message': 'Evaluator started'})
    return jsonify({'status': 'error', 'message': 'Evaluator already running'})

def run_evaluator():
    while True:
        evaluator_main.check_answers_once()
        time.sleep(check_interval)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)