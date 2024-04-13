import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Lesson(SqlAlchemyBase):
    __tablename__ = 'lessons'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    language_1 = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("languages.id"))
    language_2 = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("languages.id"))
    picture = sqlalchemy.Column(sqlalchemy.String, nullable=True, default=None)
    who_done = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    is_open = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)
