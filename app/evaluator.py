import os
from openai import OpenAI
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from dotenv import load_dotenv
import nltk

load_dotenv()

lemmatizer = WordNetLemmatizer()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def lemmatize_text(text):
    tokens = word_tokenize(text)
    return [lemmatizer.lemmatize(token.lower()) for token in tokens]

def evaluate_answer(answer_text, question, correct_answer):
    if not correct_answer or correct_answer.strip() == "":
        prompt = (
            f"Вопрос: {question}\n"
            f"Ответ студента: {answer_text}\n"
            "Оцени ответ студента по 10-бальной шкале. Ответь одним числом."
        )
    else:
        prompt = (
            f"Вопрос: {question}\n"
            f"Правильный ответ: {correct_answer}\n"
            f"Ответ студента: {answer_text}\n"
            "Оцени ответ студента по 10-бальной шкале. Ответь одним числом."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты — ассистент преподавателя, проверяющий ответы студентов."},
                {"role": "user", "content": prompt}
            ]
        )

        gpt_score_str = response.choices[0].message.content.strip()
        gpt_score = float(gpt_score_str)

        if gpt_score > 8:
            feedback = "Отличный ответ!"
        elif gpt_score > 5:
            feedback = "Неплохо, но есть неточности."
        else:
            feedback = "Ответ недостаточно точный."

        return gpt_score / 10, feedback

    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {e}")
        return 0.0, "Произошла ошибка при оценке ответа."
