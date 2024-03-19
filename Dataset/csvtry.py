import csv

with open('./Dataset/Records.csv', mode='r') as file:
    csvFile = csv.DictReader(file)
    for row in csvFile:
        deposits = row['Deposits']
        withdrawals = row['Withdrawls']


        if deposits != '00.00':
            print("Credit: {deposits}")
        
        if withdrawals != '00.00':
            print("Debit: {withdrawals}")
            print(float(row['Withdrawls']))
            print(type(row['Withdrawls']))