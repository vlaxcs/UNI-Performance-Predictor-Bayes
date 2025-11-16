# University Performance Predictor - Bayes Multinomial Predictor

> 251 - Vlad-Andrei Minciunescu \
> University of Bucharest, Faculty of Mathematics and Informatics

## Background

What could be harder to guess than your final grade after you've struggled all semester, especially when you know what your attendance has been to each course? The most frustrating part is when the final grade doesn't always depend on your semester attendance. This project illustrates that good attendance can sometimes be a misleading indicator of true academic performance.

## Prerequisites

- Python3:
    - Run this commands (in your default Python environment)
        ```
        pip install sqlite
        pip install scikit-learn
        ```

- DB Browser (SQLite)
    - For better data visualization :)

## Instructions

1. Clone the repository;
2. Open the repository in your IDE;
3. Install these library in your default Python environment:
    - If any other libraries are missing, follow the logs;
    ```
    pip install sqlite
    pip install scikit-learn
    ```
4. Run the main:
    ```
    python3 main.py
    ```
5. You can preview the database object (data/student_stats.db) in DB Browser. Close it if it causes troubles during transactions.
6. Explore the code!

> Disclaimer: Average accuracy: 92-95%

## Structure

- [main.py](./main.py) - Centralizes all functions from separated libraries
    ```    
    from dbconfig import run_db_setup
    from dataconfig import run_db_seed
    from classification import run_db_classification
    from tokenization import run_fd_tokenization
    from naive_bayes import run_naive_bayes

    ...
    ```
    - ### [dbconfig.py *(database)*](./dbconfig.py) - Creates a SQLite3 DB Object with specific structure - read [Data Generation - Tables and rules](#data-generation)
        - I wanted so much to do this experimental project with large data, so I generated mine cause Kaggle was not enough :<
        - Used a **SQLite3 DB**, manipulated in **Python**.

    - ### [dataconfig.py *(database)*](./dataconfig.py) - Seeds and generate data into DB object by rules described at [Data Generation - Tables and rules](#data-generation)
        | student_id | course_id | exam_type_id | exam_weight | required_presences | todo_id | max_points | todo_weight | deadline    | points | handled     | presences |
        |------------|-----------|--------------|-------------|---------------------|---------|------------|-------------|-------------|--------|-------------|-----------|
        | 1          | 1         | 1            | 60.0        | 0                   | 1       | 10         | 25.0        | 10.11.2025  | 2.0    | 26.10.2025  | 1         |
        | 1          | 1         | 1            | 60.0        | 0                   | 2       | 5          | 50.0        | 20.10.2025  | 3.0    | 20.10.2025  | 1         |
        | 1          | 1         | 1            | 60.0        | 0                   | 3       | 5          | 25.0        | 12.11.2025  | 0.0    | None        | 1         |
        | 1          | 1         | 2            | 20.0        | 0                   | 4       | 10         | 25.0        | 29.12.2025  | 5.0    | 28.12.2025  | 0         |
        | 1          | 1         | 2            | 20.0        | 0                   | 5       | 10         | 25.0        | 28.10.2025  | 0.0    | None        | 0         |
        | 1          | 1         | 2            | 20.0        | 0                   | 6       | 5          | 50.0        | 30.01.2026  | 3.0    | 01.02.2026  | 0         |


    - ### [classification.py *(database + dataframe)*](./classification.py) - Based on seeded data, this library contains methods that computes relevant metrics for final tokenization
        - > (context pentru traduceri și pentru formulele în română :)) am decis la jumatea proiectului că vreau să-l fac în engleză, good luck mie cu etichetele din dataframe-uri)
        - Using **hasDone, hasTodo**: \
            [RO]
            - Fiecare sarcină **Todo** oferă un procent de satisfacere a nevoilor de învățare, ca *raport dintre **points / max_points*** (hasDone și hasTodo(hasDone.task_id).max_points)
            - Pentru fiecare raport, se ține cont de ponderea sarcinii și de ponderea asociată tipului de examinare pentru cursul respectiv.

            [EN]
            - Each **Todo** task provides a percentage of learning-needs satisfaction, calculated as the *ratio between **points / max_points*** (hasDone and hasTodo(hasDone.task_id).max_points).
            - For each ratio, the task’s weight and the weight associated with the exam type for the corresponding course are taken into account.

        $$\text{ScorTotalTodo}_E = \sum_{t \in \text{Todo}_E} \left( \frac{\text{hasDone.points}}{\text{hasTodo.max\_points}} \times \text{hasTodo.weight} \right)$$

        $$\text{PunctajNormalizatTodo}_E = \frac{\text{ScorTotalTodo}_E}{\sum_{t \in \text{Todo}_E} \text{hasTodo.weight}} \times 100$$


        - Using **hasDone**:  \
            [RO]
            - Fiecare sarcină:
                - **întârziată (predată după deadline)**, scade valoarea totală a succesului gradual geometric, cu o valoare de început de la **-0,05%, scăzând spre -0,1%, -0.2%, -0.4%**. Această valoare este **înmulțită ulterior cu numărul de zile întârziate (*maxim 30 de zile*)** și se aplică pentru maxim 5 sarcini;
                - **predată înainte de deadline**, **adaugă** la valoarea totală a succesului aceleași valori menționate anterior, pentru **toate sarcinile**;
                - Se folosește o funcție generator `classification.py/adjust_generator()` pentru aplicarea geometrică.

            [EN]
            - Each task:
                - **submitted late (after the deadline)** decreases the total success value using a geometric gradual reduction, starting from **-0.05%, then decreasing toward -0.1%, -0.2%, -0.4%**. This value is then multiplied by the number of delayed days (up to a maximum of 30 days) and applies to a maximum of 5 tasks;
                - **submitted before the deadline** adds to the total success value using the same values mentioned above, for all tasks;
                - A generator function `classification.py/adjust_generator()` is used to apply the geometric adjustment.

            $$\text{PunctajAjustatTodo}_E = \text{PunctajNormalizatTodo}_E \times (1 + \text{Ajustare}_{\text{Delay/Bonus}})$$

            $$\text{PunctajComponentaExamene} = \sum_{E} \left( \text{PunctajAjustatTodo}_E \times \frac{\text{hasWeights.weight}_E}{100} \right)$$

        - Using **hasPresences, hasDone**:
            [RO]
            - Dacă data aleasă pentru calcul (default e random, din intervalul descris în [Data Generation - Tables and rules/hasTodo/deadline](#hastodo)):
                - este înainte de **01.12.2025**, prezențele contează **80%**, iar task-urile din **hasDone** contează **20%**:
                    - **$W_P$ (Prezențe) = 80%**
                    - **$W_T$ (Todo) = 20%**
                - altfel, este înainte de **01.01.2026**, prezențele contează **60%**, iar task-urile din **hasDone** contează **40%**:
                    - **$W_P$ (Prezențe) = 60%**
                    - **$W_T$ (Todo) = 40%**

            [EN]
            - If the chosen date for the calculation (default is random, within the interval described in [Data Generation - Tables and rules/hasTodo/deadline](#hastodo)):
                - is before **01.12.2025**, attendances count **80%**, and tasks from **hasDone** count **20%**:
                    - **$W_P$ (Attendances) = 80%**
                    - **$W_T$ (Todo) = 20%**
                - otherwise, if it is before **01.01.2026**, attendances count **60%**, and tasks from **hasDone** count **40%**:
                    - **$W_P$ (Attendances) = 60%**
                    - **$W_T$ (Todo) = 40%**

                $$\text{IndeplinitPrezente}_E = \begin{cases} 1 & \text{dacă } \text{hasPresences.presences} \ge \text{hasWeights.RequiredPresences} \\ 0 & \text{altfel} \end{cases}$$

                $$\text{NotaAproximativa} = (\text{PunctajComponentaExamene} \times W_T) + (\text{ScorPrezențe} \times W_P)$$

            | student_id | course_id | PunctajComponentaExamene  | ScorPrezenteExam | Ajustare_Delay/Bonus  | NotaAproximativa | Class       |
            |------------|-----------|---------------------------|------------------|-----------------------|------------------|-------------|
            | 1          | 1         | 29.63275                  | 100.0            | 0.45                  | 8.592655         | Promovat    |
            | 1          | 2         | 12.43200                  | 0.0              | 18.40                 | 0.248640         | Nepromovat  |
            | 1          | 3         | 1.00000                   | 0.0              | 0.00                  | 0.020000         | Nepromovat  |
            | 1          | 4         | 24.00000                  | 0.0              | 0.00                  | 0.480000         | Nepromovat  |
            | 1          | 5         | 18.50000                  | 0.0              | 0.00                  | 0.370000         | Nepromovat  |
            | 1          | 6         | 49.50000                  | 90.0             | 0.00                  | 8.190000         | Promovat    |

    - ### [tokenization.py *(dataframe)*](./tokenization.py) - Loads final metrics and filter data into less specific tokens
        | Feature | Condition Range                       | Resulting Token        |
        |---------|----------------------------------------|-------------------------|
        | **PunctajComponentaExamene (pce)** | pce < 30                               | low_todo                |
        |         | 30 ≤ pce < 60                          | medium_todo             |
        |         | pce ≥ 60                               | good_todo               |
        | **ScorPrezenteExam (spe)**         | spe < 50                               | low_presences           |
        |         | 50 ≤ spe < 90                           | medium_presences        |
        |         | spe ≥ 90                                | good_presences          |
        | **Ajustare_Delay/Bonus (adj)**     | adj < -1.0                              | low_motivation          |
        |         | -1.0 < adj ≤ 1.0                        | medium_motivation       |
        |         | adj > 1.0                               | high_motivation         |


    - ### [naive_bayes.py *(dataframe)*](./naive_bayes.py) - Manual implementation of Naive Bayes Multinomial



## Data generation

- ## ExamType
    - Id - Auto-Incremented
    - Names: Course, Laboratory, Seminary (hard-coded)

    ```
    CREATE TABLE ExamType (
        id      INTEGER PRIMARY KEY,
        name    TEXT NOT NULL UNIQUE
    );
    ```

- ## Student
    - Id - Auto-Incremented
    - Name - Randomly generated strings from LAST_NAME and FIRST_NAME lists generated with Gemini

    ```
    CREATE TABLE Student (
        id      INTEGER PRIMARY KEY,
        name    TEXT NOT NULL
    );
    ```

- ## Course
    - Id - Auto-Incremented
    - Name - Load from CSV (course_names.csv), generated with ChatGPT

    ```
    CREATE TABLE Course (
        id      INTEGER PRIMARY KEY,
        name    TEXT NOT NULL UNIQUE
    );
    ```

- ## hasWeights 
    - CourseId - All Id's from Course                       | Count(Course) = n tuples: (CourseId, ExamType)
    - ExamType - All Id's from ExamType for each CourseId   | for each CourseId
    - Percentage 
        - 1 (Course) percentage: Random value from {50, 60, 70}
        - 2 (Laboratory) percentage: Random value from {20, 30}
        - 3 (Seminary) percentage: 100 - [Course% + Laboratory%]
    - RequiredPresences: Random value from {0, 5, 7, 10, 14}
    
    ```
    CREATE TABLE hasWeights (
        course_id           INTEGER NOT NULL,
        exam_type_id        INTEGER NOT NULL,
        weight              REAL NOT NULL,
        required_presences  INTEGER NOT NULL,
        
        PRIMARY KEY (course_id, exam_type_id),
        FOREIGN KEY (course_id) REFERENCES Course(id),
        FOREIGN KEY (exam_type_id) REFERENCES ExamType(id)
    );
    ```

- ## hasTodo
    - Id                - Auto-Incremented
    - CourseId          - All Id's from Course, repeating until sum(WeightPercent[]) = 100
    - ExamTypeId        - Random value from ExamTypeId
    - MaxPoints         - Random value from {5, 10}
    - Weight            - Random value from {10, 20, 40, 100}
    - Deadline          - Random value between [01.10.2025 - 01.02.2026]

    ```
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

    ```

- ## hasDone
    - StudentId - All Id's from Student
    - TodoId    - All Id's from Todo
    - Points    - Random from Todo(TodoId).max_points or 0 if handled is NULL
    - Handled   - Nullable random date time [deadline - 30, deadline + 30]

    ```
    CREATE TABLE hasDone (
        student_id  INTEGER NOT NULL,
        todo_id     INTEGER NOT NULL,
        points      REAL,               -- Actual points achieved (out of MaxPoints)
        handled     TEXT,               -- True if submitted, False otherwise
        
        PRIMARY KEY (student_id, todo_id),
        FOREIGN KEY (student_id) REFERENCES Student(id),
        FOREIGN KEY (todo_id) REFERENCES hasTodo(todo_id)
    );
    ```

- ## hasPresences
    - StudentId     - All Id's from Students
    - CourseId      - All Id's from hasWeights
    - ExamTypeId    - All Id's from hasWeights
    - Presences     - Random value between each [0, hasWeights.RequiredPresences]

    ```
    CREATE TABLE hasPresences (
        student_id      INTEGER NOT NULL,
        course_id       INTEGER NOT NULL,
        exam_type_id    INTEGER NOT NULL,
        presences       INTEGER NOT NULL, -- Number of attended sessions
        
        PRIMARY KEY (student_id, course_id, exam_type_id),
        FOREIGN KEY (student_id)    REFERENCES Student(id),
        FOREIGN KEY (course_id)     REFERENCES Course(id),
        FOREIGN KEY (exam_type_id)  REFERENCES ExamType(id)
    );
    ```