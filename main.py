import base64
import os
import requests
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
from forms.filters import FilterForm
from forms.newlesson import NewLessonForm
from forms.createcard import NewCardForm
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


@app.route('/', defaults={'language_filter': 'Все', 'search_word': '%'}, methods=['GET', 'POST'])
@app.route('/index', defaults={'language_filter': 'Все', 'search_word': '%'}, methods=['GET', 'POST'])
@app.route('/index/<language_filter>/<search_word>', methods=['GET', 'POST'])
def index(language_filter, search_word):
    db_sess = db_session.create_session()
    languages = db_sess.query(Language)
    form = FilterForm()
    form.language_filter.choices = [("Все", "Все"), *[(lan.id, lan.name) for lan in languages]]
    form.language_filter.data = language_filter
    print(search_word)
    if current_user.is_authenticated:
        if language_filter != 'Все':
            lessons = db_sess.query(Lesson).filter(Lesson.language_1 == int(language_filter),
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(str(search_word))),
                                                   ((Lesson.who_done == current_user.id) | (Lesson.is_open == True)))
        else:
            lessons = db_sess.query(Lesson).filter(((Lesson.who_done == current_user.id) | (Lesson.is_open == True)),
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(str(search_word))))
    else:
        if language_filter != 'Все':
            lessons = db_sess.query(Lesson).filter(Lesson.language_1 == int(language_filter),
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(str(search_word))),
                                                   Lesson.is_open == True)
        else:
            lessons = db_sess.query(Lesson).filter(Lesson.is_open == True,
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(str(search_word))))
    if form.validate_on_submit():
        search_word_ = form.search_bar.data
        if search_word_:
            search_word_ = '%' + search_word_ + '%'
        else:
            search_word_ = '%'
        return redirect('/index/' + form.language_filter.data + '/' + search_word_)
    if search_word == '%':
        to_form = ""
    else:
        to_form = search_word[1:-1]
    return render_template("index.html", form=form, lessons=lessons, search_word=to_form)


@app.route('/lesson/<lesson_id>')
def lesson(lesson_id):
    db_sess = db_session.create_session()
    current_lesson = db_sess.query(Lesson).filter((Lesson.id == lesson_id)).first()
    if not current_lesson:
        return redirect('/')
    if current_user.is_authenticated:
        if not current_lesson.is_open or current_lesson.who_done != current_user.id:
            return redirect('/')
    else:
        if not current_lesson.is_open:
            return redirect('/')
    cards = db_sess.query(Card).filter((Card.lesson_id == lesson_id))
    return render_template("lesson.html", cards=cards)


@app.route('/profile', defaults={'language_filter': 'Все', 'search_word': '%'}, methods=['GET', 'POST'])
@app.route('/profile/<language_filter>/<search_word>', methods=['GET', 'POST'])
def profile(language_filter, search_word):
    db_sess = db_session.create_session()
    if not current_user.is_authenticated:
        return redirect('/')
    languages = db_sess.query(Language)
    form = FilterForm()
    form.language_filter.choices = [("Все", "Все"), *[(lan.id, lan.name) for lan in languages]]
    form.language_filter.data = language_filter
    print(search_word)
    if language_filter != 'Все':
        lessons = db_sess.query(Lesson).filter(Lesson.language_1 == int(language_filter),
                                               (Lesson.name.like(str(search_word)) | Lesson.description.like(str(search_word))),
                                               (Lesson.who_done == current_user.id))
    else:
        lessons = db_sess.query(Lesson).filter((Lesson.who_done == current_user.id),
                                               (Lesson.name.like(str(search_word)) | Lesson.description.like(str(search_word))))
    if form.validate_on_submit():
        search_word_ = form.search_bar.data
        if search_word_:
            search_word_ = '%' + search_word_ + '%'
        else:
            search_word_ = '%'
        return redirect('/profile/' + form.language_filter.data + '/' + search_word_)
    user = db_sess.query(User).filter((User.id == current_user.id)).first()
    if search_word == '%':
        to_form = ""
    else:
        to_form = search_word[1:-1]
    return render_template("profile.html", user=user, lessons=lessons, form=form, search_word=to_form)


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
        user = db_sess.query(User).filter((User.id == current_user.id)).first()
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
        user = db_sess.query(User).filter((User.id == current_user.id)).first()
        f = form.picture.data
        filename = secure_filename(f.filename)
        f.save(os.path.join("C:\\\\Users\\\\dingo\\\\PycharmProjects\\\\REALPROJECT", "static", "profile", filename))
        user.picture = filename
        db_sess.commit()
        return redirect("/profile")
    return render_template('changingimage.html', title='Смена Изображения', form=form)


@app.route('/createlesson', methods=['GET', 'POST'])
def create_lesson():
    if not current_user.is_authenticated:
        return redirect('/')
    db_sess = db_session.create_session()
    languages = db_sess.query(Language)
    form = NewLessonForm()
    form.language_1.choices = [(lan.id, lan.name) for lan in languages]
    form.language_2.choices = [(lan.id, lan.name) for lan in languages]
    if form.validate_on_submit():
        is_open = 1
        if form.is_open.data:
            is_open = 0
        new_lesson = Lesson(
            who_done=current_user.id,
            name=form.name.data,
            description=form.description.data,
            language_1=form.language_1.data,
            language_2=form.language_2.data,
            picture=form.color.data,
            is_open=is_open
        )
        db_sess.add(new_lesson)
        db_sess.commit()
        return redirect('/editlesson/' + str(new_lesson.id))
    return render_template('createlesson.html', title='Создание нового урока', form=form)


@app.route('/createcard/<lesson_id>', methods=['GET', 'POST'])
def create_card(lesson_id):
    if not current_user.is_authenticated:
        return redirect('/')
    form = NewCardForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        new_card = Card(
            word=form.word.data,
            definition=form.definition.data,
            translate=form.translate.data,
            lesson_id=lesson_id
        )
        db_sess.add(new_card)
        db_sess.commit()
        return redirect('/editlesson/' + str(lesson_id))
    return render_template('createcard.html', title='Создание новой карточки', form=form)


@app.route('/editlesson/<lesson_id>/<change_status>/<delete_card>/<delete_lesson>')
@app.route('/editlesson/<lesson_id>', defaults={'change_status': 0, 'delete_card': -1, 'delete_lesson': 0})
@app.route('/editlesson/<lesson_id>/<change_status>', defaults={'delete_card': -1, 'delete_lesson': 0})
@app.route('/editlesson/<lesson_id>/<change_status>/<delete_card>', defaults={'delete_lesson': 0})
def editlesson(lesson_id, change_status, delete_card, delete_lesson):
    db_sess = db_session.create_session()
    current_lesson = db_sess.query(Lesson).filter((Lesson.id == lesson_id)).first()
    if not current_lesson:
        return redirect('/')
    if not current_user.is_authenticated or current_lesson.who_done != current_user.id:
        return redirect('/')
    if delete_lesson:
        db_sess.query(Lesson).filter(Lesson.id == int(lesson_id)).delete()
        db_sess.commit()
        return redirect('/profile')
    if delete_card != -1:
        db_sess.query(Card).filter(Card.id == delete_card).delete()
        db_sess.commit()
    lesson = db_sess.query(Lesson).filter(Lesson.id == int(lesson_id)).first()
    if change_status:
        lesson.is_open = abs(lesson.is_open - 1)
        db_sess.commit()
    cards = db_sess.query(Card).filter((Card.lesson_id == lesson_id))
    return render_template("editlesson.html", cards=cards, lesson=lesson)


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
