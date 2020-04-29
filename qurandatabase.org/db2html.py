#!/usr/bin/env python3

import sys
from pathlib import Path
import jinja2
import sqlite3
import shutil


BISMILLAH_LITERAL = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'


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

    surah_tempate_path = html_dest_directory / 'surah.html'
    with surah_tempate_path.open() as f:
        surah_template = jinja2.Template(f.read())


    index_template_path = html_dest_directory / 'index.html'
    with index_template_path.open() as f:
        index_template = jinja2.Template(f.read())

    # remove template file from destination html directory
    surah_tempate_path.unlink()
    index_template_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        surahs = list(map(dict, c.execute('select * from surahs order by number')))

        # index page rendering
        with (html_dest_directory / 'index.html').open('w') as f:
            f.write(index_template.render(
                surahs=surahs,
            ))

        # page for every surah rendering
        for s in surahs:
            verses = list(map(dict, c.execute('select * from surah_verses where surah_id = ? order by number', (s['id'], ))))
            s['verses'] = verses
            if s['bismillah_pre']:
                fv = verses[0]
                if fv['text'].startswith(BISMILLAH_LITERAL):
                    text_without_bismillah = fv['text'][len(BISMILLAH_LITERAL):].lstrip()
                    fv['text'] = text_without_bismillah

            surah_file_path = html_dest_directory / 'surah_{}.html'.format(s['number'])
            
            with surah_file_path.open('w') as f:
                f.write(surah_template.render(
                    surah=s,
                    BISMILLAH_LITERAL=None,     # let it fallback to '\ufdfd' (﷽)
                ))


if __name__ == '__main__':
    main()
