import questionary
from moodle_db import get_questions_without_answers, update_grader_info
from main import check_answers_once
import time
import threading

# Глобальные переменные для управления проверкой
check_thread = None
stop_event = threading.Event()
current_interval = 30
is_checking = False

def change_interval(current_interval):
    """Изменение интервала проверки"""
    new_interval = questionary.text(
        f"Текущий интервал: {current_interval} сек. Введите новый интервал (секунды):",
        validate=lambda x: x.isdigit() and int(x) > 0
    ).ask()
    return int(new_interval)

def check_and_add_grader_answers():
    """Проверка наличия эталонных ответов и их добавление при необходимости"""
    questions = get_questions_without_answers()
    if not questions:
        print("🎉 Все вопросы уже имеют эталонные ответы!")
        return

    print(f"⚠️ Найдено {len(questions)} вопросов без эталонных ответов.")
    
    for q in questions:
        print(f"\nВопрос ID {q['id']}: {q['name']}")
        print(f"Текст вопроса: {q['questiontext']}")
        
        if questionary.confirm("Добавить эталонный ответ для этого вопроса?").ask():
            grader_info = questionary.text("Введите эталонный ответ:").ask()
            if grader_info.strip():
                success = update_grader_info(q['id'], grader_info)
                print("✅ Ответ сохранен!" if success else "❌ Ошибка сохранения!")
            else:
                print("❌ Текст ответа не может быть пустым!")

def run_auto_check(interval):
    """Запуск авто-проверки с заданным интервалом"""
    global is_checking
    try:
        is_checking = True
        while not stop_event.is_set():
            print(f"\n🔍 Проверка ответов... (интервал: {interval} сек)")
            check_answers_once()
            
            # Ожидаем указанный интервал или прерывание
            for _ in range(interval):
                if stop_event.is_set():
                    break
                time.sleep(1)
    except Exception as e:
        print(f"Ошибка при проверке: {e}")
    finally:
        is_checking = False

def start_background_check():
    """Запуск проверки в фоновом режиме"""
    global check_thread, stop_event, is_checking
    stop_event.clear()
    check_thread = threading.Thread(
        target=run_auto_check, 
        args=(current_interval,),
        daemon=True
    )
    check_thread.start()

def stop_background_check():
    """Остановка фоновой проверки"""
    global stop_event, is_checking
    stop_event.set()
    is_checking = False
    print("🛑 Проверка остановлена")

def main_menu():
    global current_interval, is_checking
    
    while True:
        choices = [
            "1. Запустить проверку" if not is_checking else "1. Остановить проверку",
            f"2. Изменить интервал проверки (текущий: {current_interval} сек)",
            "3. Проверить наличие эталонных ответов",
            "4. Выход"
        ]

        choice = questionary.select(
            "=== Moodle Evaluator CLI ===",
            choices=choices
        ).ask()

        if choice.startswith("1."):
            if "Запустить" in choice:
                start_background_check()
                print(f"🔍 Проверка запущена с интервалом {current_interval} сек")
            else:
                stop_background_check()

        elif choice.startswith("2."):
            current_interval = change_interval(current_interval)

        elif choice.startswith("3."):
            check_and_add_grader_answers()

        elif choice.startswith("4."):
            if is_checking:
                stop_background_check()
            break

if __name__ == "__main__":
    main_menu()