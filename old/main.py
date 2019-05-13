#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.
#
# THIS EXAMPLE HAS BEEN UPDATED TO WORK WITH THE BETA VERSION 12 OF PYTHON-TELEGRAM-BOT.
# If you're still using version 11.1.0, please see the examples at
# https://github.com/python-telegram-bot/python-telegram-bot/tree/v11.1.0/examples

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler, CallbackQueryHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

##BOOK_MENU, ETC, LOCATION, BIO, PROCESS_SELECT, SOME_OTHER = range(6)


def start(update, context):
##    reply_keyboard = [['Записаться на ТО'],['Рассчитать стоимость ТО'],['Проверить статус заявки']]
    reply_keyboard = [[InlineKeyboardButton('Записаться на ТО', callback_data='book')],
            [InlineKeyboardButton('Рассчитать стоимость ТО', callback_data='price')],
            [InlineKeyboardButton('Проверить статус заявки', callback_data='status')]]
    update.message.reply_text(
        'Привет! Я помогу вам записаться на ТО, рассчитать стоимость '
        'или уточнить статус заявки.\n\n'
        'Выберите желаемое действие.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    print('start')

def button(update, context):
    print('here')
    query = update.callback_query
    start_option = query.data
    if start_option == 'book':
        print('book')
        book(query)
    elif start_option == 'price':
        price(query)
    elif start_option == 'status':
        status(query)
    elif start_option == 'book_vin':
        book_vin(query)
    elif start_option == 'book_auto':
        book_auto(query)
    elif start_option == 'book_back':
        book_back(query)

def book(update, context):
    user = update.message.from_user
    logger.info("MAIN_MENU_ACTION of %s: %s", user.first_name, update.message.text)
    
    reply_keyboard = [['Выбрать дату и время'],['*Показать все записи'],['Назад']]
    update.message.reply_text(
        'Выберите свободный слот.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))

def main():
    updater = Updater("728544464:AAGBm0Crj5a0-1Ydp_2B6PWuf3k_N5oDCEI", use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.start_polling()
##    print('main')
    updater.idle()

main()


##    main_manu_action = update.message.text
##    print(main_manu_action)
##    if main_manu_action == 'Записаться на ТО':
##        print('here')
##        return BOOK_MENU
##    else:
##        return ETC


##def process_select(update, context, user_data):
##    print('+')
####    query = update.callback_query
####    selection = query.data
####    user_data['selection'] = selection
##    
##    main_manu_action = update.message.text
##    print(main_manu_action)
##    
##    if main_manu_action == 'Записаться на ТО':
##        print('here')
##        return BOOK_MENU
##    else:
##        return ETC



##    return BOOK_MENU_ACTION

##def book_dates(update, context):
##    user = update.message.from_user
##    logger.info("BOOK_MENU_ACTION of %s: %s", user.first_name, update.message.text)
##    
##    reply_keyboard = [['Cр, 08/05','Чт, 09/05','Пт, 10/05'],['<< Назад']]
##    update.message.reply_text(
##        'Выберите дату.',
##        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
##
##    return BOOK_DATE
##
##def book_times(update, context):
##    user = update.message.from_user
##    logger.info("BOOK_DATE of %s: %s", user.first_name, update.message.text)
##    
##    reply_keyboard = [['10:00','11:00','12:00'],['<< Назад']]
##    update.message.reply_text(
##        'Выберите время.',
##        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
##
##    return BOOK_TIME
##
##def book_action(update, context):
##    user = update.message.from_user
##    logger.info("BOOK_TIME of %s: %s", user.first_name, update.message.text)
##    
##    reply_keyboard = [['Записаться'],['<< Назад']]
##    update.message.reply_text(
##        'Подтвердите запись на Среду, 08 мая, 11:00',
##        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
##
##
##
##    return BOOK_CONFIRM
##
##
##def book():
##    return 1
##
##def button(update, context):
##    query = update.callback_query
##    start_option = query.data
##    if start_option == 'book':
##        book(query)
##    elif start_option == 'price':
##        price(query)
##    elif start_option == 'status':
##        status(query)
##    elif start_option == 'book_vin':
##        book_vin(query)
##    elif start_option == 'book_auto':
##        book_auto(query)
##    elif start_option == 'book_back':
##        book_back(query)
##
##
##def photo(update, context):
##    user = update.message.from_user
##    photo_file = update.message.photo[-1].get_file()
##    photo_file.download('user_photo.jpg')
##    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
##    update.message.reply_text('Gorgeous! Now, send me your location please, '
##                              'or send /skip if you don\'t want to.')
##
##    return LOCATION
##
##
##def skip_photo(update, context):
##    user = update.message.from_user
##    logger.info("User %s did not send a photo.", user.first_name)
##    update.message.reply_text('I bet you look great! Now, send me your location please, '
##                              'or send /skip.')
##
##    return LOCATION
##
##
##def location(update, context):
##    user = update.message.from_user
##    user_location = update.message.location
##    logger.info("Location of %s: %f / %f", user.first_name, user_location.latitude,
##                user_location.longitude)
##    update.message.reply_text('Maybe I can visit you sometime! '
##                              'At last, tell me something about yourself.')
##
##    return BIO
##
##
##def skip_location(update, context):
##    user = update.message.from_user
##    logger.info("User %s did not send a location.", user.first_name)
##    update.message.reply_text('You seem a bit paranoid! '
##                              'At last, tell me something about yourself.')
##
##    return BIO
##
##
##def bio(update, context):
##    user = update.message.from_user
##    logger.info("Bio of %s: %s", user.first_name, update.message.text)
##    update.message.reply_text('Thank you! I hope we can talk again some day.')
##
##    return ConversationHandler.END
##
##
##def cancel(update, context):
##    user = update.message.from_user
##    logger.info("User %s canceled the conversation.", user.first_name)
##    update.message.reply_text('До свидания!',
##                              reply_markup=ReplyKeyboardRemove())
##
##    return ConversationHandler.END
##
##
##def error(update, context):
##    """Log Errors caused by Updates."""
##    logger.warning('Update "%s" caused error "%s"', update, context.error)
##
##
##def main():
##    # Create the Updater and pass it your bot's token.
##    # Make sure to set use_context=True to use the new context based callbacks
##    # Post version 12 this will no longer be necessary
##    updater = Updater("728544464:AAGBm0Crj5a0-1Ydp_2B6PWuf3k_N5oDCEI", use_context=True)
##
##    # Get the dispatcher to register handlers
##    dp = updater.dispatcher
##
##    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
##    conv_handler = ConversationHandler(
##        entry_points=[CommandHandler('start', start_menu)],
##
##        states={ETC: [RegexHandler('^(Boy|Girl|Other)$', error)],},
##        fallbacks=[CommandHandler('cancel', cancel)]
##    )
##
##    dp.add_handler(conv_handler)
##
##    # log all errors
##    dp.add_error_handler(error)
##
##    # Start the Bot
##    updater.start_polling()
##
##    # Run the bot until you press Ctrl-C or the process receives SIGINT,
##    # SIGTERM or SIGABRT. This should be used most of the time, since
##    # start_polling() is non-blocking and will stop the bot gracefully.
##    updater.idle()
##
##
##if __name__ == '__main__':
##    main()
