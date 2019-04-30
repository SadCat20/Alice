from flask import Flask, request
import logging
import json
import random
from geo import get_country, get_distance, get_coordinates
from get_entities import get_cities, get_first_name

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities_ = {
    'москва': [
        '1540737/daa6e420d33102bf6947', '213044/7df73ae4cc715175059e'
    ],
    'нью-йорк': [
        '1652229/728d5c86707054d4745f', '1030494/aca7ed7acefde2606bdc'
    ],
    'париж': [
        '1652229/f77136c2364eb90a3ea8', '3450494/aca7ed7acefde22341bdc'
    ]
}

# имена пользователей
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    # если пользователь новый
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # если пользователь не новый
    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        # если не нашли
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' + first_name.title()  + '. Я - Алиса. Я могу показать город или сказать расстояние между городами!'
            res['response']['buttons'] = [
                {
                    'title': city.title(),
                    'hide': True
                } for city in cities_
            ]

    # если пользователь уже что-то написал
    else:
        # ищем города в сообщении от пользователя
        cities = get_cities(req)
        if not cities:
            res['response']['text'] = 'Ты не написал название ни одного города!'

        elif len(cities) == 1:

            if cities[0] in cities_:
                if 'подробнее'  in req['request']['original_utterance'].lower() or 'хочу больше информации' in req['request']['original_utterance'].lower():
                    res['response']['text'] = 'https://ru.wikipedia.org/wiki/' + cities[0]
                else:
                    res['response']['card'] = {}
                    res['response']['card']['type'] = 'BigImage'
                    res['response']['card']['title'] = 'Этот город я знаю. Он в стране ' + get_country(cities[0]) + '.'
                    res['response']['card']['image_id'] = random.choice(cities_[cities[0]])
                    res['response']['text'] = 'Этот город я знаю.'
            else:
                res['response']['text'] = 'Этот город я знаю. Он в стране ' + get_country(cities[0]) + '.'

        elif len(cities) == 2:
            distance = get_distance(get_coordinates(
                cities[0]), get_coordinates(cities[1]))
            res['response']['text'] = 'Расстояние между этими городами: ' + str(round(distance)) + ' км.'
        else:
            res['response']['text'] = 'Слишком много городов!'
            res['response']['buttons'] = [
                {
                    'title': city.title(),
                    'hide': True
                } for city in cities_
            ]


def get_suggests(user_id):
    session = sessionStorage[user_id]

    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests']
    ]

    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    return suggests


if __name__ == '__main__':
    app.run()
