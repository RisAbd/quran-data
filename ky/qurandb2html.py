#!/usr/bin/env python3

import sys
from pathlib import Path
import jinja2
import sqlite3
import shutil

from utils import int_to_ky_text
from db import make_session_and_engine, KySurah as Surah, Verse, Note


BISMILLAH_LITERAL = 'Мээримдүү, Ырайымдуу Аллахтын аты менен'


def main():
    import optparse

    p = optparse.OptionParser(usage='%prog [options] <db_path> <html_template_directory> <destination_directory>')

    opts, args = p.parse_args()

    db_path, html_directory, html_dest_directory = map(Path, args)
    assert db_path.is_file()
    assert html_directory.is_dir()

    if html_dest_directory.exists():
        # shutil.rmtree(html_dest_directory)
        for p in html_dest_directory.glob('*'):
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
    else:
        html_dest_directory.mkdir()

    # shutil.copytree(html_directory, html_dest_directory)
    for p in html_directory.glob('*'):
        (shutil.copytree if p.is_dir() else shutil.copy)(p, html_dest_directory / p.name)

    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath='./'))
    jinja_env.trim_blocks = True
    jinja_env.strip_blocks = True 

    index_template_path = html_dest_directory / 'index.html'
    index_template = jinja_env.get_template(str(index_template_path))

    surah_tempate_path = html_dest_directory / 'surah.html'
    surah_template = jinja_env.get_template(str(surah_tempate_path))

    # remove template file from destination html directory
    surah_tempate_path.unlink()
    index_template_path.unlink()

    Session, _ = make_session_and_engine(db_path)
    session = Session()

    surahs = session.query(Surah).order_by(Surah.number)

    # index page rendering
    with (html_dest_directory / 'index.html').open('w') as f:
        f.write(index_template.render(
            surahs=surahs,
        ))

    for s in surahs:
        verses = s.verses
        if s.bismillah_pre:
            if verses[0].text.startswith(BISMILLAH_LITERAL):
                verses[0].text = verses[0].text[len(BISMILLAH_LITERAL):].lstrip()

        surah_file_path = html_dest_directory / 'surah_{}.html'.format(s.number)

        with surah_file_path.open('w') as f:
            f.write(surah_template.render(
                surah=s,
                verses_count_text=int_to_ky_text(s.verses_count),
                BISMILLAH_LITERAL=BISMILLAH_LITERAL,     # None lets it fallback to '\ufdfd' (﷽)
            ))


if __name__ == '__main__':
    main()
