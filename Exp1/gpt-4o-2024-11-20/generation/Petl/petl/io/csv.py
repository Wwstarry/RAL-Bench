import csv

def fromcsv(path):
    def table():
        with open(path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                yield row
    return table

def tocsv(table, path):
    with open(path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in table():
            writer.writerow(row)