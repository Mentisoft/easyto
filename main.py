#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

# Google Sheets
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# SQL
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

# Telegram
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          RegexHandler, ConversationHandler)

# Etc
import time
import logging
import os.path
from flask import Flask

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1IC8VyWS2VLZGrhKJC4lIHwtDeoQWD_ZeEMUHrlb9dp8'
SAMPLE_RANGE_NAME = 'Запись!A2:L1000'
    
# Enable logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)



# Keyboards
KEYBOARD_START = [['Старт']]
KEYBOARD_BACK_STOP = [['\u2b05 Назад', '\u274c Стоп']]
KEYBOARD_MAIN = [['\u260e Контакты', '\u274c Стоп'],['Записаться на ТО'],
                          ['Рассчитать стоимость ТО'],['Проверить статус заявки']]
KEYBOARD_BOOK = [['Выбрать дату и время'],['Показать все записи']]
KEYBOARD_SKIP = [['Пропустить']]
KEYBOARD_PLATE = [['Найти авто по госномеру']]
KEYBOARD_CONFIRM = [['Подтвердить запись']]
KEYBOARD_CONTINUE = [['Продолжить']]
KEYBOARD_AUTO = [['Указать авто вручную']]
KEYBOARD_CHANGE = [['Изменить данные']]

# MSGs
MSG_START = 'Привет! Я помогу вам записаться на ТО, рассчитать стоимость ' \
            'или уточнить статус заявки.\n\n' \
            'Нажмите Старт для начала работы.'
MSG_STOP =  'Работа приостановлена. Возвращайтесь!'
MSG_MAIN =  'Выберите желаемое действие.'
MSG_BOOK =  'Выберите свободный слот.'
MSG_DATE =  'Выберите дату.'
MSG_TIME =  'Выберите время.'
MSG_MODEL = 'Веберите модель вашего автомобиля.'
MSG_ENG =   'Укажите двигатель.'
MSG_TO =    'Укажите ТО или введите текущий пробег автомобиля.'
MSG_COMM =  'Укажите дополнительные комментарии.'
MSG_PLATE = 'Введите номерной знак.'
MSG_NOT_FOUND = 'Машина не найдена, попробуйте другой номер.'
MSG_NOT_READY = 'Это пока не готово :)'
MSG_PHONE = 'Введите ваш контактный номер телефона.'

# Main
app = Flask(__name__)

# Responses
(START_ACTION, MAIN_MENU_ACTION, BOOK_MENU_ACTION, PRICE_MENU_ACTION,
 STATUS_MENU_ACTION, TYPING_REPLY, TYPING_CHOICE, BOOK_DATE_ACTION, BOOK_TIME_ACTION,
 BOOK_AUTO_ACTION, BOOK_REG_ACTION, BOOK_TO_ACTION, BOOK_COMMENTS_ACTION,
 BOOK_CONFIRM_ACTION, BOOK_PHONE_ACTION, BOOK_ENGINE_ACTION, CARPLATE_DB_ACTION,
 CARPLATE_DB_ACTION_SUCCESS, BOOK_CHANGE_ACTION, PRICE_AUTO_ACTION, PRICE_ENGINE_ACTION,
 PRICE_TO_ACTION, PRICE_CONFIRM_ACTION, PRICE_DATE_ACTION, PRICE_TIME_ACTION,
 PRICE_COMMENTS_ACTION, PRICE_PHONE_ACTION, CHANGE_ACTION,
 CARPLATE_DB_ACTION_PRICE, GET_STATUS_ACTION, POST_STATUS_ACTION) = range(31)


def get_reply_markup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True):
    reply_markup = ReplyKeyboardMarkup(reply_keyboard,
        one_time_keyboard=True, resize_keyboard=True)
    return reply_markup

def send_log_msg(update):
    user = update.message.from_user
    logger.info("Action by %s: %s", user.full_name, update.message.text)
    
def start(update, context):
    send_log_msg(update)
    reply_msg = MSG_START
    reply_markup = get_reply_markup(KEYBOARD_START)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return START_ACTION

def stop(update, context):
    send_log_msg(update)
    reply_msg = MSG_STOP
    reply_markup = get_reply_markup(KEYBOARD_START)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return START_ACTION

def clear_user_data(context, key='all'):
    data_keys = ['date','time','auto','engine','to','comments','phone','fullname']
    if key == 'all':
        for k in list(context.user_data):
            context.user_data.pop(k, None)
    else:
        context.user_data.pop(key, None)

