#!/usr/bin/env python3

import csv
import sqlite3
from pathlib import Path
import itertools as IT, operator as OP
import json


BISMILLAH_LITERAL = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'


def load_meta(path=Path(__file__).absolute().parent.parent / 'wiki_surah_infos.json'):
    with path.open() as f:
        return json.load(f)


def fill_database(path, surah_infos):
    with sqlite3.connect(path) as conn:
        c = conn.cursor()
        c.executescript('''
create table surahs (
    id INTEGER PRIMARY KEY, 
    number INTEGER NOT NULL, 
    title TEXT NOT NULL,
    verses_count INTEGER NOT NULL,
    revelation_place TEXT NOT NULL,
    chronological_order INTEGER NOT NULL,
    bismillah_pre BOOLEAN NOT NULL
);

create table surah_verses (
    id INTEGER PRIMARY KEY,
    surah_id INTEGER NOT NULL ,
    number INTEGER NOT NULL,
    text TEXT NOT NULL,
    sacdah BOOLEAN DEFAULT 0,
    FOREIGN KEY (surah_id) REFERENCES surahs(id)
);

create table surah_verse_notes (
    id INTEGER PRIMARY KEY,
    verse_id INTEGER NOT NULL,
    text_position INTEGER NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (verse_id) REFERENCES surah_verses(id)
);
''')

        # surah_insert_values = (
        #     (s['number'], s['arabic_title'],
        #      s['verses_count'], s['revelation_place'],
        #      s['chronological_order'], )
        #     for s in surah_infos
        # )

        for s in surah_infos:
            c.execute('''
insert into surahs (
    number, title, verses_count,
    revelation_place, chronological_order,
    bismillah_pre
) values (?, ?, ?, ?, ?, ?)
''',        (s['number'], s['arabic_title'], 
             s['verses_count'], s['revelation_place'],
             s['chronological_order'], s['bismillah_pre']), )
            insert_id = c.lastrowid
            assert insert_id == s['number']
            s['_db_id'] = insert_id

        def surah_verses_values():
            for s in surah_infos:
                sid = s['_db_id']
                for i, text in enumerate(s['verses'], 1):
                    yield (sid, i, text)

        c.executemany(
            'insert into surah_verses (surah_id, number, text) values (?, ?, ?)',
            surah_verses_values()
        )

        c.executemany(
            'update surah_verses set sacdah = 1 where surah_id = ? and number = ?',
            [
                (7, 206),   # el-A'raf
                (13, 15),   # er-Ra'd
                (16, 49),   # en-Nahl
                (17, 107),   # el-İsrâ
                (19, 58),   # Meryem
                (22, 18),   # el-Hac
                (25, 60),   # el-Furkân
                (27, 25),   # en-Neml
                (32, 15),   # es-Secde
                (38, 24),   # Sâd
                (41, 37),   # Fussilet
                (53, 62),   # en-Necm
                (84, 21),   # el-İnşikâk
                (96, 19),   # Alak
            ]
        )



def main():

    import optparse

    p = optparse.OptionParser(usage='usage: %prog [options] <input_csv> <output_sqlite>')

    p.add_option('-i', '--input', '--csv', help='Input CSV file')
    p.add_option('-o', '--output', '--db', help='Output sqlite3 database destination')

    opts, args = p.parse_args()

    args_it = iter(args)

    csv_path = Path(opts.input or next(args_it))
    assert csv_path.is_file(), 'csv_path is not valid file: %r' % csv_path

    db_path = Path(opts.input or next(args_it))
    assert not db_path.exists(), 'db_path already exists: %r' % db_path

    print(csv_path, db_path)

    surah_that_should_start_with_bismillah = set(range(1, 115))
    surah_that_should_start_with_bismillah.difference_update({1, 9})

    surah_infos = load_meta();

    surah_texts = []

    with csv_path.open(newline='') as csvf:
        csv_reader = csv.reader(csvf)
        header_line = next(csv_reader)
        for surah_id, lines in IT.groupby(csv_reader, OP.itemgetter(1)):
            surah_id = int(surah_id)
            starts_with_bismillah = False
            surah_info = surah_infos[surah_id-1]
            assert surah_info['number'] == surah_id
            
            verses = []

            for _, _, verse_id, text in lines:
                verse_id = int(verse_id)
                if verse_id == 1 and surah_id != 1 and text.startswith(BISMILLAH_LITERAL):
                    # exclude Fatihah (1.surah) (bismillah should(?) go as plain text)
                    # exclude Taubah (9.surah) (no bismillah at start of this surah)
                    surah_that_should_start_with_bismillah.remove(surah_id)
                    starts_with_bismillah = True
                    # text = text[len(BISMILLAH_LITERAL):].lstrip()
                verses.append(text)

            surah_info['bismillah_pre'] = starts_with_bismillah

            # print(surah_info, len(verses))
            assert len(verses) == surah_info['verses_count']

            surah_info['verses'] = verses

    assert not surah_that_should_start_with_bismillah, 'should be empty: %r' % surah_that_should_start_with_bismillah

    fill_database(db_path, surah_infos)



if __name__ == '__main__':
    main()
