import mysql.connector
import time
import os
from dotenv import load_dotenv
#import psycopg2



def get_connection():
    """
    Устанавливает и возвращает соединение с базой данных Moodle.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Объект соединения с БД
    """
    load_dotenv()
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
# def get_connection():
#     return psycopg2.connect(
#         host=os.getenv("DB_HOST"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         database=os.getenv("DB_NAME")
#     )

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

def get_questions_without_answers():
    """Получает список вопросов без эталонных ответов в graderinfo"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT q.id, q.name, q.questiontext
    FROM mdl_question q
    LEFT JOIN mdl_qtype_essay_options e ON q.id = e.questionid
    WHERE q.qtype = 'essay'
      AND q.parent = 0
      AND (
          e.graderinfo IS NULL 
          OR e.graderinfo = '' 
          OR e.graderinfo = '<p></p>'
          OR e.graderinfo = '<p><br></p>'
          OR e.id IS NULL
      )
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return results

def save_evaluation(attemptid, score, explanation=None):
    conn = get_connection()
    cursor = conn.cursor()

    score_fraction = min(0.9999999, round(score, 7))
    explanation_text = explanation or ""
    now_ts = int(time.time())

    # Получаем данные об использовании и maxmark
    cursor.execute("""
        SELECT questionusageid, questionid, maxmark
        FROM mdl_question_attempts
        WHERE id = %s
    """, (attemptid,))
    qu = cursor.fetchone()
    quba_id, questionid, maxmark = qu

    # Обновляем основную попытку
    cursor.execute("""
        UPDATE mdl_question_attempts
        SET maxfraction = %s, rightanswer = %s, flagged = 1
        WHERE id = %s
    """, (score_fraction, explanation_text, attemptid))

    # Вычисляем следующий number шага
    cursor.execute("""
        SELECT COALESCE(MAX(sequencenumber), 0) + 1
        FROM mdl_question_attempt_steps
        WHERE questionattemptid = %s
    """, (attemptid,))
    next_seq = cursor.fetchone()[0]

    # Определяем state
    state = 'gradedright' if score_fraction >= 0.9 else \
            'gradedpartial' if score_fraction >= 0.1 else \
            'gradedwrong'

    # Вставляем шаг с fraction
    cursor.execute("""
        INSERT INTO mdl_question_attempt_steps
            (questionattemptid, sequencenumber, state, timecreated, userid, fraction)
        VALUES (%s, %s, %s, %s, COALESCE((SELECT quiz.userid FROM mdl_quiz_attempts quiz
                                         JOIN mdl_question_attempts qa ON qa.questionusageid = quiz.uniqueid
                                         WHERE qa.id = %s), 0),
                %s)
    """, (attemptid, next_seq, state, now_ts, attemptid, score_fraction))
    step_id = cursor.lastrowid

    # Добавляем параметры шага (ваше значение оценки и комментарий)
    cursor.execute("""
        INSERT INTO mdl_question_attempt_step_data (attemptstepid, name, value)
        VALUES
            (%s, ':-mark', %s),
            (%s, ':-comment', %s)
    """, (step_id, str(score_fraction), step_id, explanation_text))

    # Пересчёт общей оценки теста
    cursor.execute("""
        UPDATE mdl_quiz_attempts qa
        JOIN (
            SELECT questionusageid, SUM(maxfraction * maxmark) AS total
            FROM mdl_question_attempts
            WHERE questionusageid = %s
            GROUP BY questionusageid
        ) AS sums ON qa.uniqueid = sums.questionusageid
        SET qa.sumgrades = sums.total
    """, (quba_id,))

    conn.commit()
    conn.close()


def update_grader_info(question_id, grader_info):
    """Обновляет graderinfo для указанного вопроса"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже запись для этого вопроса
        cursor.execute("""
            SELECT id FROM mdl_qtype_essay_options 
            WHERE questionid = %s
        """, (question_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Обновляем существующую запись (без timemodified)
            cursor.execute("""
                UPDATE mdl_qtype_essay_options 
                SET graderinfo = %s,
                    graderinfoformat = 1
                WHERE questionid = %s
            """, (grader_info, question_id))
        else:
            # Создаем новую запись (без timemodified)
            cursor.execute("""
                INSERT INTO mdl_qtype_essay_options 
                (questionid, graderinfo, graderinfoformat, responseformat, responserequired, responsefieldlines)
                VALUES (%s, %s, 1, 'editor', 1, 15)
            """, (question_id, grader_info))
        
        # Обновим timemodified в основном вопросе
        cursor.execute("""
            UPDATE mdl_question
            SET timemodified = UNIX_TIMESTAMP()
            WHERE id = %s
        """, (question_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при обновлении graderinfo: {e}")
        return False
    finally:
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