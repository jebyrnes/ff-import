import csv

def write_rejects(csv_filename, rejects):
    if not rejects and len(rejects) > 0:
        return

    with open(csv_filename, 'w') as csvfile:

        fieldnames = ['filename', 'reason', 'row', 'column']
        for key in sorted(rejects[0].keys()):
            if not key in fieldnames:
                fieldnames.append(key)

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for reject in rejects:
            writer.writerow(reject)