def main_menu(update, context):
    send_log_msg(update)
    reply_msg = MSG_MAIN
    reply_markup = get_reply_markup(KEYBOARD_MAIN)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    clear_user_data(context)
    return MAIN_MENU_ACTION

def book(update, context):
    send_log_msg(update)
    reply_msg = MSG_BOOK
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_BOOK)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_MENU_ACTION

def book_date(update, context):
    send_log_msg(update)
    user = update.message.from_user
    context.user_data['fullname'] = user.full_name
    reply_msg = 'Загрузка данных...'
    update.message.reply_text(reply_msg)
    dates = read_records('dates')
    keyboard = generate_buttons(dates)
    reply_msg = MSG_DATE
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)   
    return BOOK_DATE_ACTION

def book_time(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['date'] = text
    dateslot = context.user_data['date'].split()
    date = dateslot[1]
    reply_msg = 'Загрузка данных...'
    update.message.reply_text(reply_msg)
    times = read_records('times', date)
    keyboard = generate_buttons(times)
    reply_msg = MSG_TIME
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_TIME_ACTION

def price_date(update, context):
    send_log_msg(update)
    user = update.message.from_user
    context.user_data['fullname'] = user.full_name
    reply_msg = 'Загрузка данных...'
    update.message.reply_text(reply_msg)
    dates = read_records('dates')
    keyboard = generate_buttons(dates)
    reply_msg = MSG_DATE
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)   
    return PRICE_DATE_ACTION

