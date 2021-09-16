#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Ivanyuk DY 16/09/21
  Список акций
  На компе создается табличка excel в которую вносятся акции по цене закупа и нижний уровень который нужно мониторить.
  Прога читает табличку и ищет список акций на Yahoo, сравнивает цены и отправляет сообщение по расписанию.
"""
import pandas as pd
import schedule
import time
import matplotlib
from pandas_datareader import data
import datetime
from googlefinance import getQuotes
import json

# Telegram
import emoji
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Парсинг с сайта
import requests
import bs4


# Создаем Job для планирования расписания отправки
def job():
    # Считываем данные в датафрейм из таблички
    Path_book = 'C:\\Users\\Иванюк Дмитрий\\PycharmProjects\\Stock\\Stock_db.xlsx'
    df_stock = pd.read_excel(Path_book, sheet_name='Sheet1')
    print(df_stock)

    # df_stock.loc[df_stock["Stock"] == 'GMKN.ME', 'Price'] = 2000
    # df_stock.to_excel('C:\\Users\\Иванюк Дмитрий\\PycharmProjects\\Stock\\Stock_db.xlsx', index = False)

    # Список акций из таблички
    mystocks = df_stock['Stock'].tolist()
    stockdata = []

    class Stocks(object):
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0(Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
        }

        # Забираем с сайта Yahoo акции
        def getData(self, symbol):
            url = f'https://finance.yahoo.com/quote/{symbol}'
            r = requests.get(url, headers=self.headers)
            soup = bs4.BeautifulSoup(r.text, 'html.parser')
            stock = {
                'name': symbol,
                'price': soup.find('div', {'class': 'D(ib) Mend(20px)'}).findAll('span')[0].text,
                'change': soup.find('div', {'class': 'D(ib) Mend(20px)'}).findAll('span')[1].text
            }
            return stock

    stk = Stocks()

    # Собираем данные с сайта, добавляем цену из таблички
    for item in mystocks:
        stock_dict = stk.getData(item)
        stock_dict['min_price'] = df_stock.loc[df_stock["Stock"] == item, 'Min_Price'].values[0]
        stockdata.append(stock_dict)
        print('Getting: ', item)

    print(stockdata)

    #  Телеграмм
    # Токен бота от Фазербота
    token = "1985457918:AAEHW0Eye-VjDHl9HzTvZHAkeFcU5OUUIa8"
    updater = Updater(token, use_context=True)

    # Отправляем сообщение в чат по chat_id
    def send_stock(Mess):
        updater.bot.sendMessage(chat_id='244813036', text=Mess)

    # Подготовка сообщения перед отправкой в телеграмм
    def prepare_text(text):
        txt = ""
        for itm in text:
            prc = itm.get("price")
            min_prc = itm.get("min_price")
            prc = prc.replace(',', '')
            if float(prc) < float(min_prc):
                emj = emoji.emojize(":red_circle:")
            else:
                emj = emoji.emojize(":green_circle:")
            min_price = "[" + str(itm.get("min_price")) + "]"
            txt += emj + " " + itm.get("name") + "   " + itm.get("price") + " " \
                   + min_price + "   " + "'" + itm.get("change") + "'" + '\n'
        stock_txt = txt
        return str(stock_txt)

    stock_msg = prepare_text(stockdata)
    send_stock(stock_msg)


# Расписание отправки сообщений
schedule.every().day.at("11:00").do(job)
schedule.every().day.at("14:00").do(job)
schedule.every().day.at("18:00").do(job)
schedule.every().day.at("22:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
