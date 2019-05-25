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
import logging
import os.path
from flask import Flask

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1IC8VyWS2VLZGrhKJC4lIHwtDeoQWD_ZeEMUHrlb9dp8'
SAMPLE_RANGE_NAME = 'Запись!A2:J1000'
    
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
                          ['Рассчитать стоимость ТО'],['Проверить статус заявки'], ['База номеров']]
KEYBOARD_BOOK = [['Выбрать дату и время'],['Показать все записи']]

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
MSG_PLATE_NOT_FOUND =   'Машина не найдена, попробуйте другой номер.'
MSG_NOT_READY = 'Это пока не готово :)'

# Main
app = Flask(__name__)

# Responses
(START_ACTION, MAIN_MENU_ACTION, BOOK_MENU_ACTION, PRICE_MENU_ACTION,
 STATUS_MENU_ACTION, TYPING_REPLY, TYPING_CHOICE, BOOK_DATE_ACTION, BOOK_TIME_ACTION,
 BOOK_AUTO_ACTION, BOOK_REG_ACTION, BOOK_TO_ACTION, BOOK_COMMENTS_ACTION,
 BOOK_CONFIRM_ACTION, BOOK_ENGINE_ACTION, CARPLATE_DB_ACTION) = range(16)


def get_reply_markup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True):
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

def main_menu(update, context):
    send_log_msg(update)
    reply_msg = MSG_MAIN
    reply_markup = get_reply_markup(KEYBOARD_MAIN)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return MAIN_MENU_ACTION

def book(update, context):
    send_log_msg(update)
    reply_msg = MSG_BOOK
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + KEYBOARD_BOOK)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)
    return BOOK_MENU_ACTION

def book_date(update, context):
    send_log_msg(update)
    dates = read_records('dates')
    keyboard = generate_buttons(dates)
    reply_msg = MSG_DATE
    reply_markup = get_reply_markup(KEYBOARD_BACK_STOP + keyboard)
    update.message.reply_text(reply_msg, reply_markup=reply_markup)   
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
    times_buttons = [['\u2b05 Назад', '\u274c Стоп']] + times_buttons
    reply_keyboard = times_buttons
    update.message.reply_text(
        'Выберите время.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return BOOK_TIME_ACTION

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

def carplate_db(update, context):
    
    reply_keyboard = [['\u2b05 Назад', '\u274c Стоп']]
    update.message.reply_text(
        'Введите номерной знак.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return CARPLATE_DB_ACTION

def get_car_details(update, context):

    msg = 'Загрузка данных...'
    update.message.reply_text(
        msg)


    text = update.message.text
    msg = get_car_details_db(text)
    if msg == '':
        msg = 'Машина не найдена, попробуйте другой номер.'
    reply_keyboard = [['\u2b05 Назад', '\u274c Стоп']]
    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return CARPLATE_DB_ACTION

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
    read_records('book',date,time,write_data)

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
    return main_ACTION

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

@app.route('/')
def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("837308089:AAFgncR0cc4W6gDubC6Jx0id0cowuwaLCdQ", use_context=True)

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
                                    not_ready,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Проверить статус заявки$'),
                                    not_ready,
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
                                    main,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    get_car_details,
                                    pass_user_data=True)
                       ],

            BOOK_MENU_ACTION: [MessageHandler(Filters.regex('^Выбрать дату и время$'),
                                    book_date,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Показать все записи$'),
                                    not_ready,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    main,
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
                                    book_date,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_engine,
                                    pass_user_data=True)
                       ],

            BOOK_ENGINE_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_date,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                    book_to,
                                    pass_user_data=True)
                       ],

            BOOK_TO_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_auto,
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
                                    book_confirm,
                                    pass_user_data=True)
                       ],
            BOOK_CONFIRM_ACTION: [MessageHandler(Filters.regex('^\u2b05 Назад$'),
                                    book_comments,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^\u274c Стоп$'),
                                    stop,
                                    pass_user_data=True),
                       MessageHandler(Filters.regex('^Подтвердить запись$'),
                                    write_data,
                                    pass_user_data=True)
                       ],
            
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

        fallbacks=[MessageHandler(Filters.regex('^Done$'), done, pass_user_data=True)]
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
                    target_range = 'Запись!E'+row[0]+':I'+row[0]
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


if __name__ == '__main__':
##    app.run(host='127.0.0.1', port=8080, debug=True)
    main()


