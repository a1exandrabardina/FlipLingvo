import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Card(SqlAlchemyBase):
    __tablename__ = 'cards'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    lesson_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("lessons.id"))
    word = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    translate = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    definition = sqlalchemy.Column(sqlalchemy.String, nullable=True)
