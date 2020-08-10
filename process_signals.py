import csv
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta
from pytz import timezone
import time
import sys
import logging
import json
import numpy as np
import pandas as pd


class Metrics:
    def __init__(self):
        super().__init__()

    def metric_SMA(self, API, name_active="EURUSD", candle_size=60, period=21, time=time.time()):
        candles = API.get_candles(name_active, candle_size, period, time)
        candles_value = []
        for c in candles:
            candles_value.append(float(c['open']))
        return round(self.moving_average(candles_value, period)[-1], 5)

    def moving_average(self, values, window):
        weigths = np.repeat(1.0, window) / window
        smas = np.convolve(values, weigths, 'valid')
        return smas


class Bot(Metrics):
    def __init__(self, path_config='config.json', path_signals="signals.csv", path_report="report.csv"):
        super().__init__()
        self.logger = self.log()
        self.config = self.read_the_config_file(path_config)
        self.API = IQ_Option(self.config['email'], self.config['password'])
        self.path_signals = path_signals
        self.path_report = path_report
        self.profit = 0
        self.signals = None
        self.balance = None
        self.stop_gain = None
        self.stop_loss = None
        self.max_martingale = None
        self.martingale = None
        self.wallet = None
        self.signals = None
        self.report = None

    def log(self):
        FMT = '%(levelname)s - %(asctime)s - MSG: %(message)s'
        logging.basicConfig(format=FMT, filename='process.log', datefmt='%m/%d/%Y %I:%M:%S %p')
        logger = logging.getLogger('bot')
        logger.setLevel(logging.INFO)
        return logger

    def read_the_config_file(self, path_config='config.json'):
        with open(path_config, 'r') as json_file:
            config = json.load(json_file)
        return config

    def stop(self):
        if self.profit <= float('-' + str(abs(self.stop_loss))):
            self.logger.info('Stop Loss')
            sys.exit()

        if self.profit >= float(abs(self.stop_gain)):
            self.logger.info('Stop Gain')
            sys.exit()

    def connect(self):
        self.API.connect()
        while True:
            while not self.API.check_connect():
                self.API.connect()
                self.logger.warning("Retry connection in 5 seconds")
                time.sleep(5)
            self.logger.info('Connected')
            self.set_config_porcess()
            self.signals = self.load_signals()
            break

    def set_config_porcess(self):
        self.balance = self.API.get_profile_ansyc()['balance']
        self.wallet = self.balance
        self.stop_loss = self.wallet * self.config['pct_stop_loss']
        self.stop_gain = self.wallet * self.config['pct_stop_gain']
        self.max_martingale = self.config['max_martingale']
        self.martingale = self.config['martingale']
        self.API.change_balance(self.config['balance_mode'])
        self.report = pd.DataFrame(
            columns=['trading_instrument', 'name_active', 'order_value', 'call_or_put', 'profit', 'martingale',
                     'count_martingale',
                     'time_order', 'time_exp'])

    def load_signals(self):
        self.logger.info('Load signals')
        with open(self.path_signals, newline='') as csvfile:
            reader = csv.reader(csvfile)
            data = [list(row) for row in reader]
        self.signals = data
        return data

    def horary(self):
        return datetime.now(self.get_iq_timezone())

    def get_iq_timezone(self):
        return timezone(self.API.get_profile_ansyc()['tz'])

    def is_valid_order(self, FMT, time_now, signal_hour, candle_size, name_active):
        is_valid_datetime = datetime.strptime(time_now.strftime(FMT), FMT) < datetime.strptime(signal_hour, FMT)
        if is_valid_datetime:
            is_valid_SMA = self.is_valid_value_SMA(candle_size, name_active, time_now)
            self.logger.info("valid SMA: {} - valid datetime: True".format(is_valid_SMA))
            return is_valid_SMA
        return False

    def is_valid_value_SMA(self, candle_size, name_active, time_now):
        current_candle = self.API.get_candles(name_active, candle_size, 1, time_now.timestamp())
        candle_open_value = round(current_candle[0]['open'], 5)
        sma_value = self.metric_SMA(self.API, name_active, candle_size)
        return candle_open_value >= sma_value

    def execute_signal(self, signal_data, time_now):
        name_active = str(signal_data[1])
        expiration_time = int(signal_data[2])
        call_or_put = signal_data[3].lower()
        signal_value = round(self.wallet * self.config['pct_wallet'], 2)
        operation_type = signal_data[4].lower()
        self.run_trader(name_active, signal_value, call_or_put, expiration_time, operation_type, time_now)

    def run_trader(self, name_active, order_value, call_or_put, exp_timer, operation_type, time_now):
        if operation_type == "b":
            self.trading_binary(call_or_put, name_active, exp_timer, order_value, time_now, 0)
        elif operation_type == "d":
            self.trading_digitals(call_or_put, name_active, exp_timer, order_value, time_now)

    def trading_digitals(self, call_or_put, name_active, exp_timer, order_value, time_now, count_martingale,
                         martingale=False):
        status, order_id = self.API.buy(order_value, name_active, call_or_put, exp_timer)
        self.logger.info("Buy order id: {} status: {}".format(order_id, status))
        order_profit = round(self.API.check_win_digital_v2(order_id), 2)
        self.profit += order_profit
        self.add_order_to_the_report('digitals', call_or_put, exp_timer, name_active, order_value, time_now, martingale,
                                     count_martingale)
        if order_profit < 0 and self.martingale and self.max_martingale > count_martingale:
            self.stop()
            self.logger.info("Order id:{} Loss: {}".format(order_id, order_profit))
            self.logger.info("Current profit: {}".format(self.profit))
            self.logger.info('Executing martingale')
            order_value = round(order_value * 2, 2)
            count_martingale += 1
            self.trading_binary(call_or_put, name_active, exp_timer, order_value, time_now, count_martingale,
                                True)
        else:
            self.logger.info(
                "Profit order id: {}  order_profit: {} current profit: {}".format(order_id, order_profit,
                                                                                  round(self.profit, 2)))
        return call_or_put, name_active, exp_timer, order_value

    def trading_binary(self, call_or_put, name_active, exp_timer, order_value, time_now, count_martingale,
                       martingale=False):
        status, order_id = self.API.buy(order_value, name_active, call_or_put, exp_timer)
        self.logger.info("Buy order id: {} status: {}".format(order_id, status))
        order_profit = round(self.API.check_win_v3(order_id), 2)
        self.profit += order_profit
        self.add_order_to_the_report('binary', call_or_put, exp_timer, name_active, order_value, time_now, martingale,
                                     count_martingale)
        if order_profit < 0 and self.martingale and self.max_martingale > count_martingale:
            self.stop()
            self.logger.info("Order id:{} Loss: {}".format(order_id, order_profit))
            self.logger.info("Current profit: {}".format(self.profit))
            self.logger.info('Executing martingale')
            order_value = round(order_value * 2, 2)
            count_martingale += 1
            self.trading_binary(call_or_put, name_active, exp_timer, order_value, time_now, count_martingale,
                                True)
        else:
            self.logger.info(
                "Profit order id: {}  order_profit: {} current profit: {}".format(order_id, order_profit,
                                                                                  round(self.profit, 2)))
        return call_or_put, name_active, exp_timer, order_value

    def add_order_to_the_report(self, trading_instrument, call_or_put, exp_timer, name_active, order_value, time_now,
                                martingale,
                                count_martingale):
        time_order = time_now - timedelta(minutes=exp_timer)
        self.report.loc[len(self.report) + 1] = [trading_instrument, name_active, order_value, call_or_put,
                                                 round(self.profit, 2), martingale, count_martingale, time_order,
                                                 time_now]

    def process(self):
        FMT = '%H:%M:%S'
        while len(self.signals) > 0:
            time_now = self.horary()
            signal_data = self.signals[0]
            candle_size = int(signal_data[2]) * 60
            name_active = str(signal_data[1])
            signal_hour = signal_data[0]
            if self.is_valid_order(FMT, time_now, signal_hour, candle_size, name_active):
                wait_time = datetime.strptime(signal_hour, FMT) - datetime.strptime(time_now.strftime(FMT), FMT)
                self.logger.info('Running signal: {}'.format(signal_data))
                time.sleep(wait_time.seconds - 1)
                self.signals.remove(signal_data)
                self.execute_signal(signal_data, time_now)
        self.report.to_csv(self.path_report, index=False)


if __name__ == '__main__':
    bot = Bot(path_signals="sinais.csv")
    bot.connect()
    bot.process()
