import pandas as pd

def generate_tokens(row: pd.Series) -> list:
    tokens = [None] * 3

    pce = row['PunctajComponentaExamene']
    spe = row['ScorPrezenteExam']
    adj = row['Ajustare_Delay/Bonus']

    if pce < 30:
        tokens[0] = 'low_todo' 
    elif 30 <= pce < 60:
        tokens[0] = 'medium_todo'
    else:
        tokens[0] ='good_todo'


    if spe < 50:
        tokens[1] = 'low_presences'
    elif 50 <= spe < 90:
        tokens[1] = 'medium_presences'
    else:
        tokens[1] = 'good_presences'


    if adj < -1.0:
        tokens[2] = 'low_motivation'
    elif -1.0 < adj <= 1.0:
        tokens[2] = 'medium_motivation'
    else:
        tokens[2] = 'high_motivation'

    return tokens


def run_fd_tokenization(final_data):
    print("\n\n>>> Started data tokenization <<<\n")

    final_data['Document'] = final_data.apply(generate_tokens, axis=1)
    train_set = list(zip(final_data['Document'], final_data['Class']))
    
    to_show = 5
    print(f"Preview {to_show} lines from dataframe with relevant metrics")
    print(train_set[:to_show])

    return train_set