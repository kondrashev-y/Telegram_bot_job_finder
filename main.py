import re

import requests
from flask import Flask
from flask.views import MethodView
from flask import request
import os


app = Flask(__name__)
TOKEN = os.environ.get('TOKEN')
API_URL = os.environ.get('API_URL')
TELEGRAM_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage'


def get_data_from_api(command):
    url = API_URL + command
    print(url, 'this is URL+command')
    session = requests.Session()
    r = session.get(url).json()
    print(r, 'this is r in get_data_from_api')
    return r


def send_message(chat_id, msg):
    session = requests.Session()
    r = session.get(TELEGRAM_URL, params=dict(chat_id=chat_id, text=msg, parse_mode='Markdown'))
    return r.json()


def parse_text(text_message):
    """Парсер входящих сообщений"""
    addresses = {'city': '/cities', 'lang': '/lang'}
    command_p = r'/\w+'
    doc_pattern = r'@\w+'
    message = 'Неверный запрос'
    if '/' in text_message:
        if '/start' in text_message or '/help' in text_message:
            message = '''Для того, чтобы узнать, какие города доступны, отправь в сообщени `/city`.
            Чтобы узнать о доступных языках программирования - отправь `/lang`.
            Чтобы сделать запрос на вакансии, отправь в сообщении через пробел  - @город @язык.
            Например так - `@moscow @python` '''
            return message
        else:
            command = re.search(command_p, text_message).group().replace('/', '')
            command = addresses.get(command, None)
            return [command] if command else None
    elif '@' in text_message:
        result = re.findall(doc_pattern, text_message)
        commands = [s.replace('@', '') for s in result]
        return commands if len(commands) == 2 else None
    else:
        return message


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        return '<h1>Hi bot!</h1>'
    return '<h1>Hi bot!</h1>'


class BotAPI(MethodView):
    """Оправление сообщений клиенту"""

    def get(self):
        return '<h1>Hi bot_class!</h1>'

    def post(self):
        resp = request.get_json()
        text_massage = resp['message']['text']
        chat_id = resp['message']['chat']['id']
        print(text_massage, 'this text_message in BotAPI')
        tmp = parse_text(text_massage)
        text_error = 'Неверный запрос'
        text_server_error = 'Сервер не отвечает'
        if tmp:
            if len(tmp) > 10:
                send_message(chat_id, tmp)
            elif len(tmp) == 1:
                message = ''
                msg = ''
                resp = get_data_from_api(tmp[0])
                if resp:
                    for d in resp:
                        message += '`' + d['slug'] + '`' + '\n'
                    if tmp[0] == '/lang':
                        msg = "Доступные языки: \n"
                    else:
                        msg = "Доступные города: \n"
                send_message(chat_id, msg + message)
            elif len(tmp) == 2:
                url = '/vacancy/?city={}&lang={}'.format(*tmp)
                resp = get_data_from_api(url)
                if resp:
                    parts = []
                    size = len(resp)
                    extra = size % 10
                    if size < 11:
                        parts.append(resp)
                    else:
                        num = 0
                        for i in range(size//10):
                            num = i * 10
                            parts.append(resp[num:num+10])
                        if extra:
                            parts.append(resp[num+10:])
                    text_msg = 'Рузльтат поиска согласно вашему запросу:\n' + '- ' * 10
                    send_message(chat_id, text_msg)

                    for part in parts:
                        message = ''
                        for item in part:
                            message += item['title'] + '\n'
                            message += item['url'] + '\n'
                            message += item['company'] + ' - '
                            message += item['salary'] + '\n'
                            message += '-' * 5 + '\n\n'
                        send_message(chat_id, message)
                else:
                    send_message(chat_id, text_server_error)

        else:
            send_message(chat_id, text_error)
        return '<h1>Hi i am chat bot!</h1>'


app.add_url_rule(f'/{TOKEN}/', view_func=BotAPI.as_view('bot'))

if __name__ == '__main__':
    app.run()
