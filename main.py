import base64
import os
from flask import Flask
from flask import redirect
from flask import render_template
from flask_login import LoginManager
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from flask_login import current_user
import sqlalchemy as sa
from data import db_session
from data.users import User
from data.lessons import Lesson
from data.cards import Card
from data.languages import Language
from forms.loginform import LoginForm
from forms.user import RegisterForm
from forms.changingimage import ChangeImageForm
from forms.changingpassword import ChangingPasswordForm
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path="/static")
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        lessons = db_sess.query(Lesson).filter(
            (Lesson.who_done == current_user.id) | (Lesson.is_open == True))
    else:
        lessons = db_sess.query(Lesson).filter(Lesson.is_open == True)
    return render_template("index.html", lessons=lessons)


@app.route('/lesson/<lesson_id>')
def lesson(lesson_id):
    db_sess = db_session.create_session()
    cards = db_sess.query(Card).filter((Card.lesson_id == lesson_id))
    return render_template("lesson.html", cards=cards)


@app.route('/profile')
def profile():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter((User.id == current_user.is_authenticated)).first()
    return render_template("profile.html", user=user)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/changingpassword', methods=['GET', 'POST'])
def changingpassword():
    form = ChangingPasswordForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.id == current_user.is_authenticated)).first()
        if user.check_password(form.last_password.data):
            if form.new_password.data != form.confirm_password.data:
                return render_template('changingpassword.html', title='Регистрация',
                                       form=form,
                                       message="Пароли не совпадают")
            user.set_password(form.new_password.data)
            db_sess.commit()
            return redirect("/profile")
        return render_template('changingpassword.html',
                               message="Неправильный пароль",
                               form=form)
    return render_template('changingpassword.html', title='Авторизация', form=form)


@app.route('/changingimage', methods=['GET', 'POST'])
def changingimage():
    form = ChangeImageForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.id == current_user.is_authenticated)).first()
        f = form.picture.data
        filename = secure_filename(f.filename)
        f.save(os.path.join("C:\\\\Users\\\\dingo\\\\PycharmProjects\\\\REALPROJECT", "static", "profile", filename))
        user.picture = filename
        db_sess.commit()
        return redirect("/profile")
    return render_template('changingimage.html', title='Смена Изображения', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/FlipLingvo.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
    db_sess = db_session.create_session()
    db_sess.commit()
