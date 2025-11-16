import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dbconfig import create_connection, DB_NAME

DATE_FORMAT = "%d.%m.%Y"

def get_init_data():
    def get_random_date(start_date_str, end_date_str):
        start_date = datetime.strptime(start_date_str, DATE_FORMAT)
        end_date = datetime.strptime(end_date_str, DATE_FORMAT)

        time_difference = end_date - start_date
        days_in_interval = time_difference.days
        random_days = random.randrange(days_in_interval + 1)

        random_date = start_date + timedelta(days=random_days)

        return random_date


    def get_datetime_dependency(calc_date, data_thresholds):
        if calc_date < data_thresholds[1]:
            return 80, 20
        elif calc_date < data_thresholds[0]:
            return 60, 40

        return 60, 40 # Default case

    # Random calculation date
    calc_date = get_random_date("01.10.2025", "01.02.2026")
    
    # Datatime dependencies thresholds
    data_thresholds = list(map(lambda x: datetime.strptime(x, "%d.%m.%Y"), ["01.12.2025", "01.01.2026"]))

    # Default datetime dependent presences / todos weights 
    return get_datetime_dependency(calc_date, data_thresholds)

student_adjustments = {}
def adjust_todo(group: pd.DataFrame) -> pd.DataFrame:
    global student_adjustments

    def adjust_generator():
        rates = [0.0005, 0.001, 0.002, 0.004, 0.008] 
        rate_index = 0
        
        while True:
            if rate_index < len(rates):
                yield rates[rate_index]
                rate_index += 1
            else:
                yield 0

    student_id = group.name[0]

    if student_id not in student_adjustments:
        student_adjustments[student_id] = {'gen': adjust_generator(), 'count': 0}

    group = group.sort_values(by='deadline', ascending=True)

    final_adjustment_percent = 0

    for index, row in group.iterrows():
        diff_days = row['diff_days']
        
        if diff_days != 0 and pd.notna(row['handled']):
            
            try:
                adjust_rate = next(student_adjustments[student_id]['gen']) 
            except StopIteration:
                adjust_rate = 0 
                
            days_limit = min(abs(diff_days), 30)
            
            final_adjust = adjust_rate * days_limit * 100
            
            if diff_days > 0:
                final_adjustment_percent -= final_adjust
            elif diff_days < 0:
                final_adjustment_percent += final_adjust
                
    return pd.Series({
        'Ajustare_Delay/Bonus': final_adjustment_percent,
        'PunctajNormalizatTodo_E_Unic': group['PunctajNormalizatTodo_E'].iloc[0]
    })

def compute_metrics(data: pd.DataFrame) -> pd.DataFrame:
    w_presence, w_todos = get_init_data()

    data['handled'] = pd.to_datetime(data['handled'], format="%d.%m.%Y", errors='coerce')
    data['deadline'] = pd.to_datetime(data['deadline'], format="%d.%m.%Y", errors='coerce')

# ScorTotalTodo(E)
    data['scor_total_todo'] = (data['points'] / data['max_points']) * data['todo_weight']


# PunctajNormalizatTodo(E) (Normalization)
    todo_scores = data.groupby(['student_id', 'course_id', 'exam_type_id']).agg(
        scor_total_todo_E=('scor_total_todo', 'sum'),
        suma_greutati_todo_E=('todo_weight', 'sum')
    ).reset_index()

    todo_scores['PunctajNormalizatTodo_E'] = (
        todo_scores['scor_total_todo_E'] / todo_scores['suma_greutati_todo_E']
    ) * 100

    data = data.merge(todo_scores[['student_id', 'course_id', 'exam_type_id', 'PunctajNormalizatTodo_E', 'suma_greutati_todo_E']],
                      on=['student_id', 'course_id', 'exam_type_id'], 
                      how='left')
    

# Delay/Bonus adjustments
    data['diff_days'] = data.apply(lambda row: (row['handled'] - row['deadline']).days if pd.notna(row['handled']) else 0, axis=1)


