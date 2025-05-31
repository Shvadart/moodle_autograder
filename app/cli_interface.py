import questionary
from moodle_db import get_questions_without_answers, update_grader_info
from main import check_answers_once
import time

def main_menu():
    current_interval = 30  # Значение по умолчанию
    
    while True:
        choice = questionary.select(
            "=== Moodle Evaluator CLI ===",
            choices=[
                f"1. Запустить авто-проверку (интервал: {current_interval} сек)",
                "2. Изменить интервал проверки",
                "3. Проверить наличие эталонных ответов",
                "4. Выход"
            ]
        ).ask()

        if choice.startswith("1. Запустить авто-проверку"):
            run_auto_check(current_interval)

        elif choice == "2. Изменить интервал проверки":
            current_interval = change_interval(current_interval)

        elif choice == "3. Проверить наличие эталонных ответов":
            check_and_add_grader_answers()

        elif choice == "4. Выход":
            break

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
    try:
        print(f"🔍 Авто-проверка запущена (интервал: {interval} сек). Нажмите Ctrl+C для остановки.")
        while True:
            check_answers_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("🛑 Проверка остановлена.")

if __name__ == "__main__":
    main_menu()