def price_time(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['date'] = text
    dateslot = context.user_data['date'].split()
    date = dateslot[1]
    reply_msg = 'Загрузка данных...'
    update.message.reply_text(reply_msg)
    times = read_records('times', date)
    keyboard = generate_buttons(times)
    reply_msg = MSG_TIME
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return PRICE_TIME_ACTION

def book_auto(update, context):
    send_log_msg(update)
    text = update.message.text
    if text not in ('Выберите желаемое действие','Выберите авто вручную', '\u2b05 Назад'):
        context.user_data['time'] = text
    keyboard = generate_buttons(read_cars())
    reply_msg = MSG_MODEL
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_PLATE + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_AUTO_ACTION

def book_engine(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['auto'] = text
    keyboard = generate_buttons(read_engines(context.user_data['auto']))
    reply_msg = MSG_ENG
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_ENGINE_ACTION

def book_to(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != 'Продолжить' and text!= '\u2b05 Назад':
        context.user_data['engine'] = text
    keyboard = generate_buttons(read_tos())
    reply_msg = MSG_TO
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_TO_ACTION

def book_comments(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['to'] = text
    reply_msg = MSG_COMM
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_SKIP)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_COMMENTS_ACTION

def price_comments(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['time'] = text
    reply_msg = MSG_COMM
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_SKIP)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return PRICE_COMMENTS_ACTION

# ---

def price_auto(update, context):
    send_log_msg(update)
    text = update.message.text
    if text not in ('Выберите авто вручную', '\u2b05 Назад'):
        context.user_data['time'] = text
    keyboard = generate_buttons(read_cars())
    reply_msg = MSG_MODEL
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_PLATE + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return PRICE_AUTO_ACTION

def price_engine(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['auto'] = text
    keyboard = generate_buttons(read_engines(context.user_data['auto']))
    reply_msg = MSG_ENG
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return PRICE_ENGINE_ACTION

def price_to(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != 'Продолжить' and text!= '\u2b05 Назад':
        context.user_data['engine'] = text
    keyboard = generate_buttons(read_tos())
    reply_msg = MSG_TO
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return PRICE_TO_ACTION

def price_confirm(update, context):
    send_log_msg(update)
    text = update.message.text
    context.user_data['to'] = text
    reply_msg = get_confirm_msg(update, context)
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + [['Записаться на ТО']] + [['В главное меню']])
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return PRICE_CONFIRM_ACTION

def book_phone(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['comments'] = text
    reply_msg = MSG_PHONE
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_SKIP)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_PHONE_ACTION

def price_phone(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != '\u2b05 Назад':
        context.user_data['comments'] = text
    reply_msg = MSG_PHONE
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_SKIP)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return PRICE_PHONE_ACTION

def get_confirm_msg(update, context):
    user = update.message.from_user

    # generate jobs and price - to be excluded from this function

    model = context.user_data['auto'].replace('Audi ','')
    engine = context.user_data['engine']
    milage = context.user_data['to'].replace(' тыс.','')

##    get_car_details_db_clean


    jobs = read_tos2(model, engine, milage)
    jobs_str = '\n'
    i=1
    to_price = ''
    for job in jobs:
        jobs_str += '\n' + str(i) + '. ' + job[1]
        to_price = job[2].replace('\n','')
        i += 1

##    reply_keyboard = [['\u2b05 Назад', '\u274c Стоп'],['Подтвердить запись'],['Изменить данные']]
    print(context.user_data)
    try:  
        text = 'Отлично! Проверьте пожалуйста данные:\n\n' \
               + ' - Имя: ' + context.user_data['fullname'] + '\n' \
               + ' - Дата: ' + context.user_data['date'] + '\n' \
               + ' - Время: ' + context.user_data['time'] + '\n' \
               + ' - Автомобиль: ' + context.user_data['auto'] + '\n' \
               + ' - Двигатель: ' + context.user_data['engine'] + '\n' \
               + ' - ТО: ' + context.user_data['to'] + '\n' \
               + ' - Комментарии: ' + context.user_data['comments'] + '\n' \
               + ' - Номер телефона: ' + context.user_data['phone'] + '\n' \
               + '\n' + 'Список работ: ' + jobs_str + '\n' \
               + '\n' + 'Cтоимость ТО - ' + to_price + ' грн'
    except KeyError:
        if to_price != '':
            text = 'Список работ: ' + jobs_str + '\n' \
                   + '\n' + 'Cтоимость ТО - ' + to_price + ' грн'
        else:
            text = 'Информация не найдена'
    return text

def book_change(update, context):
    send_log_msg(update)
    context.user_data.pop('changed', None)
    reply_msg = 'Что изменить?'
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + [['Имя']] + [['Телефон']])
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_CHANGE_ACTION

def change_smth(update, context):
    send_log_msg(update)
    text = update.message.text
    thisdict =	{
      "Имя": "fullname",
      "Телефон": "phone",
    }
    context.user_data['changed'] = thisdict[text]
    reply_msg = 'Введите новые данные.'
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return CHANGE_ACTION

def book_confirm(update, context):
    send_log_msg(update)
    text = update.message.text
    if 'changed' in context.user_data:
        context.user_data[context.user_data['changed']] = text
    elif text != '\u2b05 Назад':
        context.user_data['phone'] = text
    reply_msg = get_confirm_msg(update, context)
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_CONFIRM + KEYBOARD_CHANGE)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_CONFIRM_ACTION

def write_data(update, context):
    send_log_msg(update)
    user_data = context.user_data
    dateslot = user_data['date'].split()
    date = dateslot[1]
    time = user_data['time']
    user = update.message.from_user
    status = get_status()
    write_data = [context.user_data['fullname'], context.user_data['auto'], '', 'ТО ' + context.user_data['to'],
                context.user_data['comments'], 'Бот', status, 'На обработке']
    read_records('book',date,time,write_data)
    reply_keyboard = [['Старт']]
    
    update.message.reply_text(
        'Запись произведена успешно! Номер вашей заявки: ' + status + '.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return START_ACTION

def carplate_db(update, context):
    send_log_msg(update)
    reply_msg = MSG_PLATE
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_AUTO)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return CARPLATE_DB_ACTION

def get_car_details(update, context):
    send_log_msg(update)
    reply_msg = 'Загрузка данных...'
    update.message.reply_text(reply_msg)
    text = update.message.text

    car_data = get_car_details_db_clean(text)

    if car_data == 0:
        reply_msg = MSG_NOT_FOUND
        reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_AUTO)
##        update.message.reply_text(reply_msg, reply_markup=reply_markup)
##        return CARPLATE_DB_ACTION
    else:
        context.user_data['auto'] = car_data[1]
        context.user_data['engine'] = car_data[2]
        car_data_str = 'Найдено: '
        for i in car_data:
            car_data_str += i + ' '
        reply_msg = car_data_str
        reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_CONTINUE + KEYBOARD_AUTO)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return CARPLATE_DB_ACTION

def carplate_db_price(update, context):
    send_log_msg(update)
    reply_msg = MSG_PLATE
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_AUTO)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return CARPLATE_DB_ACTION_PRICE

