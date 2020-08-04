from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta
import time
import sys
import os

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que conecta a API do IQ Option.
Executa o laço até a conexão com a API.
"""
def connect():
    while (not API.check_connect()):
        API.connect()
        print("Connecting")
        time.sleep(5)
        
    print("Connected")

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
        print('Stop Loss')
        sys.exit()

    # Se o lucro foi maior que a taxa de ganha, apresenta que o bot parou no "lucro".
    if profit >= float(abs(gain)):
        print('Stop Gain')
        sys.exit()

# def configure_timezone():
#     os.environ['TZ'] = 'Europe/London'

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que carrega os arquivos de sinais, montando um vetor de sinais.

@return vetor de sinais processados
"""
def load_signals():
    # Carrega o arquivo de sinais
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

        if(datetime.strptime(time_now, FMT) < datetime.strptime(signal_hour, FMT)):
            wait_time = datetime.strptime(signal_hour, FMT) - datetime.strptime(time_now, FMT)
            time.sleep(wait_time.seconds - 1)
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

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que executa o trade binário.
Invocada pela @method run_trader()
"""
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

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função que salva um log a partir do Trade executado.
Utilizada em @method trading_digitals() e @method trading_binary() 
"""
def logging(call_or_put, id_martingale, order_value, lucro, name_active, ordem_op, order_profit):
    print('# Operation: \n   order =>', ordem_op, '\n   Actives =>', name_active,
          '\n   Trading Value =>  R$ ', float(order_value), ' \n   call_or_put => ', call_or_put, '\n')
    print('   # Resultado da operacao : \n   Atives =>', name_active,
          '\n   call_or_put =>', call_or_put, ' \n   Status: ', end='')
    print('WIN /' if order_profit > 0 else 'LOSS /', round(order_profit, 2), '/',
          round(lucro, 2), ('/ ' + str(id_martingale) + ' GALE' if id_martingale > 0 else ''))
    print('\n   ============================')


"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Pega a data atual no formato d/m/y
"""
def date_now():
    return datetime.now().date().strftime('%d/%m/%y')

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Pega o horário atual no formato H:M:S
"""
def horary():
    hour = datetime.now() - timedelta(hours=ajuste_hora, minutes=ajuste_minuto)
    hour = hour.strftime('%H:%M:%S')
    return hour

"""
1ª Documentação - 03/08/2020 - @author Mateus Ragazzi
Função principal que executa:
    - Conecta com a API através @method connect()
    - Leitura de sinais através @method load_signals()
    - Processa os sinais através @method process()
"""
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

    connect()
    signals = load_signals()
    process(signals)
