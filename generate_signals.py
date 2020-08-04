import random
from datetime import datetime, timedelta


def create_file(file, active):
    time = datetime.now() - timedelta(0, 0)
    hour = int(time.strftime('%H'))
    minute = int(time.strftime('%M'))
    while hour <= 20:
        for i in range(19):
            minute += 3
            if minute >= 57:
                hour += 1
                minute = 0
            value = 1
            call_or_put = random.choices(["call", "put"])
            file.write(
                "{:0>2}:{:0>2}:00,{},1,{},{},b\n".format(hour, minute, active, call_or_put[0], value))
    file.close()

if __name__ == '__main__':

    file = open("./sinais.txt", "w")
    create_file(file, "EURUSD")