def get_car_details_price(update, context):
    send_log_msg(update)
    reply_msg = 'Загрузка данных...'
    update.message.reply_text(reply_msg)
    text = update.message.text

    car_data = get_car_details_db_clean(text)

    if car_data == 0:
        reply_msg = MSG_NOT_FOUND
        reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_AUTO)
##        update.message.reply_text(reply_msg, reply_markup=reply_markup)
##        return CARPLATE_DB_ACTION
    else:
        context.user_data['auto'] = car_data[1]
        context.user_data['engine'] = car_data[2]
        car_data_str = 'Найдено: '
        for i in car_data:
            car_data_str += i + ' '
        reply_msg = car_data_str
        reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_CONTINUE + KEYBOARD_AUTO)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return CARPLATE_DB_ACTION_PRICE

def not_ready(update, context):
    send_log_msg(update)
    reply_msg = MSG_NOT_READY
    reply_markup = get_reply_markup(KEYBOARD_MAIN)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return MAIN_MENU_ACTION

##def calc_to(update, context):
    

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

@app.route('/')
def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("728544464:AAGBm0Crj5a0-1Ydp_2B6PWuf3k_N5oDCEI", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(Filters.regex('^Старт$'),
                                    main_menu,
                                    pass_user_data=True),
                      MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True)],
        

        states={
            START_ACTION: [MessageHandler(Filters.regex('^Старт$'),
                                    main_menu,
                                    pass_user_data=True)
                       ],   
            MAIN_MENU_ACTION: [MessageHandler(Filters.regex('^Записаться на ТО$'),
                                    book,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Рассчитать стоимость ТО$'),
                                    price_auto,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Проверить статус заявки$'),
                                    get_status_now,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^База номеров$'),
                                    carplate_db,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u260e Контакты$'),
                                    not_ready,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True)
                       ],
            CARPLATE_DB_ACTION: [
                       MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_auto,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Продолжить$'),
                                    book_to,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Указать авто вручную$'),
                                    book_auto,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    get_car_details,
                                    pass_user_data=True)
                       ],
            CARPLATE_DB_ACTION_PRICE: [
                       MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_auto,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Продолжить$'),
                                    price_to,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Указать авто вручную$'),
                                    price_auto,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    get_car_details_price,
                                    pass_user_data=True)
                       ],
            BOOK_MENU_ACTION: [MessageHandler(Filters.regex('^Выбрать дату и время$'),
                                    book_date,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Показать все записи$'),
                                    not_ready,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    main_menu,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True)
                       ],
            BOOK_DATE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_time,
                                    pass_user_data=True)
                       ],
            BOOK_TIME_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_date,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_auto,
                                    pass_user_data=True)
                       ],
            BOOK_AUTO_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_time,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Найти авто по госномеру'),
                                    carplate_db,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_engine,
                                    pass_user_data=True)
                       ],
            BOOK_ENGINE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_auto,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_to,
                                    pass_user_data=True)
                       ],
            BOOK_TO_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_engine,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_comments,
                                    pass_user_data=True)
                       ],
            BOOK_COMMENTS_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_to,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_phone,
                                    pass_user_data=True)
                       ],
            BOOK_PHONE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_comments,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_confirm,
                                    pass_user_data=True)
                       ],
            PRICE_COMMENTS_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_time,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    price_phone,
                                    pass_user_data=True)
                       ],
            PRICE_PHONE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_comments,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_confirm,
                                    pass_user_data=True)
                       ],
            CHANGE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_change,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_confirm,
                                    pass_user_data=True)
                       ],
            BOOK_CONFIRM_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_phone,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Подтвердить запись$'),
                                    write_data,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Изменить данные$'),
                                    book_change,
                                    pass_user_data=True)
                       ],
            BOOK_CHANGE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_confirm,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    change_smth,
                                    pass_user_data=True)
                       ],
            
            PRICE_MENU_ACTION: [MessageHandler(Filters.text,
                                           not_ready,
                                           pass_user_data=True),

                        ],
            PRICE_AUTO_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    main_menu,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Найти авто по госномеру'),
                                    carplate_db_price,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    price_engine,
                                    pass_user_data=True)
                       ],
            PRICE_ENGINE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_auto,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    price_to,
                                    pass_user_data=True)
                       ],
            PRICE_TO_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_engine,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    price_confirm,
                                    pass_user_data=True)
                       ],
            PRICE_CONFIRM_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_engine,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Записаться на ТО$'),
                                    price_date,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^В главное меню$'),
                                    main_menu,
                                    pass_user_data=True)
                       ],
            PRICE_DATE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_confirm,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    price_time,
                                    pass_user_data=True)
                       ],
            PRICE_TIME_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    price_date,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    price_comments,
                                    pass_user_data=True)
                       ],
            GET_STATUS_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    main_menu,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    post_status_now,
                                    pass_user_data=True)
                       ],
            POST_STATUS_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    get_status_now,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Обновить$'),
                                    post_status_now,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    post_status_now,
                                    pass_user_data=True)
                       ],
        },
        fallbacks=[MessageHandler(Filters.regex('^\u274c Стоп$'), stop, pass_user_data=True)]
    )
    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    ##updater.idle()
    return "Bot is working now."

