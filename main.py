import requests
from flask import Flask
from flask import request
import telebot
import os


app = Flask(__name__)
TOKEN = os.environ.get('TOKEN')
API_URL = os.environ.get('API_URL')
bot = telebot.TeleBot(TOKEN)


choice_lang = ''
choice_city = ''


def get_data_from_api(command):
    url = API_URL + command
    try:
        session = requests.Session()
        r = session.get(url).json()
        return r
    except Exception as e:
        print(repr(e))
        return []


try:
    lang_list = get_data_from_api('/lang')
    lang_slug_list = [item['slug'] for item in lang_list]
    cities_list = get_data_from_api('/cities')
    cities_slug_list = [item['slug'] for item in cities_list]
except Exception as e:
    print(repr(e))
    pass


@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_2 = telebot.types.InlineKeyboardMarkup()
    button_lang = telebot.types.InlineKeyboardButton('Начать поиск', callback_data='lang')
    markup_2.row(button_lang)
    button_a = telebot.types.InlineKeyboardButton('/help')
    markup.row(button_a)
    bot.send_message(message.chat.id, 'Привет, это бот сервиса по сбору вакансий, '
                                      'введу команду /help для подробной информации.', reply_markup=markup)
    bot.send_message(message.chat.id, 'Или сразу переходи к поиску', reply_markup=markup_2)


@bot.message_handler(commands=['help'])
def hel_info(message):
    markup = telebot.types.InlineKeyboardMarkup()

    button_lang = telebot.types.InlineKeyboardButton('Начать поиск', callback_data='lang')

    markup.row(button_lang)

    bot.send_message(message.chat.id, 'Привет, это телеграмм бот сервиса по сбору вакансий, для отображения вакансий'
                                      'за сегоднешний деннь необходимо выбрать язык и город.', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['lang'])
def lang(call):
    global lang_list
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for item in lang_list:
        buttons.append(telebot.types.InlineKeyboardButton(text=item['name'], callback_data=item['slug']))
    markup.add(*buttons)
    bot.send_message(call.message.chat.id, 'Выберите язык', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in lang_slug_list + cities_slug_list)
def callback_inline(call):
    global choice_lang, choice_city

    if call.data in lang_slug_list:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id)

        markup = telebot.types.InlineKeyboardMarkup()
        buttons = []

        bot.send_message(call.message.chat.id, f'Язык - {call.data}')

        for city in cities_list:
            buttons.append(markup.add(telebot.types.InlineKeyboardButton(text=city['name'],
                                                                         callback_data=city['slug'])))
        bot.send_message(call.message.chat.id, 'Выберите город', reply_markup=markup)
        choice_lang = call.data

    elif call.data in cities_slug_list:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
        choice_city = call.data
        bot.send_message(call.message.chat.id, f'Город - {call.data}')
        bot.send_message(call.message.chat.id, 'Подождите, загружаю...')
        print(choice_lang, choice_city)
        try:
            if choice_city and choice_lang:
                command = f'/vacancy/?city={choice_city}&lang={choice_lang}'
                if '#' in choice_lang:
                    choice_lang = 'c%23'
                vacancy = get_data_from_api(command)
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                buttons = []
                if len(vacancy) == 0:
                    bot.send_message(call.message.chat.id, 'Упс, на сегодня вакансий еще '
                                                           'не появилось, попробуйте позже')
                for item in vacancy:
                    buttons.append(telebot.types.InlineKeyboardButton(text=f"{item['title']} - {item['salary']}",
                                                                      url=item['url']))
                    if len(buttons) % 10 == 0:
                        markup.add(*buttons)
                        bot.send_message(call.message.chat.id, 'Доступные вакансии', reply_markup=markup)
                        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                        buttons = []
                if buttons:
                    markup.add(*buttons)
                    bot.send_message(call.message.chat.id, 'Доступные вакансии', reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, 'Что то пошло не  так, выберите язык и город')
        except Exception as e:
            print(repr(e))


@bot.message_handler(func=lambda message: True)
def other_message(message):
    bot.send_message(message.chat.id, 'Упс, неверная команда, попробуйте еще раз.')


@app.route("/" + TOKEN + "/", methods=['POST'])
def getMessage():
    print('getMessage work')
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route('/', methods=['GET'])
def index():
    return '<h1>Hi bot!</h1>'


if __name__ == '__main__':
    app.run()
