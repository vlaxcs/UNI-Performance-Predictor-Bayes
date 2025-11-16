import os
import random
import sqlite3
import importlib.util
from datetime import datetime, timedelta
from dbconfig import create_connection, DB_NAME

basefile_dir = os.path.abspath(os.path.dirname(__file__)) if '__file__' in locals() else '/app_directory'


def seed_examType(conn):
    print(">> Seeding table ExamType")

    names = ['Course', 'Laboratory', 'Seminary']
    sql = 'INSERT INTO ExamType (name) VALUES (?);'
    
    try:
        cursor = conn.cursor()
        for name in names:
            cursor.execute(sql, (name,))
            print(f"\tInserted ExamType: {name}")
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"\tIntegrity Error: {e}. Data likely already exists.")
    except Exception as e:
        print(f"\tAn error occurred during ExamType seeding: {e}")


def seed_student(conn):    
    spec = importlib.util.spec_from_file_location("data", "data/student_names.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    FIRST_NAMES = module.FIRST_NAMES
    LAST_NAMES = module.SURNAMES
    
    print(">> Seeding table Student")
    
    sql = 'INSERT INTO Student (name) VALUES (?);'
    
    try:
        cursor = conn.cursor()
        
        for _ in range (0, 200):
            student_name = " ".join([random.choice(LAST_NAMES), random.choice(FIRST_NAMES)]).strip()
            cursor.execute(sql, (student_name,))
            print(f"\tInserted Student: {student_name}")

        conn.commit()

    except sqlite3.IntegrityError as e:
        print(f"\tIntegrity Error: {e}. Data likely already exists.")
    except Exception as e:
        print(f"\tAn error occurred during Student seeding: {e}")


def seed_course(conn):
    courses_file = f"{basefile_dir}/data/course_names.csv"
    
    print(">> Seeding table Course")
    
    sql = 'INSERT INTO Course (name) VALUES (?);'
    
    try:
        cursor = conn.cursor()

        with open(courses_file, 'r', encoding='utf-8') as f:
            for name in f.readlines():
                course_name = name.strip()
                if course_name:
                    cursor.execute(sql, (course_name,))
                    print(f"\tInserted Student: {course_name}")

        conn.commit()

    except sqlite3.IntegrityError as e:
        print(f"\tIntegrity Error: {e}. Data likely already exists.")
    except Exception as e:
        print(f"\tAn error occurred during Student seeding: {e}")


def seed_hasWeights(conn):
    print(">> Seeding table hasWeights")

    sql_courses = "SELECT id FROM Course;"
    sql_examTypes = "SELECT id FROM ExamType;"
    sql_insert = "INSERT INTO hasWeights (course_id, exam_type_id, weight, required_presences) VALUES (?, ?, ?, ?);"
    
    try:
        cursor = conn.cursor()
        
        cursor.execute(sql_courses)
        courses = [row[0] for row in cursor.fetchall()]
        print(f"\tTotal number of courses found: {len(courses)}")

        cursor.execute(sql_examTypes)
        exam_types = [row[0] for row in cursor.fetchall()]
        print(f"\tTotal number of exam types found: {len(exam_types)}")

        allowed_presences = [0, 5, 7, 10, 14]
        allowed_percentages = [[50, 60, 70], [20, 30]]
        generated_relations = 0
        for course_id in courses:
            total_weight = 100
            for idx, exam_type_id in enumerate(exam_types):
                required_presences = random.choice(allowed_presences)
                weight = 0
                if idx < 2:
                    weight = random.choice(allowed_percentages[idx])
                    total_weight = total_weight - weight
                else:
                    weight = total_weight

                record = (course_id, exam_type_id, weight, required_presences)
                cursor.execute(sql_insert, record)

                generated_relations += 1

        conn.commit()
        print(f"\tSuccessfully seeded **{generated_relations}** records into hasWeights.")
        
    except sqlite3.OperationalError as e:
        print(f"\tDatabase Operational Error: {e}.")
    except Exception as e:
        print(f"\tAn error occurred during hasWeights seeding: {e}")


def get_random_date(start_date_str, end_date_str):
    date_format = "%d.%m.%Y"
    start_date = datetime.strptime(start_date_str, date_format).date()
    end_date = datetime.strptime(end_date_str, date_format).date()
    
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    
    if days_between_dates <= 0:
        return start_date.strftime(date_format)

    random_number_of_days = random.randrange(days_between_dates + 1)
    random_date = start_date + timedelta(days=random_number_of_days)
    
    return random_date.strftime(date_format)


def seed_hasTodo(conn):
    print(">> Seeding table hasTodo")

    sql_components = "SELECT course_id, exam_type_id FROM hasWeights;"

    sql_insert = """
        INSERT INTO hasTodo (course_id, exam_type_id, max_points, weight, deadline) 
        VALUES (?, ?, ?, ?, ?);
    """

    START_DATE = "01.10.2025"
    END_DATE = "01.02.2026"

    try:
        cursor = conn.cursor()
        
        cursor.execute(sql_components)
        components = cursor.fetchall()
        print(f"\tTotal number of (courses x exams) found: {len(components)}")

        allowed_max_points = [5, 10]
        allowed_weight = [25, 50, 100]
        generated_todos = 0


        for course_id, exam_type_id in components:
            course_todos = [] 
            current_weight = 100

            while current_weight > 0:
                available_weights = [w for w in allowed_weight if w <= current_weight]
                if current_weight <= min(allowed_weight) or not available_weights:
                    weight_to_use = current_weight
                else:
                    weight_to_use = random.choice(available_weights)
                
                max_points = random.choice(allowed_max_points)
                deadline = get_random_date(START_DATE, END_DATE)

                record = (course_id, exam_type_id, max_points, weight_to_use, deadline)
                course_todos.append(record)
                current_weight -= weight_to_use

            cursor.executemany(sql_insert, course_todos)
            generated_todos += len(course_todos)

        conn.commit()
        print(f"\tSuccessfully seeded **{generated_todos}** records into hasTodo.")
        
    except sqlite3.OperationalError as e:
        print(f"\tDatabase Operational Error: {e}.")
    except Exception as e:
        print(f"\tAn error occurred during hasTodo seeding: {e}")


def seed_hasDone(conn):
    print(">> Seeding table hasDone")

    sql_students = "SELECT id FROM Student;"
    sql_todos = "SELECT todo_id, max_points, deadline FROM hasTodo;"
    sql_insert = """
        INSERT INTO hasDone (student_id, todo_id, points, handled) 
        VALUES (?, ?, ?, ?);
    """

    DATE_FORMAT = "%d.%m.%Y"

    try:
        cursor = conn.cursor()

        cursor.execute(sql_students)
        students = [row[0] for row in cursor.fetchall()]
        print(f"\tTotal number of students found: {len(students)}")

        cursor.execute(sql_todos)
        todos = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        print(f"\tTotal number of todo's found: {len(todos)}")

        generated_done_todos = 0

        for student_id in students:
            done_todos = []

            for (todo_id, todo_max_points, deadline_str) in todos:
                deadline_date = datetime.strptime(deadline_str, DATE_FORMAT).date()
                start_date_str = (deadline_date - timedelta(days=30)).strftime(DATE_FORMAT)
                end_date_str = (deadline_date + timedelta(days=30)).strftime(DATE_FORMAT)

                handled = random.choice([None, get_random_date(start_date_str, end_date_str)])
                points = 0 if handled is None else random.randint(0, todo_max_points)

                record = (student_id, todo_id, points, handled)
                done_todos.append(record)

            cursor.executemany(sql_insert, done_todos)
            generated_done_todos += len(done_todos)
        
        conn.commit()
        print(f"\tSuccessfully seeded **{generated_done_todos}** records into hasDone.")

    except sqlite3.OperationalError as e:
        print(f"\tDatabase Operational Error: {e}.")
    except Exception as e:
        print(f"\tAn error occurred during hasDone seeding: {e}")


def seed_hasPresences(conn):
    print(">> Seeding table hasPresences")

    sql_students = "SELECT id FROM Student;"
    sql_course_stats = "SELECT course_id, exam_type_id, required_presences FROM hasWeights;"
    
    sql_insert = """
        INSERT INTO hasPresences (student_id, course_id, exam_type_id, presences) 
        VALUES (?, ?, ?, ?);
    """

    try:
        cursor = conn.cursor()
        
        cursor.execute(sql_students)
        students = [row[0] for row in cursor.fetchall()]
        print(f"\tTotal number of students found: {len(students)}")

        cursor.execute(sql_course_stats)
        course_stats = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        print(f"\tTotal number of course stats found: {len(course_stats)}")

        generated_presences = 0

        for student_id in students:
            incoming_presences = []

            for (course_id, exam_type_id, required_presences) in course_stats:
                presences = random.randint(0, required_presences + random.randint(0, 7) if required_presences <= 7 else 0)                
                record = (student_id, course_id, exam_type_id, presences)
                incoming_presences.append(record)

            cursor.executemany(sql_insert, incoming_presences)
            generated_presences += len(incoming_presences)

        print(f"\tSuccessfully seeded **{generated_presences}** records into hasPresences.")
        conn.commit()

    except sqlite3.OperationalError as e:
        print(f"\tDatabase Operational Error: {e}.")
    except Exception as e:
        print(f"\tAn error occurred during hasPresences seeding: {e}")

import pandas as pd
def run_db_seed():
    print(">>> Seeding database <<<")

    print(f"Trying to connect to {DB_NAME}...")
    conn = create_connection(DB_NAME)
    if conn:
        seed_examType(conn)
        seed_student(conn)
        seed_course(conn)
        seed_hasWeights(conn)
        seed_hasTodo(conn)
        seed_hasDone(conn)
        seed_hasPresences(conn)

        query = """
            SELECT
                S.id AS student_id,
                HW.course_id AS course_id,
                HW.exam_type_id AS exam_type_id,
                HW.weight AS exam_weight,
                HW.required_presences,
                HT.todo_id AS todo_id,
                HT.max_points,
                HT.weight AS todo_weight,
                HT.deadline,
                HD.points,
                HD.handled,
                HP.presences
            FROM Student S
            JOIN Course C
            JOIN hasWeights HW ON C.id = HW.course_id
            LEFT JOIN hasTodo HT ON C.id = HT.course_id AND HW.exam_type_id = HT.exam_type_id
            LEFT JOIN hasDone HD ON S.id = HD.student_id AND HT.todo_id = HD.todo_id
            LEFT JOIN hasPresences HP ON S.id = HP.student_id AND C.id = HP.course_id AND HW.exam_type_id = HP.exam_type_id
            ORDER BY student_id, course_id, exam_type_id, todo_id;
        """
        
        data = pd.read_sql_query(query, conn)

        to_show = 20
        print(f"Preview {to_show} lines from raw dataframe")
        print(data.head(to_show))

        conn.close()
        print("Database seeding complete.")
    else:
        print("Database operation aborted.")