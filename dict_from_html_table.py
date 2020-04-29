#!/usr/bin/env python3

from bs4 import BeautifulSoup, NavigableString
import re
import json
from pathlib import Path


def main():

    with open('wiki_table_of_surahs.html') as f:
        soup = BeautifulSoup(f, features="lxml")

    surah_infos = []

    for row in soup.find_all('tr'):
        surah_id, eng_title, arabic_title, _, verses_number, revelation_place, chrono_order, *_ = row.find_all('td')
        surah_id = int(surah_id.string)
        eng_title = eng_title.text.strip()
        arabic_lang_title = arabic_title.find('span').string.strip()
        arabic_latin_title = arabic_title.find('i').string.strip()
        verses_count = int(re.match(r'(\d+)', verses_number.string).groups()[0])
        revelation_place = revelation_place.string.strip()
        chrono_order = int(chrono_order.string)

        surah_info = dict(
            number=surah_id,
            english_title=eng_title,
            arabic_title=arabic_lang_title,
            latin_arabic_title=arabic_latin_title,
            verses_count=verses_count,
            revelation_place=revelation_place,
            chronological_order=chrono_order,
        )

        surah_infos.append(surah_info)
        # print(['{}:{}'.format(v, type(v)) for v in surah_info.values()])
        # input()

        # print(surah_id, eng_title, arabic_lang_title, arabic_latin_title, verses_count, revelation_place, chrono_order)

    destination_path = Path('wiki_surah_infos.json')

    with destination_path.open('w') as f:
        json.dump(surah_infos, f, indent=2, ensure_ascii=False, sort_keys=False)

    print(destination_path)



if __name__ == '__main__':
    main()