# Applies bonuses/delays
    adjustments = data.groupby(['student_id', 'course_id']).apply(adjust_todo, include_groups=False).reset_index()
    final_scores = todo_scores.merge(adjustments[['student_id', 'course_id', 'Ajustare_Delay/Bonus']],
                                     on=['student_id', 'course_id'], 
                                     how='left')


# PunctajAjustatTodo_E = PunctajNormalizatTodo_E * (1 + Ajustare_Delay/Bonus / 100)
    final_scores['PunctajAjustatTodo_E'] = final_scores.apply(
        lambda row: row['PunctajNormalizatTodo_E'] * (1 + row['Ajustare_Delay/Bonus'] / 100.0), axis=1
    )


# PunctajComponentaExamene (PCE)
    exam_weights = data[['course_id', 'exam_type_id', 'exam_weight']].drop_duplicates()
    final_scores = final_scores.merge(exam_weights, 
                                      on=['course_id', 'exam_type_id'], 
                                      how='left')
    
    final_scores['PunctajComponentaExamene'] = final_scores['PunctajAjustatTodo_E'] * (final_scores['exam_weight'] / 100.0)


# Aggregation of PCE to [Student_Id, Course_Id]
    pce = final_scores.groupby(['student_id', 'course_id'])['PunctajComponentaExamene'].sum().reset_index()
    pce.rename(columns={'PunctajComponentaExamene': 'PunctajComponentaExamene'}, inplace=True)


# IndeplinitPrezente(E)
    # Keeps only relevant data
    presences_data = data[['student_id', 'course_id', 'exam_type_id', 'presences', 'required_presences', 'exam_weight']]\
                    .drop_duplicates() 
    
    presences_data['IndeplinitPrezente_E'] = presences_data.apply(lambda row: row['presences'] >= row['required_presences'], axis=1)


    # Ponderates presences with exam's weight
    presences_data['scor_prezenta_ponderat'] = presences_data['IndeplinitPrezente_E'] * presences_data['exam_weight']


    # Aggregates and computes a final presence score
    presences_scores = presences_data.groupby(['student_id', 'course_id']).agg(
        scor_prezenta_total=('scor_prezenta_ponderat', 'sum'),
        total_greutati_exam=('exam_weight', 'sum')
    ).reset_index()

    presences_scores['ScorPrezenteExam'] = (
        presences_scores['scor_prezenta_total'] / presences_scores['total_greutati_exam']
    ) * 100

    final_data = pce.merge(presences_scores[['student_id', 'course_id', 'ScorPrezenteExam']], 
                            on=['student_id', 'course_id'], 
                            how='inner')
    
    adjustment_unique = adjustments[['student_id', 'course_id', 'Ajustare_Delay/Bonus']].drop_duplicates()

    final_data = final_data.merge(adjustment_unique, 
                                on=['student_id', 'course_id'], 
                                how='left')


# Applies datetime dependent weights for presences and tasks
    final_data['NotaAproximativa'] = (
        (final_data['PunctajComponentaExamene'] * w_todos) + 
        (final_data['ScorPrezenteExam'] * w_presence)
    ) / 1000.0 

    # Final class tagging
    final_data['Class'] = np.where(final_data['NotaAproximativa'] >= 5.0, 'Promovat', 'Nepromovat')
    
    return final_data


def run_db_classification():
    print("\n\n>>> Started data classification <<<\n")

    print(f"Trying to connect to {DB_NAME}...")
    conn = create_connection(DB_NAME)
    if conn:
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
        conn.close()
        print("Database fetching complete.")
    else:
        print("Database operation aborted.")

    try:
        final_data = compute_metrics(data)

        to_show = 20
        print(f"Preview {to_show} lines from dataframe with relevant metrics")
        print(final_data.head(to_show))

        return final_data
    
    except:
        print("Exception thrown while computing metrics in classification.py/compute_metrics() ")

    return final_data