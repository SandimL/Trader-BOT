import random
from datetime import datetime


def crea_file(hour, minute, file, actives):
    while hour <= 20:
        for i in range(19):
            minute += 3
            if minute >= 57:
                hour += 1
                minute = 0
            value = 1
            call_or_put = random.choices(["call", "put"])
            date = datetime.now().date().strftime('%d/%m/%y')
            file.write(
                "{},{:0>2}:{:0>2}:00,{},1,{},{},b\n".format(date, hour, minute, actives, call_or_put[0], value))
    file.close()


if __name__ == '__main__':
    hour = 13
    minute = 30

    file = open("../sinais.txt", "w")
    crea_file(hour, minute, file, "EURUSD-OTC")
