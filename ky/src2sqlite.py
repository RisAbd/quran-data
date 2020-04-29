#!/usr/bin/env python3

import typing as T
import re
from pathlib import Path
import itertools as IT, functools as FT

from bs4 import BeautifulSoup

from db import Base, KySurah as Surah, Verse, Note, make_session_and_engine

from utils import ky_number_text_to_int, load_meta, int_to_ky_text, infinite_numbers_gen


def main():

    import optparse

    p = optparse.OptionParser(usage='%prog [options] <src_dir> <db_path>')

    opts, args = p.parse_args()

    src_dir, db_path = map(Path, args)
    assert src_dir.is_dir()
    assert not db_path.exists()

    Session, db_engine = make_session_and_engine(db_path)
    Base.metadata.create_all(db_engine)
    session = Session()

    title_regexp = re.compile(r'\s*(\d+)\s*(?:-|–)\s*(?:\w+),?.?\s*(?:“|«|\")?\s*((?:\'|`|[^\d\W])+\s*(?:`|[^\d\W])+)\s*(?:\d*)\s*(?:”|»|\")?', re.UNICODE)


    BISMILLAH_LITERALS = {'Мээримдүү, Ырайымдуу Аллахтын аты менен', 'Ырайымдуу, Мээримдүү Аллахтын аты менен'}

    surah_infos = load_meta()

    note_id_func = FT.partial(next, infinite_numbers_gen())


    def link_positions(text) -> T.Tuple[str, T.List[T.Tuple[int, int]]]:
        """
            'Some{1} text with links{2} in it{3}!' -> ('Some text with links in it!', [(4, 1), (20, 2), (26, 3)])
        """
        chunks = re.split(r'(\{\d+\})', text)  # ['Some', '{1}', ' text with links', '{2}', ' in it', '{3}', '!']

        text_chunks = []
        links = []
        for i, ch in enumerate(chunks):
            if i % 2 == 0:
                text_chunks.append(ch)
            else:
                # (index, link_id)
                links.append((sum(map(len, text_chunks)), int(ch[1:-1])))

        return ''.join(text_chunks), links


    for findex, p in enumerate(sorted(src_dir.glob('suro_*.html'), key=lambda i: int(''.join(ch for ch in i.name if ch.isdigit())))):
        
        with p.open() as f:
            soup = BeautifulSoup(f.read(), features='lxml')

            # note_links = soup.find_all('a', {'class': 'sdfootnoteanc'})
            # assert len(soup.find_all('div', {'class': 'hidden'})) == 1
            notes_container = soup.select_one('div.hidden')

            def get_link_content(link_el):
                content_el = notes_container.select_one('div{} > p'.format(link_el['href'][:-3]))
                # assert len(content_el.find_all('a')) == 1
                content_el.select_one('a').decompose()
                # assert len(content_el.find_all('sup')) == 1, link_el['href']
                for el in content_el.select('sup'):
                    el.decompose()
                return ' '.join(content_el.text.split())

            # title parsing
            title_container = soup.find('div', {'class': 'title-cont'})
            main_title = title_container.select_one('div.title-parent > div.title-center')
            # assert len(main_title.select('a')) in (0, 1), p.name
            title_note_link = main_title.select_one('a')
            # assert not title_note_link or title_note_link['name'] != '_GoBack'
            title_note_content = get_link_content(title_note_link) if title_note_link else None
            # print(p, repr(title_note_content))
            # continue


            title = main_title.text
            suro_num_literal, title = title_regexp.match(title).groups()
            title = ' '.join(title.split())
            surah_num = int(suro_num_literal)
            # print(surah_num, title)

            surah_info = surah_infos[surah_num-1]

            raw_kek = [i.text for i in title_container.find_all('p', recursive=False)]
            kek = [' '.join(i.split()).rstrip('.!') for i in raw_kek if 'бөлүм' not in i and i.strip()]
            
            has_bismillah_pre = BISMILLAH_LITERALS.intersection(kek)
            assert surah_num not in (1, 9) or not has_bismillah_pre, kek
            assert surah_num in (1, 9) or has_bismillah_pre, kek

            kek = [i for i in kek if i not in BISMILLAH_LITERALS]

            assert len(kek) in (0, 1), (p, surah_num, title, kek)
            (info, ) = kek
            assert '.' in info
            revelation_place, ayat_number_text = [i.strip().capitalize() for i in info.split('.')]
            assert {'Меккеде': 'Makkah', 'Мединада': 'Madinah'}[revelation_place.split()[0]] == surah_info['revelation_place']
            # print('\t', revelation_place, ayat_number_text)
            revelation_place = revelation_place.split()[0][:-2]

            # todo: check ayat_number_text
            ayattan_turat_literal = 'айаттан турат'
            assert ayat_number_text.endswith(ayattan_turat_literal), repr(ayat_number_text)
            ayat_number_text = ayat_number_text[:-len(ayattan_turat_literal)].rstrip()

            ayat_number = ky_number_text_to_int(ayat_number_text)

            assert ayat_number == surah_info['verses_count'], (ayat_number_text, '->', ayat_number, '!=', surah_info['verses_count'])
            assert int_to_ky_text(ayat_number).capitalize() == ayat_number_text, (int_to_ky_text(ayat_number).capitalize(), ayat_number_text)
            # print(ky_to_int_vals)


            # content parsing
            content_lists = soup.find_all('ol')
            # content_lines = soup.find_all('li')
            content_lines = IT.chain.from_iterable(ol.find_all('li') for ol in content_lists)
            # assert len(list(content_lines)) == len(soup.find_all('li'))


            content_lines = list(content_lines)
            # contains_ayah_number_regexp = re.compile(r'^\d+\.', re.UNICODE)
            # assert not any(contains_ayah_number_regexp.match(l) for l in content_lines)
            cll = len(content_lines)

            assert cll == ayat_number, (cll, ayat_number)

            def process_content_line(el):
                link_contents = []
                i = 0
                for link in el.find_all('a', {'class': 'sdfootnoteanc'}):
                    link_cont = get_link_content(link)
                    if link_cont:
                        link_contents.append(link_cont)
                        link.replace_with('{{{}}}'.format(i))
                        i += 1
                    else:
                        print('\tempty note:', surah_num, title, link['href'])
                        link.decompose()
                text = ' '.join(el.text.split())
                text, notes = link_positions(text)
                return text, [(str_index, link_contents[i]) for str_index, i in notes]

            verses = list(map(process_content_line, content_lines))

            surah = Surah(
                number=surah_info['number'],
                title=title,
                verses_count=ayat_number,
                revelation_place=revelation_place,
                chronological_order=surah_info['chronological_order'],
                bismillah_pre=bool(has_bismillah_pre),
                title_note=title_note_content,
                )

            def make_verse(index, verse_text, notes):
                verse = Verse(number=index+1, text=verse_text)
                verse.notes = [Note(text_position=str_index, text=text) for str_index, text in notes]
                return verse

            surah.verses = [make_verse(i, t, n) for i, (t, n) in enumerate(verses)]

            session.add(surah)
            session.commit()

            print(surah)
            assert surah.id == surah_info['number'] == surah.number == findex+1




if __name__ == '__main__':
    main()
