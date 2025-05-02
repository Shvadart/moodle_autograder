# Импорт необходимых библиотек
import os  # Для работы с переменными окружения и файловой системой
from openai import OpenAI  # Официальный клиент OpenAI API
from nltk.tokenize import word_tokenize  # Для токенизации текста
from nltk.stem import WordNetLemmatizer  # Для лемматизации слов
from dotenv import load_dotenv  # Для загрузки переменных окружения из .env файла
import nltk  # Библиотека Natural Language Toolkit для обработки естественного языка

# Загружаем переменные окружения из файла .env
load_dotenv()

# Инициализируем лемматизатор для приведения слов к их базовой форме
lemmatizer = WordNetLemmatizer()

# Создаем клиент для работы с OpenAI API
# API ключ и базовый URL берутся из переменных окружения
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def lemmatize_text(text):
    """
    Лемматизирует входной текст, приводя слова к их базовой форме.
    
    Параметры:
        text (str): Входной текст для обработки
    
    Возвращает:
        list: Список лемматизированных слов в нижнем регистре
    """
    # Токенизируем текст на отдельные слова
    tokens = word_tokenize(text)
    # Лемматизируем каждый токен и приводим к нижнему регистру
    return [lemmatizer.lemmatize(token.lower()) for token in tokens]

def evaluate_answer(answer_text, question, correct_answer):
    """
    Оценивает ответ студента с помощью OpenAI GPT-4 по 10-балльной шкале.
    
    Параметры:
        answer_text (str): Ответ студента
        question (str): Вопрос, на который отвечал студент
        correct_answer (str): Правильный ответ (может быть пустым)
    
    Возвращает:
        tuple: (нормализованная оценка от 0 до 1, текстовая обратная связь)
               или (0.0, сообщение об ошибке) в случае исключения
    """
    # Формируем промпт для GPT в зависимости от наличия правильного ответа
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
        # Отправляем запрос к OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # Используем модель GPT-4
            messages=[
                {"role": "system", "content": "Ты — ассистент преподавателя, проверяющий ответы студентов."},
                {"role": "user", "content": prompt}
            ]
        )

        # Извлекаем и обрабатываем ответ от GPT
        gpt_score_str = response.choices[0].message.content.strip()  # Получаем строку с оценкой
        gpt_score = float(gpt_score_str)  # Преобразуем в число

        # Формируем текстовую обратную связь на основе оценки
        if gpt_score > 8:
            feedback = "Отличный ответ!"
        elif gpt_score > 5:
            feedback = "Неплохо, но есть неточности."
        else:
            feedback = "Ответ недостаточно точный."

        # Возвращаем оценку (нормализованную до 0-1) и обратную связь
        return gpt_score / 10, feedback

    except Exception as e:
        # Обработка возможных ошибок при запросе к API
        print(f"Ошибка при обращении к OpenAI: {e}")
        return 0.0, "Произошла ошибка при оценке ответа."