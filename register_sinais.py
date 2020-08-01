from datetime import datetime,timedelta
import time
import pytz as tz
from iqoptionapi.stable_api import IQ_Option
import sys


def timestamp_converter(x):  # Função para converter timestamp
    hora = datetime.strptime(datetime.utcfromtimestamp(
        x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return hora

API = IQ_Option('ra165341@ucdb.br', 'querowinpora')
API.connect()
API.change_balance('PRACTICE')

ajuste_hora = 0
ajuste_minuto = 0


while True:
    if (not API.check_connect()):
        API.connect()
    else:
        print("Conectou")
        break
    time.sleep(5)


def stop(lucro, gain, loss):
    if lucro <= float('-' + str(abs(loss))):
        print('Stop Loss batido!')
        sys.exit()

    if lucro >= float(abs(gain)):
        print('Stop Gain Batido!')
        sys.exit()


def Martingale(valor, payout):
    lucro_esperado = valor * payout
    perca = float(valor)
    while True:
        if round(valor * payout, 2) > round(abs(perca) + lucro_esperado, 2):
            return round(valor, 2)
            break
        valor += 0.01


def Payout(par, tipo, timeframe):
    if tipo == 'b':  # BINARIAS
        a = API.get_all_profit()
        return int(100 * a[par]['binary'])

    elif tipo == 'd':  # DIGITAL
        API.subscribe_strike_list(par, 1)
        while True:
            d = API.get_digital_current_profit(par, 1)
            if d != False:
                d = round(int(d) / 100, 2)
                break
            time.sleep(1)
        API.unsubscribe_strike_list(par, 1)

        return d


#####################################################################################################################
def timestamp_converter(x, retorno=1):
    hora = datetime.strptime(datetime.utcfromtimestamp(
        x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6] if retorno == 1 else hora.astimezone(
        tz.gettz('America/Sao Paulo'))


#####################################################################################################################


def horario():
    # hora = datetime.now()
    hora = datetime.now()-timedelta(hours=ajuste_hora, minutes=ajuste_minuto)
    hora = hora.strftime('%H:%M:%S')
    return hora


def carregar_sinais():
    arquivo = open('sinais.txt', encoding='UTF-8')
    lista = arquivo.read()
    arquivo.close

    lista = lista.split('\n')

    for index, a in enumerate(lista):
        if a == '':
            del lista[index]

    return lista


hora = horario()
lista = carregar_sinais()

#: funcao que realiza o trade
entrou = 0


def realizarTrade(par, valor_entrada, dir, timeframe, tipo):
    print('\n')
    # === CONFIG BOT =====================
    payout = Payout(par, tipo, timeframe)
    lucro = 0  # nao ALTERAR
    # COLOQUE AQUI A QUANTIDADE DE GALES  !=! BORA QUEBRAR ESSA BANCA ...
    martingale = 1
    martingale += 1  # nao ALTERAR

    stop_loss = 10  # STOP LOSS == COLOQUE AQUI O VALOR MAXIMO DE PERCA
    stop_gain = 10000  # STOP WIN == COLOQUE AQUI O VALOR MAXIMO DE GANHOS
    # ===================================

    # - TRADING NAS BINARIAS
    if tipo == "b":
        for i in range(martingale):
            status, id = API.buy(valor_entrada, par, dir, timeframe)
            ordem_op = id

            if status:
                if dir == "call":
                    os_dir = 'COMPRA'
                    print('   # Operacao Binaria iniciada: \n   Ordem =>', ordem_op, '\n   Par =>', par,
                          '\n   Valor do Trading =>  R$ ', float(valor_entrada), ' \n   Direcao => COMPRA  \n')
                if dir == "put":
                    os_dir = 'VENDA'
                    print('   # Operacao Binaria iniciada: \n   Ordem =>', ordem_op, '\n   Par =>', par,
                          '\n   Valor do Trading =>  R$ ', float(valor_entrada), ' \n   Direcao => VENDA  \n')

                while True:
                    valor = API.check_win_v3(id)
                    status = API.api.result

                    if status:
                        valor = valor if valor > 0 else float(
                            '-' + str(abs(valor_entrada)))
                        lucro += round(valor, 2)

                        print('   # Resultado da operacao Binaria: \n   Par =>', par,
                              '\n   Direcao =>', os_dir, ' \n   Status da Operacao: ', end='')

                        print('WIN /' if valor > 0 else 'LOSS /', round(valor, 2), '/',
                              round(lucro, 2), ('/ ' + str(i) + ' GALE' if i > 0 else ''))
                        print('\n   ============================')

                        # valor_entrada = Martingale(valor_entrada, payout)
                        valor_entrada = valor_entrada * 2
                        stop(lucro, stop_gain, stop_loss)

                        break
                if valor > 0:
                    break
            else:
                print('\n   ERRO AO REALIZAR OPERAcaO\n\n')

    # - TRADING NAS DIGITAIS
    if tipo == "d":
        for i in range(martingale):
            status, id = API.buy_digital_spot(
                par, valor_entrada, dir, timeframe)
            ordem_op = id

            if status:
                if dir == "call":
                    os_dir = 'COMPRA'
                    print('   # Operacao Digital iniciada: \n   Ordem =>', ordem_op, '\n   Par =>', par,
                          '\n   Valor do Trading =>  R$ ', float(valor_entrada), ' \n   Direcao => COMPRA  \n')
                if dir == "put":
                    os_dir = 'VENDA'
                    print('   # Operacao Digital iniciada: \n   Ordem =>', ordem_op, '\n   Par =>', par,
                          '\n   Valor do Trading =>  R$ ', float(valor_entrada), ' \n   Direcao => VENDA  \n')
                time.sleep(2)
                while True:
                    status, valor = API.check_win_digital_v2(id)

                    if status:
                        valor = valor if valor > 0 else float(
                            '-' + str(abs(valor_entrada)))
                        lucro += round(valor, 2)

                        print('   # Resultado da operacao Digital: \n   Par =>', par,
                              '\n   Direcao =>', os_dir, ' \n   Status da Operacao: ', end='')

                        print('WIN /' if valor > 0 else 'LOSS /', round(valor, 2), '/',
                              round(lucro, 2), ('/ ' + str(i) + ' GALE' if i > 0 else ''))
                        print('\n   ============================')
                        valor_entrada = Martingale(valor_entrada, payout)

                        stop(lucro, stop_gain, stop_loss)

                        break
                if valor > 0:
                    break
            else:
                print('\n RRO AO REALIZAR OPERAcaO\n\n')

while True:
    for sinal in lista:
        dados = sinal.split(',')
        data = dados[0]  # -> ARMAZENA DATA
        hora = dados[1]  # -> ARMAZENA HORA
        par = str(dados[2])  # -> ARMAZENA O PAR
        timeframe = int(dados[3])  # -> ARMAZENA O TIMEFRAME
        dirx = dados[4]  # -> ARMAZENA A DIREcaO (CALL OU PUT)
        valor_entrada = float(dados[5])  # -> ARMAZENA O VALOR DA ENTRADA
        agora = horario()
        data_atual = datetime.now().date().strftime('%d/%m/%y')

        tipo_op = dados[6]
        if data >= data_atual:
            entrou = 1
            hora_atual = agora
            dir = dirx.lower()
            tipo = tipo_op.lower()
            print(hora_atual)
            print(dados[1])

            if hora_atual == dados[1]:
                realizarTrade(par, valor_entrada, dir, timeframe, tipo)
            if entrou == 0:
                print('nao foi possível executar a operacao!')
