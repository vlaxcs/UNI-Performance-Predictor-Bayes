from dbconfig import run_db_setup
from dataconfig import run_db_seed
from classification import run_db_classification
from tokenization import run_fd_tokenization
from naive_bayes import run_naive_bayes

if __name__ == "__main__":
    # Local database table-only configuration
    run_db_setup()

    # Database table seeding with random data (read documentation for data generation rules)
    run_db_seed()
    
    # Processes the data, calculates relevant scores and classifies the data in ['Promovat/Nepromovat'] 
    final_data = run_db_classification()

    # Transforms scores into specific and comprehensive tokens
    train_data = run_fd_tokenization(final_data) 

    # Naive Bayes model evaluation
    accuracy = run_naive_bayes(train_data)

    print(f"Model's accuracy: {accuracy * 100:.2f}%")