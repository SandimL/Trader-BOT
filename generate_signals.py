import csv
import random
from datetime import datetime, timedelta


def create_filetxt(file, active):
    time = datetime.now() - timedelta(0, 0)
    hour = int(time.strftime('%H'))
    minute = int(time.strftime('%M'))
    while hour <= 22:
        for i in range(19):
            minute += 3
            if minute >= 57:
                hour += 1
                minute = 0
            value = 3.55
            call_or_put = random.choices(["call", "put"])
            file.write(
                "{:0>2}:{:0>2}:00,{},1,{},{},b\n".format(hour, minute, active, call_or_put[0], value))
    file.close()


def create_filecsv(active):
    with open('sinais.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        time = datetime.now() - timedelta(0, 0)
        hour = int(time.strftime('%H'))
        minute = int(time.strftime('%M'))
        while hour <= 22:
            for i in range(19):
                minute += 3
                if minute >= 57:
                    hour += 1
                    minute = 0
                call_or_put = random.choices(["call", "put"])
                spamwriter.writerow(["{:0>2}:{:0>2}:00".format(hour, minute), active, 1, call_or_put[0], "binary"])


if __name__ == '__main__':
    create_filecsv("EURUSD")
