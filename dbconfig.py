import sqlite3

DB_NAME = 'data/student_stats.db'

SCHEMA_SQL = """
    CREATE TABLE ExamType (
        id      INTEGER PRIMARY KEY,
        name    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE Student (
        id      INTEGER PRIMARY KEY,
        name    TEXT NOT NULL
    );

    CREATE TABLE Course (
        id      INTEGER PRIMARY KEY,
        name    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE hasWeights (
        course_id           INTEGER NOT NULL,
        exam_type_id        INTEGER NOT NULL,
        weight              REAL NOT NULL,
        required_presences  INTEGER NOT NULL,
        
        PRIMARY KEY (course_id, exam_type_id),
        FOREIGN KEY (course_id) REFERENCES Course(id),
        FOREIGN KEY (exam_type_id) REFERENCES ExamType(id)
    );

    CREATE TABLE hasTodo (
        todo_id                 INTEGER PRIMARY KEY,
        course_id               INTEGER NOT NULL,
        exam_type_id            INTEGER NOT NULL,
        max_points              INTEGER NOT NULL,
        weight                  REAL NOT NULL,
        deadline                TEXT NOT NULL,
        
        FOREIGN KEY (course_id) REFERENCES Course(id),
        FOREIGN KEY (exam_type_id) REFERENCES ExamType(id)
    );

    CREATE TABLE hasDone (
        student_id  INTEGER NOT NULL,
        todo_id     INTEGER NOT NULL,
        points      REAL,
        handled     TEXT,
        
        PRIMARY KEY (student_id, todo_id),
        FOREIGN KEY (student_id) REFERENCES Student(id),
        FOREIGN KEY (todo_id) REFERENCES hasTodo(todo_id)
    );

    CREATE TABLE hasPresences (
        student_id      INTEGER NOT NULL,
        course_id       INTEGER NOT NULL,
        exam_type_id    INTEGER NOT NULL,
        presences       INTEGER NOT NULL,
        
        PRIMARY KEY (student_id, course_id, exam_type_id),
        FOREIGN KEY (student_id)    REFERENCES Student(id),
        FOREIGN KEY (course_id)     REFERENCES Course(id),
        FOREIGN KEY (exam_type_id)  REFERENCES ExamType(id)
    );

    CREATE TABLE AttendanceStats (
        course_id   INTEGER NOT NULL,
        student_id  INTEGER NOT NULL,
        final_grade REAL,               -- The official final numeric grade (e.g., 7.5)
        success     TEXT,               -- The categorical outcome (e.g., 'Pass', 'Fail')
        
        PRIMARY KEY (course_id, student_id),
        FOREIGN KEY (course_id)     REFERENCES Course(id),
        FOREIGN KEY (student_id)    REFERENCES Student(id)
    );
    """

# Connects to database origin file
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Failed to connect to database using connection string {db_file}: {e}")

# Setup the database using SQLite instructions from schema
def setup_database(conn):
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            tables = ['AttendanceStats', 'hasPresences', 'hasDone', 'hasTodo', 'hasWeights', 'Course', 'ExamType', 'Student']
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            # Recreates all tables
            cursor.executescript(SCHEMA_SQL)
            conn.commit()

            print("Database schema created successfully.")
        except sqlite3.Error as e:
            print(f"Failed to connect create the database schema: {e}")
    else:
        print("Failed to connect to database")

def run_db_setup():
    print(">>> Setting up / Replacing database <<<")

    print(f"Trying to connect to {DB_NAME}...")
    conn = create_connection(DB_NAME)
    
    if conn:
        setup_database(conn)
        conn.close()
        print("Database setup complete.")
    else:
        print("Database operation aborted.")

def seed_db():
    return