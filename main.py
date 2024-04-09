from flask import Flask
import sqlalchemy as sa
from data import db_session
from data.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

def main():
    db_session.global_init("db/blogs.db")
    # app.run()


if __name__ == '__main__':
    main()
    db_sess = db_session.create_session()
    db_sess.commit()
