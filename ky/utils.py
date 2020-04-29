
import json
from pathlib import Path


def load_meta(path=Path(__file__).absolute().parent.parent / 'wiki_surah_infos.json'):
    with path.open() as f:
        return json.load(f)


KY_NUMBER_LITERALS_TO_INT_MAP = dict(zip(
    'бир эки үч төрт беш алты жети сегиз тогуз он жыйырма отуз кырк элүү алтымыш жетимиш сексен токсон жүз'.split(),
    (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
))
INT_TO_KY_NUMBER_LITERALS_MAP = {v:k for k, v in KY_NUMBER_LITERALS_TO_INT_MAP.items()}

def ky_number_text_to_int(text):
    ayat_number = 0
    try:
        ayat_number = int(text)
    except ValueError:
        prev_ch = None
        for i, ch in enumerate(text.split()):
            ch = ch.lower()
            chv = KY_NUMBER_LITERALS_TO_INT_MAP[ch]
            if ch == 'жүз' and i != 0:
                ayat_number = chv * KY_NUMBER_LITERALS_TO_INT_MAP[prev_ch]
            else:
                ayat_number += chv
            prev_ch = ch
    return ayat_number


def int_to_ky_text(number):
    assert number < 1000
    s = []
    if number > 100:
        if number // 100 > 1:
            # бир жуз ... деп айтылбайт
            s.append(INT_TO_KY_NUMBER_LITERALS_MAP[number // 100])
        s.append('жүз')
        number = number % 100
    if number > 10:
        s.append(INT_TO_KY_NUMBER_LITERALS_MAP[number // 10 * 10])
        number = number % 10
    if number != 0:
        s.append(INT_TO_KY_NUMBER_LITERALS_MAP[number])
    return ' '.join(s)



def infinite_numbers_gen(start=1, step=1):
    while True:
        yield start
        start += step
