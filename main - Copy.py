#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

##from flask import Flask
import logging
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          RegexHandler, ConversationHandler)

##from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

##app = Flask(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1IC8VyWS2VLZGrhKJC4lIHwtDeoQWD_ZeEMUHrlb9dp8'
SAMPLE_RANGE_NAME = 'Запись!A2:J1000'
    
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

(START_ACTION, MAIN_MENU_ACTION, BOOK_MENU_ACTION, PRICE_MENU_ACTION,
 STATUS_MENU_ACTION, TYPING_REPLY, TYPING_CHOICE, BOOK_DATE_ACTION, BOOK_TIME_ACTION,
 BOOK_AUTO_ACTION, BOOK_REG_ACTION, BOOK_TO_ACTION, BOOK_COMMENTS_ACTION,
 BOOK_CONFIRM_ACTION, BOOK_ENGINE_ACTION) = range(15)

def start(update, context):
    
    reply_keyboard = [['Старт']]
    update.message.reply_text(
        'Привет! Я помогу вам записаться на ТО, рассчитать стоимость '
        'или уточнить статус заявки.\n\n'
        'Нажмите Старт для начала работы.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
   
    return START_ACTION

def stop(update, context):
    
    reply_keyboard = [['Старт']]
    update.message.reply_text(
        'Работа приостановлена. Возвращайтесь!',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
   
    return START_ACTION

def main_menu(update, context):
    
    reply_keyboard = [['\u260e Контакты', '\u274c Стоп'],['Записаться на ТО'],
                      ['Рассчитать стоимость ТО'],['Проверить статус заявки']]
    update.message.reply_text('Выберите желаемое действие.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
   
    return MAIN_MENU_ACTION


def book(update, context):
    user = update.message.from_user
    logger.info("MAIN_MENU_ACTION of %s: %s", user.full_name, update.message.text)
    
    reply_keyboard = [['\u2b05 Назад', '\u274c Стоп'],['Выбрать дату и время'],['Показать все записи']]
    update.message.reply_text(
        'Выберите свободный слот.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_MENU_ACTION

def book_date(update, context):
    user = update.message.from_user
    logger.info("BOOK_MENU_ACTION of %s: %s", user.full_name, update.message.text)

    dates = read_records('dates')
    dates_buttons = []
    k = 0
    m = 0
    for i in range(len(dates)):
        if k == 0:
            dates_buttons.append([dates[i]])
            k+=1
        else:
            dates_buttons[m].append(dates[i])
            m+=1
            k=0
    dates_buttons = [['\u2b05 Назад', '\u274c Стоп']] + dates_buttons
    reply_keyboard = dates_buttons
    update.message.reply_text(
        'Выберите дату.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    
    return BOOK_DATE_ACTION

def book_time(update, context):

    text = update.message.text
    context.user_data['date'] = text
    dateslot = text.split()
    date = dateslot[1]
    times = read_records('times', date)
    times_buttons = []
    k = 0
    m = 0
    for i in range(len(times)):
        if k == 0:
            times_buttons.append([times[i]])
            k+=1
        else:
            times_buttons[m].append(times[i])
            m+=1
            k=0
##    print(user_data)
##    print(times_buttons)   
    times_buttons = [['\u2b05 Назад', '\u274c Стоп']] + times_buttons
    reply_keyboard = times_buttons
    update.message.reply_text(
        'Выберите время.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_TIME_ACTION

##def book_reg(update, context):
##
##    user_data = context.user_data
####    if 'time' in user_data:
####        del user_data['time']
##    text = update.message.text
##    context.user_data['reg'] = text
##    user_data = context.user_data
##    
##    reply_keyboard = [['\u2b05 Назад', '\u274c Стоп'],['Пропустить']]
##    text = 'Отлично, мы разерезвировали для вас слот на ' + user_data['date'], + user_data['time'] + _
##    '\n\n'
##    update.message.reply_text(
##        'Отлично, мы разерезвировали для вас Введите reg',
##        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
##    return BOOK_REG_ACTION


def book_auto(update, context):


    text = update.message.text
    context.user_data['time'] = text

    reply_keyboard = generate_buttons(read_cars())
    update.message.reply_text(
        'Веберите модель вашего автомобиля.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_AUTO_ACTION

def book_engine(update, context):


    text = update.message.text
    context.user_data['auto'] = text

    reply_keyboard = generate_buttons(read_engines(text))
    update.message.reply_text(
        'Укажите двигатель.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_ENGINE_ACTION

def book_to(update, context):


    text = update.message.text
    context.user_data['engine'] = text

    reply_keyboard = generate_buttons(read_tos())
    update.message.reply_text(
        'Укажите ТО или введите текущий пробег автомобиля.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_TO_ACTION

def book_comments(update, context):

    text = update.message.text
    context.user_data['to'] = text
    
    reply_keyboard = [['\u2b05 Назад', '\u274c Стоп'],['Пропустить']]
    update.message.reply_text(
        'Укажите дополнительные комментарии.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_COMMENTS_ACTION

def book_confirm(update, context):
    
    text = update.message.text
    context.user_data['comments'] = text
    user = update.message.from_user
    reply_keyboard = [['\u2b05 Назад', '\u274c Стоп'],['Подтвердить запись']]
    text = 'Отлично! Проверьте пожалуйста данные:\n\n' \
           + ' - Имя: ' + user.full_name + '\n' \
           + ' - Дата: ' + context.user_data['date'] + '\n' \
           + ' - Время: ' + context.user_data['time'] + '\n' \
           + ' - Автомобиль: ' + context.user_data['auto'] + '\n' \
           + ' - Двигатель: ' + context.user_data['engine'] + '\n' \
           + ' - ТО: ' + context.user_data['to'] + '\n' \
           + ' - Комментарии: ' + context.user_data['comments'] + '\n' \
           + '\n' + 'Примерная стоимость ТО - 8428 грн'
    update.message.reply_text(text,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_CONFIRM_ACTION

def write_data(update, context):

    user_data = context.user_data
    dateslot = user_data['date'].split()
    date = dateslot[1]
    time = user_data['time']
    user = update.message.from_user
    write_data = [user.full_name, context.user_data['auto'], '', 'ТО ' + context.user_data['to'],
                context.user_data['comments']]
    print(write_data)
    read_records('book',date,time,write_data)
##    print(key_data)
##    return

    reply_keyboard = [['Старт']]
    update.message.reply_text(
        'Запись произведена успешно! Номер вашей заявки: 14580.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return START_ACTION


def not_ready(update, context):
    user = update.message.from_user
    logger.info("PRICE_MENU_ACTION of %s: %s", user.full_name, update.message.text)
    
    reply_keyboard = [['\u260e Контакты', '\u274c Стоп'],['Записаться на ТО'],
                      ['Рассчитать стоимость ТО'],['Проверить статус заявки']]
    update.message.reply_text(
        'Это пока не готово :)',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return MAIN_MENU_ACTION

def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'Your {}? Yes, I would love to hear about that!'.format(text.lower()))

    return TYPING_REPLY


def custom_choice(update, context):
    update.message.reply_text('Alright, please send me the category first, '
                              'for example "Most impressive skill"')

    return TYPING_CHOICE


def received_information(update, context):
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text("Neat! Just so you know, this is what you already told me:"
                              "{}"
                              "You can tell me more, or change your opinion on something.".format(
                                  facts_to_str(user_data)), reply_markup=markup)

    return CHOOSING


def done(update, context):
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("I learned these facts about you:"
                              "{}"
                              "Until next time!".format(facts_to_str(user_data)))

    user_data.clear()
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

##@app.route('/')
def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("728544464:AAGBm0Crj5a0-1Ydp_2B6PWuf3k_N5oDCEI", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            START_ACTION: [RegexHandler('^Старт$',
                                    main_menu,
                                    pass_user_data=True)
                       ],
            
            MAIN_MENU_ACTION: [RegexHandler('^Записаться на ТО$',
                                    book,
                                    pass_user_data=True),
                       RegexHandler('^Рассчитать стоимость ТО$',
                                    not_ready,
                                    pass_user_data=True),
                       RegexHandler('^Проверить статус заявки$',
                                    not_ready,
                                    pass_user_data=True),
                       RegexHandler('^\u260e Контакты$',
                                    not_ready,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True)
                       ],

            BOOK_MENU_ACTION: [RegexHandler('^Выбрать дату и время$',
                                    book_date,
                                    pass_user_data=True),
                       RegexHandler('^Показать все записи$',
                                    not_ready,
                                    pass_user_data=True),
                       RegexHandler('^\u2b05 Назад$',
                                    main_menu,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True)
                       ],

            BOOK_DATE_ACTION: [RegexHandler('^\u2b05 Назад$',
                                    book,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_time,
                                    pass_user_data=True)
                       ],
            
            BOOK_TIME_ACTION: [RegexHandler('^\u2b05 Назад$',
                                    book_date,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_auto,
                                    pass_user_data=True)
                       ],
            BOOK_AUTO_ACTION: [RegexHandler('^\u2b05 Назад$',
                                    book_date,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_engine,
                                    pass_user_data=True)
                       ],

            BOOK_ENGINE_ACTION: [RegexHandler('^\u2b05 Назад$',
                                    book_date,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_to,
                                    pass_user_data=True)
                       ],
##            BOOK_REG_ACTION: [RegexHandler('^\u2b05 Назад$',
##                                    book_auto,
##                                    pass_user_data=True),
##                       RegexHandler('^\u274c Стоп$',
##                                    stop,
##                                    pass_user_data=True),
##                        MessageHandler(Filters.text,
##                                    book_to,
##                                    pass_user_data=True)
##                       ],
            
            BOOK_TO_ACTION: [RegexHandler('^\u2b05 Назад$',
                                    book_auto,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_comments,
                                    pass_user_data=True)
                       ],
            BOOK_COMMENTS_ACTION: [RegexHandler('^\u2b05 Назад$',
                                    book_to,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_confirm,
                                    pass_user_data=True)
                       ],
            BOOK_CONFIRM_ACTION: [RegexHandler('^\u2b05 Назад$',
                                    book_comments,
                                    pass_user_data=True),
                       RegexHandler('^\u274c Стоп$',
                                    stop,
                                    pass_user_data=True),
                       RegexHandler('^Подтвердить запись$',
                                    write_data,
                                    pass_user_data=True)
                       ],
            
##            BOOK_DONE_ACTION: [RegexHandler('^\u2b05 Назад$',
##                                    book_comments,
##                                    pass_user_data=True),
##                       RegexHandler('^\u274c Стоп$',
##                                    stop,
##                                    pass_user_data=True),
##                       RegexHandler('^Подтвердить запись$',
##                                    done,
##                                    pass_user_data=True)
##                       ],


            PRICE_MENU_ACTION: [MessageHandler(Filters.text,
                                           not_ready,
                                           pass_user_data=True),
                            ],
            STATUS_MENU_ACTION: [MessageHandler(Filters.text,
                                           not_ready,
                                           pass_user_data=True)
                            ],
    

            TYPING_CHOICE: [MessageHandler(Filters.text,
                                           regular_choice,
                                           pass_user_data=True)
                            ],

            TYPING_REPLY: [MessageHandler(Filters.text,
                                          received_information,
                                          pass_user_data=True)
                           ],
        },

        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
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
                # Print columns A and E, which correspond to indices 0 and 4.
    ##            print(len(row))
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
            print(arg1)
            times = []
            for row in values:
                if row[2] == arg1 and len(row) == 4:
                    times.append(row[3])
            return times
        elif mode == 'book':
            for row in values:
                if row[2] == arg1 and row[3] == arg2:
                    values = [arg3]
                    target_range = 'Запись!E'+row[0]+':I'+row[0]
                    print(target_range)
##                    return
                    print('Now updating...')
                    body = {
                        'values': values
                    }
                    result = service.spreadsheets().values().update(
                        spreadsheetId=SAMPLE_SPREADSHEET_ID, range=target_range,
                        valueInputOption='RAW', body=body).execute()
                    print('{0} cells updated.'.format(result.get('updatedCells')))
        elif mode == 'cars':
            cars = []
            for row in values:
                car = row[2] + ' ' + row[3]
                if car not in cars:
                    cars.append(car)
            return cars

##thisdict =	{
##  "brand": "Ford",
##  "model": "Mustang",
##  "year": 1964
##}

##import datetime

##read_records('bookings')
##print(dates_buttons)

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
    buttons = [['\u2b05 Назад', '\u274c Стоп']] + buttons
    reply_keyboard = buttons
    return reply_keyboard

def read_cars():
    with open('cars.txt') as f:
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
    with open('cars.txt') as f:
        content = f.readlines()
    cars = []
    for line in content:
        record = line.split(';')
        record[3] = record[3].replace('\n','')
        cars.append(record)

    engines = []
    for car in cars:
        engine = car[2]+car[3]
##        print(engine)
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

if __name__ == '__main__':
##    app.run(host='127.0.0.1', port=8080, debug=True)
    main()

##print(read_tos())

##buttons = generate_buttons(unique_cars)
##print(buttons)
##print(read_engines('Audi A6'))
##main()
##generate_buttons(read_cars())




