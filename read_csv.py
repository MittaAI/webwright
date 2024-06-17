import csv

# Path to the CSV file
csv_file_path = 'bbc_news_articles.csv'

# Read and print the contents of the CSV file
with open(csv_file_path, 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        print(row)

print('CSV file content printed successfully.')