def read_records(mode, arg1='', arg2='', arg3=[]):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
##    if not creds or not creds.valid:
##        if creds and creds.expired and creds.refresh_token:
##            creds.refresh(Request())
##        else:
##            flow = InstalledAppFlow.from_client_secrets_file(
##                'credentials.json', SCOPES)
##            creds = flow.run_local_server()
##        # Save the credentials for the next run
##        with open('token.pickle', 'wb') as token:
##            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        if mode == 'bookings':
            print('Текущие записи:')
            for row in values:
                if len(row) != 4:
                    print('- ',row[1],row[2],row[3],row[4],row[5],row[6],row[7])
        elif mode == 'dates':
            dates = []
            for row in values:
                dates_record = row[1] + ', ' + row[2]
                if dates_record not in dates:
                    dates.append(dates_record)
##                    print(dates_record)
            return dates
        elif mode == 'times':
            times = []
            for row in values:
                if row[2] == arg1 and len(row) == 4:
                    times.append(row[3])
            return times
        elif mode == 'book':
            for row in values:
                if row[2] == arg1 and row[3] == arg2:
                    values = [arg3]
                    target_range = 'Запись!E'+row[0]+':L'+row[0]
                    body = {
                        'values': values
                    }
                    result = service.spreadsheets().values().update(
                        spreadsheetId=SAMPLE_SPREADSHEET_ID, range=target_range,
                        valueInputOption='RAW', body=body).execute()
##                    print('{0} cells updated.'.format(result.get('updatedCells')))
        elif mode == 'status':
            status = ''
            for row in values:
##                print(row)
##                print(len(row), )
                if len(row) == 12 and str(row[10]) == str(arg1):
##                    print(row[9], str(arg1))
                    status = row[11]
            return status
        elif mode == 'cars':
            cars = []
            for row in values:
                car = row[2] + ' ' + row[3]
                if car not in cars:
                    cars.append(car)
            return cars

##datetime_now = datetime.datetime.now()
##year = str(datetime_now.year)
##month = str(datetime_now.month)
##day = str(datetime_now.day)
##hours = str(datetime_now.hours)
##seconds = str(datetime_now.seconds)

def get_status():
    year, month, day, hour, minute = map(int, time.strftime("%Y %m %d %H %M").split())
    status_components = [year-2000, month, day, hour, minute]
    status_str = ''
    for i in range(len(status_components)):
        if len(str(status_components[i]))==1:
            status_components[i]='0'+str(status_components[i])
        status_str += str(status_components[i])
    return status_str
    
def get_status_now(update, context):
    send_log_msg(update)
    reply_msg = 'Введите номер заявки.'
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return GET_STATUS_ACTION

def post_status_now(update, context):
    send_log_msg(update)
    text = update.message.text
    if text != 'Обновить':
        context.user_data['status'] = text
    reply_msg = 'Загрузка данных...'
    update.message.reply_text(reply_msg)

    status_now = read_records('status', context.user_data['status'])
    if status_now != '':
        reply_msg = 'Текущий статус: ' + str(status_now)
    else:
        reply_msg = 'Заявка не найдена. Проверьте правильность номера.'
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + [['Обновить']])
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return POST_STATUS_ACTION

def index():
    votes = []
    with db.connect() as conn:
        # Execute the query and fetch all results
        recent_votes = conn.execute(
            "SELECT candidate, time_cast FROM votes "
            "ORDER BY time_cast DESC LIMIT 5"
        ).fetchall()
        # Convert the results into a list of dicts representing votes
        for row in recent_votes:
            votes.append({
                'candidate': row[0],
                'time_cast': row[1]
            })

        stmt = sqlalchemy.text(
            "SELECT COUNT(vote_id) FROM votes WHERE candidate=:candidate")
        # Count number of votes for tabs
        tab_result = conn.execute(stmt, candidate="TABS").fetchone()
        tab_count = tab_result[0]
        # Count number of votes for spaces
        space_result = conn.execute(stmt, candidate="SPACES").fetchone()
        space_count = space_result[0]

