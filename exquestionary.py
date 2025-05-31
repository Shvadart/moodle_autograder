from questionary import select, text, confirm

def main():
    action = select(
        "Что вы хотите сделать?",
        choices=[
            "Проверить ответы",
            "Добавить эталонный ответ",
            "Настроить интервал",
            "Выход"
        ]).ask()

    if action == "Проверить ответы":
        print("Запуск проверки...")
    
    elif action == "Добавить эталонный ответ":
        question_id = text("Введите ID вопроса:").ask()
        answer = text("Введите эталонный ответ:").ask()
        print(f"Ответ для вопроса {question_id} сохранён!")

    elif action == "Настроить интервал":
        interval = text("Интервал (секунды):", validate=lambda x: x.isdigit()).ask()
        print(f"Установлен интервал {interval} сек.")

    elif action == "Выход" or not confirm("Продолжить?").ask():
        print("Завершение работы.")
        return

    main()  # Рекурсивный вызов для возврата в меню

if __name__ == "__main__":
    print("=== Moodle Evaluator (Консольная версия) ===")
    main()