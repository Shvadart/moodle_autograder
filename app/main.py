import time
from moodle_db import get_pending_answers, save_evaluation, get_question_info
from evaluator import evaluate_answer

def check_answers_once():
    """Одна итерация проверки ответов (для использования в веб-интерфейсе)"""
    answers = get_pending_answers()
    
    if answers:
        print(f"Найдено {len(answers)} новых ответов. Начинаю проверку.")
        
        for attemptid, questionid, answer in answers:
            question, correct_answer = get_question_info(questionid)

            if not question:
                print(f"Не удалось получить текст вопроса для Q{questionid}")
                continue

            if not correct_answer:
                print(f"Q{questionid}: Эталонный ответ отсутствует, проверка будет произведена без него.")

            score, feedback = evaluate_answer(answer, question, correct_answer)
            print(f"Attempt {attemptid}, Q{questionid}: {score} — {feedback}")
            save_evaluation(attemptid, score, feedback)
    else:
        print("Новых ответов нет.")

def main():
    """Основная функция для автономного режима"""
    print("Ожидание новых ответов студентов...")
    while True:
        check_answers_once()
        time.sleep(30)

if __name__ == "__main__":
    main()