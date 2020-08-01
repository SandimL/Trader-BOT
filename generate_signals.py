import random

hora = 17
minuto = 30

while hora <= 20:
    for i in range(19):
        minuto += 3
        if minuto >= 57:
            hora += 1
            minuto = 0
        valor = 1
        compra_ou_venda = random.choices(["call", "put"])
        print("01/08/2020,{:0>2}:{:0>2}:00,EURUSD-OTC,1,{},{},b".format(hora, minuto, compra_ou_venda[0], valor))
