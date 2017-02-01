import csv

def write_rejects(csv_filename, rejects):
    with open(csv_filename, 'w') as csvfile:
        fieldnames = ['filename', 'reason', 'row', 'column']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for reject in rejects:
            writer.writerow(reject)