def generate_buttons(values, mode=''):
    buttons = []
    k = 0
    m = 0
    for i in range(len(values)):
        if k == 0:
            buttons.append([values[i]])
            k+=1
        else:
            buttons[m].append(values[i])
            m+=1
            k=0 
##    buttons = [['\u2b05 Назад', '\u274c Стоп']] + buttons
##    reply_keyboard = buttons
    return buttons

def read_cars():
    with open('cars.txt', encoding="utf8") as f:
        content = f.readlines()

    cars = []
    for line in content:
        record = line.split(';')
        record[3] = record[3].replace('\n','')
        cars.append(record)

    unique_cars = []
    for car in cars:
        unique_car = car[0]+' '+car[1]
        if unique_car not in unique_cars:
            unique_cars.append(unique_car)
    return unique_cars

def read_engines(carmode):
    with open('cars.txt', encoding="utf8") as f:
        content = f.readlines()
    cars = []
    for line in content:
        record = line.split(';')
        record[3] = record[3].replace('\n','')
        cars.append(record)

    engines = []
    for car in cars:
        engine = car[2]+car[3]
        if (car[0]+' '+car[1])==carmode and engine not in engines:
            engines.append(engine)
    return engines

def read_tos():
    with open('tos.txt', encoding="utf8") as f:
        content = f.readlines()
    tos = []
    for line in content:
        record = line.split(';')
        record[2] = record[2].replace('\n','')
        tos.append(record)

    unique_tos = []
    for to in tos:
        unique_to = to[1] + ' тыс.'
        if unique_to not in unique_tos:
            unique_tos.append(unique_to)
    return unique_tos

def read_tos2(model, engine, milage):
    with open('tos-2.txt', encoding="utf8") as f:
        content = f.readlines()
    tos = []
    for line in content:
        record = line.split(';')
        tos.append(record)

    jobs = []
    for to in tos:
        if to[1] == model and to[2]+to[3] == engine and to[6] == milage:
            jobs.append([to[5],to[7],to[8]])
    return jobs

def get_car_details_db(carplate):
    db = MySQLdb.connect("35.185.88.63" , "root" , "admin")
    cur = db.cursor()
    cur.execute("use easytodb")
    sql_string = "SELECT d_reg, brand, model, make_year, color, fuel, capacity, n_reg_new FROM reestr WHERE n_reg_new='"+carplate.upper()+"\\r'"
    cur.execute(sql_string)
    result = []
    for row in cur.fetchall():
        result.append(row)
    result_str = ''
    for row in result:
        for field in row:
            result_str += field + ', '
        result_str = result_str[:-2]
        result_str += '\n\n'
    db.close()
    return result_str

def get_car_details_db_clean(carplate):
    db = MySQLdb.connect("35.185.88.63" , "root" , "admin")
    cur = db.cursor()
    cur.execute("use easytodb")
    sql_string = "SELECT " \
                 + "brand, model, " \
                 + "CASE" \
                 + "    WHEN fuel = 'ДИЗЕЛЬНЕ ПАЛИВО' THEN CONCAT(convert(round(capacity/1000,1),char),'D') " \
                 + "    WHEN fuel like '%БЕНЗИН%' THEN CONCAT(convert(round(capacity/1000,1),char),'B') " \
                 + "    ELSE fuel " \
                 + "END eng, make_year " \
                 + "FROM reestr " \
                 + "WHERE n_reg_new='"+carplate.upper()+"\\r' " \
                 + "order by d_reg desc " \
                 + "limit 1 "
        
    cur.execute(sql_string)
    result = []
    for row in cur.fetchall():
        result.append(row)
    if result == []:
        return 0
    result_list = []
    for i in result[0]:
        result_list.append(i)
    result_list[0] = result_list[0].replace('  '+result_list[1],'')
    return result_list
##    result_str = ''
##    for row in result:
##        for range(len(row)):
##            
##
##        
##        for field in row:
##            result_str += field + ', '
##        result_str = result_str[:-2]
##        result_str += '\n\n'
##    db.close()
##    return result_str
##print(get_car_details_db_clean("Ае8781ів"))
##assert 0

if __name__ == '__main__':
    main()


