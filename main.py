# [START gae_python37_app]
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

def start(update, context):
    keyboard = [[InlineKeyboardButton("Записаться на ТО", callback_data='book')],
                 [InlineKeyboardButton("Рассчитать стоимость ТО", callback_data='price')],
                [InlineKeyboardButton("Проверить статус заявки", callback_data='status')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Привет! Я помогу вам записаться на ТО, рассчитать стоимость или уточнить статус заявки.\n\nВыберите желаемое действие:\n\n', reply_markup=reply_markup)

def button(update, context):
    query = update.callback_query
    start_option = query.data
    if start_option == 'book':
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

def book(query):
    keyboard = [[InlineKeyboardButton("Указать VIN-код", callback_data='book_vin')],
                 [InlineKeyboardButton("Указать характеристики автомобиля", callback_data='book_auto')],
                [InlineKeyboardButton("<< Назад", callback_data='book_back')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Запись на ТО\n\n", reply_markup=reply_markup)

def price(query):
    keyboard = [[InlineKeyboardButton("Указать VIN-код", callback_data='book_vin')],
                 [InlineKeyboardButton("Указать характеристики автомобиля", callback_data='book_auto')],
                [InlineKeyboardButton("<< Назад", callback_data='book_back')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Рассчет стоимости ТО\n\n", reply_markup=reply_markup)

def status(query):
    query.message.reply_text('ОК. Укажите VIN-код или номер заявки.')

def book_vin(query):
    query.message.reply_text('ОК. Укажите VIN-код автомобиля.')

def book_auto(query):
    query.message.reply_text('ОК. Укажите марку и модель автомобиля.')

def book_back(query):
    keyboard = [[InlineKeyboardButton("Записаться на ТО", callback_data='book')],
                 [InlineKeyboardButton("Рассчитать стоимость ТО", callback_data='price')],
                [InlineKeyboardButton("Проверить статус заявки", callback_data='status')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите желаемое действие:\n\n", reply_markup=reply_markup)

def help(update, context):
    update.message.reply_text("Используйте /start для начала работы.")

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("728544464:AAGBm0Crj5a0-1Ydp_2B6PWuf3k_N5oDCEI", use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, help))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
##    updater.idle()
    return "It's fucking working!"

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
