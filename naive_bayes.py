# Probabilitati a Priori P(C)
def aps_pbs(data):
    data_count = len(data)
    passed = sum(1 for _, clasa in data if clasa == 'Promovat')

    p_passed = passed / data_count
    p_failed = 1 - p_passed

    return {'Promovat': p_passed, 'Nepromovat': p_failed}


# P(wi|C) - Laplace Smoothing (flatten 0 probabilities)
# P(wi|C) = (Count(wi, C) + 1) / (Total cuvinte în C + |V|)
def model_learn(train_data):
    classes = {'Promovat': [], 'Nepromovat': []}
    token_set = set()

    for stats_id, cls in train_data:
        classes[cls].extend(stats_id)
        token_set.update(stats_id)

    token_set_size = len(token_set)
    conditioned_probabilities = {}

    for cls, token_list in classes.items():
        total_cls_token = len(token_list)
        token_freq = {}
        
        for token in token_list:
            token_freq[token] = token_freq.get(token, 0) + 1

        conditioned_probabilities[cls] = {}
        for token in token_set:
            token_wi_C = token_freq.get(token, 0)
        # P(wi|C) - Laplace Smoothing (flatten 0 probabilities)
            prob_wi_C = (token_wi_C + 1) / (total_cls_token + token_set_size)
            conditioned_probabilities[cls][token] = prob_wi_C

    return conditioned_probabilities, token_set


import math

def classify_tokens(document, aps_cls, conditioned_probabilities, token_set):
    scores = {}
    nm_smoothing = {}
    token_set_count = len(token_set)

    for cls, prob_dict in conditioned_probabilities.items():
        if prob_dict:
            p_ex = next(iter(prob_dict.values()))
            nm_smoothing[cls] = 1.0 / p_ex
        else:
            nm_smoothing[cls] = token_set_count + 1

    for cls, ap_cls in aps_cls.items():
        log_score = math.log(ap_cls)
        
        for token in document:
            p_wi_C = 0

            if token in conditioned_probabilities[cls]:
                p_wi_C = conditioned_probabilities[cls][token]
            else:
                p_wi_C = 1.0 / (nm_smoothing[cls])
            
            log_score += math.log(p_wi_C)
            
        scores[cls] = log_score
        
    guess_class = max(scores, key=scores.get)

    return guess_class, scores

# Evaluates model
from sklearn.model_selection import train_test_split
def run_naive_bayes(initial_df):
    train_data, test_data = train_test_split(initial_df, test_size=0.2, random_state=42)

    aps = aps_pbs(train_data)
    conditioned_probabilities, token_set = model_learn(train_data)

    correct_predictions = 0

    for document, real_class in test_data:
        guess_class, _ = classify_tokens(   document, \
                                            aps, \
                                            conditioned_probabilities,\
                                            token_set)
        
        if guess_class == real_class:
            correct_predictions += 1

    accuracy = correct_predictions / len(test_data)

    return accuracy