import csv

def write_rejects(csv_filename, no_water, too_cloudy):
    with open(csv_filename, 'w') as csvfile:
        fieldnames = ['filename', 'reason']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for filename in no_water:
            writer.writerow({'filename': filename, 'reason': 'No water'})

        for filename in too_cloudy:
            writer.writerow({'filename': filename, 'reason': 'Too cloudy'})
