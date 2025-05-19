from flask import Flask, render_template, request, jsonify
from threading import Thread
import threading
import time
from moodle_db import get_questions_without_answers
import main as evaluator_main

app = Flask(__name__)

# Глобальные настройки
check_interval = 30  # секунд по умолчанию
active_thread = None
evaluator_running = False
stop_event = threading.Event()

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

@app.route('/stop_evaluator', methods=['POST'])
def stop_evaluator():
    global evaluator_running, stop_event
    if evaluator_running:
        stop_event.set()
        evaluator_running = False
        return jsonify({'status': 'success', 'message': 'Проверка остановлена'})
    return jsonify({'status': 'error', 'message': 'Проверка не запущена'})

@app.route('/refresh_questions', methods=['POST'])
def refresh_questions():
    try:
        questions = get_questions_without_answers()
        return jsonify({
            'status': 'success',
            'count': len(questions),  # Важно: передаем реальное количество
            'html': render_template('_questions_table.html', 
                                  questions_without_answers=questions)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка обновления: {str(e)}',
            'count': 0
        })

def run_evaluator():
    global evaluator_running, stop_event
    evaluator_running = True
    stop_event.clear()
    
    while evaluator_running and not stop_event.is_set():
        evaluator_main.check_answers_once()
        for _ in range(check_interval):
            if stop_event.is_set():
                break
            time.sleep(1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)