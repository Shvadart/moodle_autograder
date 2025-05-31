import time
from moodle_db import get_pending_answers, save_evaluation, get_question_info
from evaluator import evaluate_answer

def check_answers_once(silent=False):
    """Одна итерация проверки ответов (для использования в веб-интерфейсе)
    
    Args:
        silent (bool): Если True, не выводит логи в консоль
    """
    answers = get_pending_answers()
    
    if answers:
        if not silent:
            print(f"Найдено {len(answers)} новых ответов. Начинаю проверку.")
        
        for attemptid, questionid, answer in answers:
            question, correct_answer = get_question_info(questionid)

            if not question:
                if not silent:
                    print(f"Не удалось получить текст вопроса для Q{questionid}")
                continue

            if not correct_answer and not silent:
                print(f"Q{questionid}: Эталонный ответ отсутствует, проверка будет произведена без него.")

            score, feedback = evaluate_answer(answer, question, correct_answer)
            if not silent:
                print(f"Attempt {attemptid}, Q{questionid}: {score} — {feedback}")
            save_evaluation(attemptid, score, feedback)
    elif not silent:
        print("Новых ответов нет.")

def main():
    """Основная функция для автономного режима"""
    print("Ожидание новых ответов студентов...")
    while True:
        check_answers_once()
        time.sleep(30)

if __name__ == "__main__":
    main()