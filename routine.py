from check_update import check_update
from datetime import datetime
from pymongo import MongoClient
from time import time, sleep

import configparser
import logging
import logging.handlers
import requests
import telebot
import sys

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

#TOKEN = config['RASTREIOBOT']['TOKEN']
# int_check = int(config['RASTREIOBOT']['int_check'])
#LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']
#PATREON = config['RASTREIOBOT']['patreon']
INTERVAL = 0.03

logger_info = logging.getLogger(__file__)
#handler_info = logging.handlers.TimedRotatingFileHandler(LOG_ALERTS_FILE,
#    when='midnight', interval=1, backupCount=5, encoding='utf-8')
#logger_info.addHandler(handler_info)

#bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

def get_package(code):
    stat = check_update(code)
    if stat == 0:
        stat = 'Sistema dos Correios fora do ar.'
    elif stat == 1:
        stat = None
    else:
        cursor = db.rastreiobot.update_one (
        { "code" : code.upper() },
        {
            "$set": {
                "stat" : stat,
                "time" : str(time())
            }
        })
        stat = 10
    return stat

def check_system():
    try:
        URL = ('http://webservice.correios.com.br/')
        response = requests.get(URL, timeout=3)
    except:
        print(str(datetime.now()) + '\tCorreios indisponível')
        return False
    print(str(response))
    if '200' in str(response):
        return True
    else:
        print(str(datetime.now()) + '\tCorreios indisponível')
        return False

if __name__ == '__main__':
    cursor1 = db.rastreiobot.find()
    sent = 1
    if not check_system():
        sys.exit()

    for elem in cursor1:
        try:
            code = elem['code']
            time_dif = int(time() - float(elem['time']))
            try:
                old_state = elem['stat'][len(elem['stat'])-1]
                len_old_state = len(elem['stat'])
            except:
                len_old_state = 1
            if 'objeto entregue ao' in old_state.lower():
                continue
            elif 'objeto apreendido por órgão de fiscalização' in old_state.lower():
                continue
            elif 'objeto devolvido' in old_state.lower():
                continue
            elif 'objeto roubado' in old_state.lower():
                continue
            stat = get_package(code)
            if stat == 0:
                break
            cursor2 = db.rastreiobot.find_one(
            {
                "code": code
            })
            try:
                len_new_state = len(cursor2['stat'])
            except:
                len_new_state = 1
            if len_old_state != len_new_state:
                for user in elem['users']:
                    print(str(datetime.now()) + '\t' + '\t'
                        + str(code) + ' \t' + str(user) + ' \t' + str(sent) + '\t'
                        + ' ' + str(len_old_state) + ' '
                        + str(len_new_state))
                    try:
                        message = (str(u'\U0001F4EE') + '<b>' + code + '</b>\n')
                        if elem[user] != code:
                            message = message + elem[user] + '\n'
                        message = (
                            message + '\n'
                            +  cursor2['stat'][len(cursor2['stat'])-1])
                        if 'objeto entregue' in message.lower():
                            message = (message + '\n\n'
                            + str(u'\U00002B50')
                            + '<a href="https://telegram.me/storebot?start=rastreiobot">'
                            + 'Avalie o bot</a> - '
                            + str(u'\U0001F4B5')
                            + '<a href="http://grf.xyz/paypal">Colabore</a>')
                        # bot.send_message(str(user), message, parse_mode='HTML',
                        #     disable_web_page_preview=True)
                        sent = sent + 1
                    except Exception as e:
                        print(str(datetime.now())
                             + '\tEXCEPT: ' + str(user) + ' ' + code + ' ' + str(e))
                        # bot.send_message(str(user), message, parse_mode='HTML',
                        #     disable_web_page_preview=True)
                        # sent = sent + 1
                        continue
                    #else:
                    #    logger_info.info(str(datetime.now())
                    #         + '\tELSE:\t' + str(user) + ' ' + code)
                    #    continue
                    #sleep(INTERVAL)
        except Exception as e:
            print(str(datetime.now()) + '\t' + '\tEXCEPT: ' + str(e)
                + '\t' + str(code) + ' \t' + str(user))
            sys.exit()
