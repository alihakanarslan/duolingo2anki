from json import dumps

from duolingo import Duolingo
from requests import get, post
from selectolax.parser import HTMLParser
from deep_translator import GoogleTranslator

USERNAME = ''
PASSWORD = ''
MAIN_LANGUAGE = ''
TARGET_LANGUAGE = ''
DECK_NAME = f'[duolingo2anki] {MAIN_LANGUAGE} - {TARGET_LANGUAGE}'
NOTE_TYPE = ''
WORD_FIELD = ''
MEANING_FIELD = ''
SPELLING_FIELD = ''


def log(message: str):
    print(f'[duolingo2anki] - {message}')


def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    data = dumps(request(action, **params))
    response = post('http://localhost:8765', data=data.encode()).json()
    return response


def main():
    log('Connecting to the API...')
    api = Duolingo(USERNAME, PASSWORD)

    log('Getting words...')
    words = [i['word_string'] for i in api.get_vocabulary(TARGET_LANGUAGE)['vocab_overview']]

    url = F'https://duome.eu/vocabulary/{MAIN_LANGUAGE}/{TARGET_LANGUAGE}'
    content = get(url).content

    parser = HTMLParser(content)
    lis = parser.css_first('.plain').css('li:not(.single)')

    log('Getting meanings and spellings...')
    vocabulary = []
    gt = GoogleTranslator(source=TARGET_LANGUAGE, target=MAIN_LANGUAGE)
    for li in lis:
        if (info := li.css_first('.wA')).text() in words:
            title = info.attributes['title']
            spelling, meaning = title.split(']')
            vocabulary.append(
                {
                    'word': info.text().strip(),
                    'spelling': spelling[1:].strip(),
                    'meaning': meaning.strip() if len(meaning.strip()) > 0 else gt.translate(info.text().strip())
                }
            )

    invoke('createDeck', deck=DECK_NAME)

    log('Creating notes...')
    notes = [
        {
            'deckName': DECK_NAME,
            'modelName': NOTE_TYPE,
            'fields': {
                WORD_FIELD: w['word'],
                MEANING_FIELD: w['meaning'],
                SPELLING_FIELD: w['spelling']
            }
        } for w in vocabulary
    ]

    invoke('addNotes', notes=notes)
    log('Done.')


if __name__ == '__main__':
    main()
