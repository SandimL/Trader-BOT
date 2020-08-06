import csv
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from pytz import timezone
import time
import sys
import logging
import json
import numpy as np

FMT = '%(levelname)s - %(asctime)s - MSG: %(message)s'
logging.basicConfig(format=FMT, filename='process.log', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('api')
logger.setLevel(logging.INFO)

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que para a execução do bot e apresenta se o BOT perdeu ou ganhou dinheiro.
Utilizada em @method trading_digitals() e @method trading_binary() 

@param profit indica a perda/ganho obtido
@param gain define a taxa de ganho
@param loss define a taxa de perda
"""


def stop(profit, gain, loss):
    # Se o lucro foi menor que a taxa de perda, apresenta que o bot parou na "perda".
    if profit <= float('-' + str(abs(loss))):
        logger.info('Stop Loss')
        sys.exit()

    # Se o lucro foi maior que a taxa de ganha, apresenta que o bot parou no "lucro".
    if profit >= float(abs(gain)):
        logger.info('Stop Gain')
        sys.exit()


def get_iq_timezone():
    return timezone(API.get_profile_ansyc()['tz'])


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que carrega os arquivos de sinais, montando um vetor de sinais.

@return vetor de sinais processados
"""


def load_signals():
    # Carrega o arquivo de sinais
    logger.info('Load signals')

    with open('sinais.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = [list(row) for row in reader]

    return data


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que processa a lista de sinais, invocando a função de execução.
Recebe como parâmetro a lista de sinais, lida pela @method load_signals()

@param signals lista de sinais lidos
"""


def process(signals):
    FMT = '%H:%M:%S'
    for signal_data in signals:
        time_now = horary()
        candle_size = int(signal_data[2]) * 60
        name_active = str(signal_data[1])
        signal_hour = signal_data[0]
        if is_valid_order(FMT, time_now, signal_hour, candle_size, name_active):
            wait_time = datetime.strptime(signal_hour, FMT) - datetime.strptime(time_now.strftime('%H:%M:%S'), FMT)
            time.sleep(wait_time.seconds - 1)
            logger.info('Running signal: {}'.format(signal_data))
            execute_signal(signal_data)


def is_valid_order(FMT, time_now, signal_hour, candle_size, name_active):
    is_valid_datetime = datetime.strptime(time_now.strftime('%H:%M:%S'), FMT) < datetime.strptime(signal_hour, FMT)
    if is_valid_datetime:
        is_valid_SMA = is_valid_value_SMA(candle_size, name_active, time_now)
        logger.info("valid SMA: {} - valid datetime: True".format(is_valid_SMA))
        return is_valid_SMA
    return False


def is_valid_value_SMA(candle_size, name_active, time_now):
    current_candle = API.get_candles(name_active, candle_size, 1, time_now.timestamp())
    candle_open_value = round(current_candle[0]['open'], 5)
    sma_value = metric_SMA(name_active, candle_size) - 1
    return candle_open_value >= sma_value


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que executa a operação, dado seu tipo.
"""


def run_trader(name_active, order_value, call_or_put, exp_timer, operation_type):
    profit = 0
    if operation_type == "b":
        trading_binary(call_or_put, profit, name_active, exp_timer, order_value)
    if operation_type == "d":
        trading_digitals(call_or_put, profit, name_active, exp_timer, order_value)


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que executa o trade digital.
Invocada pela @method run_trader()
"""


def trading_digitals(call_or_put, profit, name_active, exp_timer, order_value):
    for id_martingale in range(max_martingale + 1):
        status, ordem_id = API.buy_digital_spot(
            name_active, order_value, call_or_put, exp_timer)
        logger.info("Buy order id: {} status: {}".format(ordem_id, status))
        if status:
            while True:
                status, order_profit = API.check_win_digital_v2(ordem_id)
                if status:
                    profit += round(order_profit, 2)
                    order_value = order_value * 2
                    break
            if order_profit > 0:
                logger.info(
                    "Profit order id: {}  order_profit: {} current profit: {} - WIN".format(ordem_id, order_profit,
                                                                                            round(profit, 2)))
                break
            logger.info("Order id:{} Loss: {}".format(ordem_id, order_profit))
            logger.info("Current profit: {}".format(profit))
            logger.info('Executing martingale')
            stop(profit, stop_gain, stop_loss)
        else:
            logger.error('Error placing order')


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que executa o trade binário.
Invocada pela @method run_trader()
"""


def trading_binary(call_or_put, profit, name_active, exp_timer, order_value):
    for id_martingale in range(max_martingale + 1):

        status, ordem_id = API.buy(order_value, name_active, call_or_put, exp_timer)
        logger.info("Buy order id: {} status: {}".format(ordem_id, status))

        if status:
            while True:
                order_profit = API.check_win_v3(ordem_id)
                status = API.api.result
                if status:
                    profit += round(order_profit, 2)
                    order_value = order_value * 2
                    break
            if order_profit > 0:
                logger.info(
                    "Profit order id: {}  order_profit: {} current profit: {} - WIN".format(ordem_id, order_profit,
                                                                                            round(profit, 2)))
                break
            logger.info("Order id:{} Loss: {}".format(ordem_id, order_profit))
            logger.info("Current profit: {}".format(profit))
            logger.info('Executing martingale')
            stop(profit, stop_gain, stop_loss)
        else:
            logger.error('Error placing order')
    return profit, call_or_put, order_value


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Pega a data atual no formato d/m/y
"""


def date_now():
    return datetime.now(get_iq_timezone()).date().strftime('%d/%m/%y')


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Pega o horário atual no formato H:M:S
"""


def horary():
    hour = datetime.now(get_iq_timezone())
    return hour


def metric_SMA(name_active="EURUSD", candle_size=60, period=21, time=time.time()):
    candles = API.get_candles(name_active, candle_size, period, time)
    candles_value = []
    for c in candles:
        candles_value.append(float(c['open']))
    return round(movingaverage(candles_value, period)[-1], 5)


def movingaverage(values, window):
    weigths = np.repeat(1.0, window) / window
    smas = np.convolve(values, weigths, 'valid')
    return smas  # as a numpy array


def connect():
    API.connect()
    while True:
        while not API.check_connect():
            API.connect()
            logger.warning("Retry connection in 5 seconds")
            time.sleep(5)

        logger.info('Connected')
        balance_mode = ['REAL', 'PRACTICE']
        API.change_balance(balance_mode[1])
        signals = load_signals()
        process(signals)
        break


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Executa o sinal.

@param signal sinal a ser executado.
"""


def execute_signal(signal_data):
    name_active = str(signal_data[1])
    expiration_time = int(signal_data[2])
    call_or_put = signal_data[3].lower()
    signal_value = float(signal_data[4])
    operation_type = signal_data[5].lower()
    run_trader(name_active, signal_value, call_or_put, expiration_time, operation_type)


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função principal que executa:
    - Conecta com a API através @method connect()
    - Leitura de sinais através @method load_signals()
    - Processa os sinais através @method process()
"""


def get_config(path='config.json'):
    with open(path, 'r') as json_file:
        config = json.load(json_file)
    return config


if __name__ == '__main__':
    config = get_config('./config.json')
    API = IQ_Option(config['email'], config['password'])
    max_martingale = config['max_martingale']
    stop_loss = config['stop_loss']
    stop_gain = config['stop_gain']
    connect()
