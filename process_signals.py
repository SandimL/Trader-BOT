from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta
import time
import sys
import os


def stop(profit, gain, loss):
    if profit <= float('-' + str(abs(loss))):
        print('Stop Loss')
        sys.exit()

    if profit >= float(abs(gain)):
        print('Stop Gain')
        sys.exit()

# def configure_timezone():
#     os.environ['TZ'] = 'Europe/London'

def load_signals():
    file = open('sinais.txt', encoding='UTF-8')
    signals = file.read()
    file.close

    signals = signals.split('\n')

    for index, a in enumerate(signals):
        if a == '':
            del signals[index]
    return signals


def run_trader(name_active, order_value, call_or_put, exp_timer, operation_type):
    profit = 0
    if operation_type == "b":
        trading_binary(call_or_put, profit, name_active, exp_timer, order_value)
    if operation_type == "d":
        trading_digitals(call_or_put, profit, name_active, exp_timer, order_value)


def trading_digitals(call_or_put, profit, name_active, exp_timer, order_value):
    for id_martingale in range(max_martingale + 1):
        status, ordem_id = API.buy_digital_spot(
            name_active, order_value, call_or_put, exp_timer)
        if status:
            while True:
                status, order_profit = API.check_win_digital_v2(ordem_id)
                if status:
                    profit += round(order_profit, 2)
                    logging(call_or_put, id_martingale, order_value, profit, name_active, ordem_id, order_profit)
                    order_value = order_value * 2
                    stop(profit, stop_gain, stop_loss)
                    break
            if order_profit > 0:
                break
        else:
            print('\n\nError placing order\n\n')


def trading_binary(call_or_put, profit, name_active, exp_timer, order_value):
    for id_martingale in range(max_martingale + 1):

        status, ordem_id = API.buy(order_value, name_active, call_or_put, exp_timer)

        if status:
            while True:
                order_profit = API.check_win_v3(ordem_id)
                status = API.api.result
                if status:
                    profit += round(order_profit, 2)
                    logging(call_or_put, id_martingale, order_value, profit, name_active, ordem_id,
                            order_profit)
                    order_value = order_value * 2
                    stop(profit, stop_gain, stop_loss)
                    break
            if order_profit > 0:
                break
        else:
            print('\n\nError placing order\n\n')
    return profit, call_or_put, order_value


def logging(call_or_put, id_martingale, order_value, lucro, name_active, ordem_op, order_profit):
    print('# Operation: \n   order =>', ordem_op, '\n   Actives =>', name_active,
          '\n   Trading Value =>  R$ ', float(order_value), ' \n   call_or_put => ', call_or_put, '\n')
    print('   # Resultado da operacao : \n   Atives =>', name_active,
          '\n   call_or_put =>', call_or_put, ' \n   Status: ', end='')
    print('WIN /' if order_profit > 0 else 'LOSS /', round(order_profit, 2), '/',
          round(lucro, 2), ('/ ' + str(id_martingale) + ' GALE' if id_martingale > 0 else ''))
    print('\n   ============================')


def date_now():
    return datetime.now().date().strftime('%d/%m/%y')


def horary():
    hour = datetime.now() - timedelta(hours=ajuste_hora, minutes=ajuste_minuto)
    hour = hour.strftime('%H:%M:%S')
    return hour


def conect():
    while True:
        if (not API.check_connect()):
            API.connect()
        else:
            print("connecting")
            break
        time.sleep(5)


def process(signals):
    FMT = '%H:%M:%S'
    for signal in signals:
        signal_data = signal.split(',')
        signal_hour = signal_data[0]
        time_now = horary()

        if(datetime.strptime(time_now, FMT) < datetime.strptime(signal_hour, FMT)):
            wait_time = datetime.strptime(signal_hour, FMT) - datetime.strptime(time_now, FMT)
            time.sleep(wait_time.seconds - 1)
            execute_signal(signal)


def execute_signal(signal):
    signal_data = signal.split(',')
    name_active = str(signal_data[1])
    expiration_time = int(signal_data[2])
    call_or_put = signal_data[3].lower()
    signal_value = float(signal_data[4])
    operation_type = signal_data[5].lower()
    run_trader(name_active, signal_value, call_or_put, expiration_time, operation_type)


if __name__ == '__main__':
    API = IQ_Option('ra165341@ucdb.br', 'querowinpora')
    API.connect()
    balance_mode = ['REAL', 'PRACTICE']
    API.change_balance(balance_mode[1])

    ajuste_hora = 0
    ajuste_minuto = 0
    max_martingale = 1

    stop_loss = 10
    stop_gain = 10000

    conect()
    signals = load_signals()
    process(signals)
