# Импорт необходимых модулей
import time  # Для работы с временными задержками
from moodle_db import get_pending_answers, save_evaluation, get_question_info  # Функции работы с БД Moodle
from evaluator import evaluate_answer  # Функция оценки ответов

def main():
    """
    Основная функция программы - бесконечный цикл проверки новых ответов студентов.
    Проверяет наличие новых ответов в БД, оценивает их и сохраняет результаты.
    """
    print("Ожидание новых ответов студентов...")
    
    # Основной бесконечный цикл работы программы
    while True:
        # Получаем список непроверенных ответов из БД
        answers = get_pending_answers()
        
        if answers:
            print(f"Найдено {len(answers)} новых ответов. Начинаю проверку.")
            
            # Обрабатываем каждый ответ в цикле
            for attemptid, questionid, answer in answers:
                # Получаем информацию о вопросе (текст и эталонный ответ)
                question, correct_answer = get_question_info(questionid)

                # Проверяем, удалось ли получить текст вопроса
                if not question:
                    print(f"Не удалось получить текст вопроса для Q{questionid}")
                    continue  # Пропускаем этот ответ

                # Проверяем наличие эталонного ответа
                if not correct_answer:
                    print(f"Эталонный ответ для Q{questionid} не найден. Продолжаю без него.")
                    correct_answer = ""  # Устанавливаем пустую строку, если эталона нет

                # Дублирующая проверка (возможно избыточная, можно удалить)
                if not correct_answer:
                    print(f"Q{questionid}: Эталонный ответ отсутствует, проверка будет произведена без него.")

                # Выводим информацию о текущем вопросе для лога
                print(f"Q{questionid} - Вопрос: {question}")
                print(f"Q{questionid} - Эталон: {correct_answer}")

                # Оцениваем ответ студента
                score, feedback = evaluate_answer(answer, question, correct_answer)
                
                # Выводим и сохраняем результаты оценки
                print(f"Attempt {attemptid}, Q{questionid}: {score} — {feedback}")
                save_evaluation(attemptid, score, feedback)
        else:
            # Если новых ответов нет, выводим сообщение
            print("Новых ответов нет.")
        
        # Пауза перед следующей проверкой (30 секунд)
        time.sleep(30)

# Стандартная проверка для запуска main() при непосредственном выполнении скрипта
if __name__ == "__main__":
    main()