import csv

with open('./Dataset/Records.csv', mode='r') as file:
    csvFile = csv.reader(file)
    for lines in csvFile:
        if lines[2] != 0.0:
            print('debit')
        elif lines[3] != 0:
            print('credit')