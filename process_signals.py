from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from pytz import timezone
import time
import sys
import os
import logging

FMT = '%(levelname)s - %(asctime)s - MSG: %(message)s'
logging.basicConfig(format=FMT, filename='process.log', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('api')
logger.setLevel(logging.INFO)

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que conecta a API do IQ Option.
Executa o laço até a conexão com a API.
"""


def connect():
    while (not API.check_connect()):
        API.connect()
        logger.warning("Retry connection in 5 seconds")
        time.sleep(5)

    logger.info("Connected")


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

    file = open('sinais.txt', encoding='UTF-8')

    # Lê o arquivo
    signals = file.read()
    file.close

    # Separa os sinais pelo "Enter"
    signals = signals.split('\n')

    # Limpa a lista de sinais, retirando os vazios
    for index, value in enumerate(signals):
        if value == '':
            del signals[index]
    return signals


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que processa a lista de sinais, invocando a função de execução.
Recebe como parâmetro a lista de sinais, lida pela @method load_signals()

@param signals lista de sinais lidos
"""


def process(signals):
    FMT = '%H:%M:%S'
    for signal in signals:
        signal_data = signal.split(',')
        signal_hour = signal_data[0]
        time_now = horary()

        if (datetime.strptime(time_now, FMT) < datetime.strptime(signal_hour, FMT)):
            wait_time = datetime.strptime(signal_hour, FMT) - datetime.strptime(time_now, FMT)
            time.sleep(wait_time.seconds - 1)
            logger.info('Running signal: [{}]'.format(signal))
            execute_signal(signal)


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Executa o sinal.

@param signal sinal a ser executado.
"""


def execute_signal(signal):
    signal_data = signal.split(',')
    name_active = str(signal_data[1])
    expiration_time = int(signal_data[2])
    call_or_put = signal_data[3].lower()
    signal_value = float(signal_data[4])
    operation_type = signal_data[5].lower()
    run_trader(name_active, signal_value, call_or_put, expiration_time, operation_type)


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
                                                                                            profit))
                break
            logger.info("Order id:{} Loss: {}".format(ordem_id, order_profit))
            logger.info("Current profit: {}".format(profit))
            logger.info('Executing GATE')
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
                                                                                            profit))
                break
            logger.info("Order id:{} Loss: {}".format(ordem_id, order_profit))
            logger.info("Current profit: {}".format(profit))
            logger.info('Executing GATE')
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
    hour = hour.strftime('%H:%M:%S')
    return hour


def connect():
    API.connect()
    while True:
        while not API.check_connect():
            API.connect()
            logger.info('connecting')
            time.sleep(5)

        logger.info('Connected')
        balance_mode = ['REAL', 'PRACTICE']
        API.change_balance(balance_mode[1])
        signals = load_signals()
        process(signals)
        break


def execute_signal(signal):
    signal_data = signal.split(',')
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

if __name__ == '__main__':
    API = IQ_Option('ra165341@ucdb.br', 'querowinpora')
    max_martingale = 1
    stop_loss = 10
    stop_gain = 10000
    connect()
