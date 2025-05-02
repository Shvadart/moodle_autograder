import mysql.connector
import time

def get_connection():
    return mysql.connector.connect(
        host="mariadb",
        user="moodleuser",
        password="moodlepass",
        database="moodle"
    )

def get_pending_answers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        qa.id AS attemptid,
        qa.questionid,
        qa.responsesummary
    FROM mdl_question_attempts qa
    JOIN mdl_question_usages qu ON qa.questionusageid = qu.id
    JOIN mdl_quiz_attempts qza ON qza.uniqueid = qu.id
    JOIN mdl_question q ON qa.questionid = q.id
    WHERE qa.behaviour = 'manualgraded'
      AND qa.responsesummary IS NOT NULL
      AND qa.maxfraction = 1.0000000  # Только строго неоценённые
      AND qa.flagged = 0  # Только необработанные
      AND q.qtype = 'essay'
    """

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return [(row["attemptid"], row["questionid"], row["responsesummary"]) for row in results]

def save_evaluation(attemptid, score, explanation=None):
    """
    Сохраняет оценку ответа и шаг в попытке, чтобы Moodle показал результат.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    score_fraction = min(0.9999999, round(score, 7))
    explanation_text = explanation or ""

    # Получаем данные по попытке, чтобы узнать questionusageid
    cursor.execute("""
        SELECT questionusageid, slot, questionid
        FROM mdl_question_attempts
        WHERE id = %s
    """, (attemptid,))
    attempt = cursor.fetchone()

    questionusageid = attempt["questionusageid"]
    slot = attempt["slot"]
    questionid = attempt["questionid"]

    # Обновляем основную попытку
    cursor.execute("""
        UPDATE mdl_question_attempts
        SET maxfraction = %s, 
            rightanswer = %s,
            flagged = 1  # Помечаем как обработанное
        WHERE id = %s
    """, (score_fraction, explanation_text, attemptid))

    # Получаем текущий sequence number
    cursor.execute("""
        SELECT MAX(sequencenumber) as seq FROM mdl_question_attempt_steps
        WHERE questionattemptid = %s
    """, (attemptid,))
    seq_row = cursor.fetchone()
    next_seq = (seq_row["seq"] or 0) + 1

    # Добавляем шаг с выставлением оценки
    state = 'gradedright' if score_fraction >= 0.9 else 'gradedpartial' if score_fraction >= 0.1 else 'gradedwrong'
    cursor.execute("""
        INSERT INTO mdl_question_attempt_steps (questionattemptid, sequencenumber, state, timecreated)
        VALUES (%s, %s, %s, %s)
    """, (attemptid, next_seq, state, int(time.time())))

    # Обновляем общую оценку по тесту
    cursor.execute("""
        SELECT SUM(maxfraction * qa.maxmark) as total
        FROM mdl_question_attempts qa
        WHERE qa.questionusageid = %s
    """, (questionusageid,))

    total = cursor.fetchone()["total"] or 0.0

    cursor.execute("""
        UPDATE mdl_quiz_attempts
        SET sumgrades = %s
        WHERE uniqueid = %s
    """, (total, questionusageid))

    conn.commit()
    conn.close()

def get_question_info(questionid):
    """
    Возвращает текст вопроса и эталонный ответ.
    Для эссе берет graderinfo, для остальных — generalfeedback.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Сначала получаем тип вопроса
    cursor.execute("""
        SELECT q.questiontext, q.generalfeedback, q.qtype
        FROM mdl_question q
        WHERE q.id = %s
    """, (questionid,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "", ""

    question_text = row["questiontext"]
    correct_answer = row["generalfeedback"] or ""
    qtype = row["qtype"]

    # Если вопрос — эссе, берем graderinfo
    if qtype == "essay":
        cursor.execute("""
            SELECT graderinfo
            FROM mdl_qtype_essay_options
            WHERE questionid = %s
        """, (questionid,))
        essay_row = cursor.fetchone()
        if essay_row and essay_row["graderinfo"]:
            correct_answer = essay_row["graderinfo"]

    conn.close()
    return question_text, correct_answer
