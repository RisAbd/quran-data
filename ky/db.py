
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression
import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class Surah(Base):
    __tablename__ = 'surahs'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    number = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    verses_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    revelation_place = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    chronological_order = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    bismillah_pre = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    verses = relationship('Verse', order_by='Verse.number', back_populates='surah')

    __mapper_args__ = {
        'polymorphic_identity': 'surah',
    }

    def __repr__(self):
        s = sqlalchemy.inspect(self).session
        notes_count = s.query(Note).filter(Note.verse_id.in_(s.query(Verse.id).filter(Verse.surah == self).subquery())).count()
        return '<Surah(id={}, number={}, title={!r}, revelation={!r}, verses={}, notes={}, chronoorder={}, bismillah_pre={})>' \
            .format(self.id, self.number, self.title, self.revelation_place, 
                self.verses_count, notes_count, 
                self.chronological_order, 1 if self.bismillah_pre else 0)


class KySurah(Surah):
    __mapper_args__ = {
        'polymorphic_identity': 'ky_surah',
    }

    title_note = sqlalchemy.Column(sqlalchemy.String)


class Verse(Base):
    __tablename__ = 'surah_verses'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    surah_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('surahs.id'), nullable=False)
    number = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    sacdah = sqlalchemy.Column(sqlalchemy.Boolean, server_default=expression.false(), nullable=False)

    surah = relationship('Surah', back_populates='verses', enable_typechecks=False)

    notes = relationship('Note', order_by='Note.text_position', back_populates='verse')


class Note(Base):
    __tablename__ = 'surah_verse_notes'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    verse_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('surah_verses.id'), nullable=False)
    text_position = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    verse = relationship('Verse', back_populates='notes')



def make_session_and_engine(db_path):
    db_engine = sqlalchemy.create_engine('sqlite:///{}'.format(db_path))
    Session = sessionmaker()
    Session.configure(bind=db_engine)
    return Session, db_engine