import mysql.connector
import time

def get_connection():
    """
    Устанавливает и возвращает соединение с базой данных Moodle.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Объект соединения с БД
    """
    return mysql.connector.connect(
        host="mariadb",          # Хост базы данных
        user="moodleuser",       # Имя пользователя БД
        password="moodlepass",   # Пароль пользователя БД
        database="moodle"        # Название базы данных
    )

def get_pending_answers():
    """
    Получает список неоцененных ответов на вопросы типа 'essay', требующих ручной проверки.
    
    Returns:
        list[tuple]: Список кортежей вида (attemptid, questionid, responsesummary)
                    для каждого неоцененного ответа
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)  # Используем словарь для удобства доступа к полям

    # SQL-запрос для поиска неоцененных ответов на эссе
    query = """
    SELECT
        qa.id AS attemptid,
        qa.questionid,
        qa.responsesummary
    FROM mdl_question_attempts qa
    JOIN mdl_question_usages qu ON qa.questionusageid = qu.id
    JOIN mdl_quiz_attempts qza ON qza.uniqueid = qu.id
    JOIN mdl_question q ON qa.questionid = q.id
    WHERE qa.behaviour = 'manualgraded'      # Только ответы, требующие ручной проверки
      AND qa.responsesummary IS NOT NULL     # Только ответы с заполненным текстом
      AND qa.maxfraction = 1.0000000        # Только строго неоценённые (максимальный балл не изменялся)
      AND qa.flagged = 0                     # Только необработанные (не помеченные флагом)
      AND q.qtype = 'essay'                  # Только вопросы типа 'эссе'
    """

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    # Формируем список кортежей с нужными полями
    return [(row["attemptid"], row["questionid"], row["responsesummary"]) for row in results]

def save_evaluation(attemptid, score, explanation=None):
    """
    Сохраняет оценку ответа в базе данных Moodle и обновляет связанные данные.
    
    Args:
        attemptid (int): ID попытки ответа на вопрос
        score (float): Оценка (должна быть между 0 и 1)
        explanation (str, optional): Комментарий к оценке. По умолчанию None.
    
    Процесс:
        1. Получает метаданные о попытке
        2. Обновляет основную запись о попытке
        3. Добавляет шаг оценки в историю попытки
        4. Пересчитывает общую оценку за тест
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Нормализуем оценку (Moodle использует дробные значения от 0 до 1)
    score_fraction = min(0.9999999, round(score, 7))  # Ограничиваем максимальную оценку
    explanation_text = explanation or ""              # Используем пустую строку если explanation=None

    # 1. Получаем метаданные о попытке
    cursor.execute("""
        SELECT questionusageid, slot, questionid
        FROM mdl_question_attempts
        WHERE id = %s
    """, (attemptid,))
    attempt = cursor.fetchone()

    questionusageid = attempt["questionusageid"]  # ID использования вопроса
    slot = attempt["slot"]                        # Позиция вопроса в тесте
    questionid = attempt["questionid"]            # ID вопроса

    # 2. Обновляем основную запись о попытке
    cursor.execute("""
        UPDATE mdl_question_attempts
        SET maxfraction = %s,         # Устанавливаем оценку
            rightanswer = %s,         # Сохраняем комментарий
            flagged = 1               # Помечаем как обработанное
        WHERE id = %s
    """, (score_fraction, explanation_text, attemptid))

    # 3. Получаем следующий номер шага для истории попытки
    cursor.execute("""
        SELECT MAX(sequencenumber) as seq FROM mdl_question_attempt_steps
        WHERE questionattemptid = %s
    """, (attemptid,))
    seq_row = cursor.fetchone()
    next_seq = (seq_row["seq"] or 0) + 1  # Увеличиваем максимальный номер на 1

    # Определяем состояние оценки на основе полученных баллов
    state = 'gradedright' if score_fraction >= 0.9 else \
            'gradedpartial' if score_fraction >= 0.1 else \
            'gradedwrong'

    # Добавляем шаг оценки в историю попытки
    cursor.execute("""
        INSERT INTO mdl_question_attempt_steps 
            (questionattemptid, sequencenumber, state, timecreated)
        VALUES (%s, %s, %s, %s)
    """, (attemptid, next_seq, state, int(time.time())))  # Текущее время в Unix timestamp

    # 4. Пересчитываем общую оценку за тест
    cursor.execute("""
        SELECT SUM(maxfraction * qa.maxmark) as total
        FROM mdl_question_attempts qa
        WHERE qa.questionusageid = %s
    """, (questionusageid,))

    total = cursor.fetchone()["total"] or 0.0  # Сумма всех оценок с учетом весов вопросов

    # Обновляем общую оценку в попытке теста
    cursor.execute("""
        UPDATE mdl_quiz_attempts
        SET sumgrades = %s
        WHERE uniqueid = %s
    """, (total, questionusageid))

    conn.commit()  # Фиксируем все изменения
    conn.close()

def get_question_info(questionid):
    """
    Получает текст вопроса и эталонный ответ для указанного вопроса.
    
    Args:
        questionid (int): ID вопроса в базе данных
    
    Returns:
        tuple: (question_text, correct_answer) - текст вопроса и эталонный ответ
    
    Примечание:
        Для вопросов типа 'essay' берет graderinfo из специализированной таблицы,
        для остальных типов вопросов использует generalfeedback.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Получаем основную информацию о вопросе
    cursor.execute("""
        SELECT q.questiontext, q.generalfeedback, q.qtype
        FROM mdl_question q
        WHERE q.id = %s
    """, (questionid,))
    row = cursor.fetchone()

    if not row:  # Если вопрос не найден
        conn.close()
        return "", ""

    question_text = row["questiontext"]                # Текст вопроса
    correct_answer = row["generalfeedback"] or ""      # Общий фидбек (эталонный ответ)
    qtype = row["qtype"]                              # Тип вопроса

    # Для вопросов типа 'essay' получаем дополнительную информацию для оценки
    if qtype == "essay":
        cursor.execute("""
            SELECT graderinfo
            FROM mdl_qtype_essay_options
            WHERE questionid = %s
        """, (questionid,))
        essay_row = cursor.fetchone()
        if essay_row and essay_row["graderinfo"]:
            correct_answer = essay_row["graderinfo"]  # Используем graderinfo для эссе

    conn.close()
    return question_text, correct_answer