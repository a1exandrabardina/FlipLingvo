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


# Основная страница
@app.route('/', defaults={'language_filter': 'Все', 'search_word': '%'}, methods=['GET', 'POST'])
@app.route('/index', defaults={'language_filter': 'Все', 'search_word': '%'}, methods=['GET', 'POST'])
@app.route('/index/<language_filter>/<search_word>', methods=['GET', 'POST'])
def index(language_filter, search_word):
    db_sess = db_session.create_session()
    # Создание фильтра в том числе на языки
    languages = db_sess.query(Language)
    form = FilterForm()
    form.language_filter.choices = [("Все", "Все"), *[(lan.id, lan.name) for lan in languages]]
    form.language_filter.data = language_filter
    # Выбор среди уроков те, которые нужно вывести в зависимости от того, зарегистрирован ли он
    if current_user.is_authenticated:
        # Выбор среди уроков те, которые нужно вывести в зависимости от того, выбран ли фильтр по языкам
        if language_filter != 'Все':
            lessons = db_sess.query(Lesson).filter(Lesson.language_1 == int(language_filter),
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(
                                                       str(search_word))),
                                                   ((Lesson.who_done == current_user.id) | (Lesson.is_open == True)))
        else:
            lessons = db_sess.query(Lesson).filter(((Lesson.who_done == current_user.id) | (Lesson.is_open == True)),
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(
                                                       str(search_word))))
    else:
        #  Выбор среди уроков те, которые нужно вывести в зависимости от того, выбран ли фильтр языка
        if language_filter != 'Все':
            lessons = db_sess.query(Lesson).filter(Lesson.language_1 == int(language_filter),
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(
                                                       str(search_word))),
                                                   Lesson.is_open == True)
        else:
            lessons = db_sess.query(Lesson).filter(Lesson.is_open == True,
                                                   (Lesson.name.like(str(search_word)) | Lesson.description.like(
                                                       str(search_word))))
    # обработка поиска по фильтру
    if form.validate_on_submit():
        search_word_ = form.search_bar.data
        # бработка запроса в зависимости от того, пустой он или нет
        if search_word_:
            search_word_ = '%' + search_word_ + '%'
        else:
            search_word_ = '%'
        return redirect('/index/' + form.language_filter.data + '/' + search_word_)
    # заплолнение строки поиска текущим запросом
    if search_word == '%':
        to_form = ""
    else:
        to_form = search_word[1:-1]
    return render_template("index.html", form=form, lessons=lessons, search_word=to_form)


# страница урока
@app.route('/lesson/<lesson_id>')
def lesson(lesson_id):
    db_sess = db_session.create_session()
    current_lesson = db_sess.query(Lesson).filter((Lesson.id == lesson_id)).first()
    # проверка на существование урока
    if not current_lesson:
        return redirect('/')
    # Проверка на доступ к текущему уроку у пользователя
    if (current_user.is_authenticated and (not current_lesson.is_open or current_lesson.who_done != current_user.id)
            or not current_lesson.is_open):
        return redirect('/')
    # составление списка карточек, входящих в текущий урок
    cards = db_sess.query(Card).filter((Card.lesson_id == lesson_id))
    return render_template("lesson.html", cards=cards)


# Страница профиля
@app.route('/profile', defaults={'language_filter': 'Все', 'search_word': '%'}, methods=['GET', 'POST'])
@app.route('/profile/<language_filter>/<search_word>', methods=['GET', 'POST'])
def profile(language_filter, search_word):
    db_sess = db_session.create_session()
    # Проверка что на страницу заходит авторизованный пользователь
    if not current_user.is_authenticated:
        return redirect('/')
    # Настройка фильтров уроков по языку
    languages = db_sess.query(Language)
    form = FilterForm()
    form.language_filter.choices = [("Все", "Все"), *[(lan.id, lan.name) for lan in languages]]
    form.language_filter.data = language_filter
    # Проверка на наличие фильтра языка
    if language_filter != 'Все':
        lessons = db_sess.query(Lesson).filter(Lesson.language_1 == int(language_filter),
                                               (Lesson.name.like(str(search_word)) | Lesson.description.like(
                                                   str(search_word))),
                                               (Lesson.who_done == current_user.id))
    else:
        lessons = db_sess.query(Lesson).filter((Lesson.who_done == current_user.id),
                                               (Lesson.name.like(str(search_word)) | Lesson.description.like(
                                                   str(search_word))))
    # обработка формы фильтров
    if form.validate_on_submit():
        search_word_ = form.search_bar.data
        if search_word_:
            search_word_ = '%' + search_word_ + '%'
        else:
            search_word_ = '%'
        return redirect('/profile/' + form.language_filter.data + '/' + search_word_)
    user = db_sess.query(User).filter((User.id == current_user.id)).first()
    # заполнение строки поиска текущим поиском
    if search_word == '%':
        to_form = ""
    else:
        to_form = search_word[1:-1]
    return render_template("profile.html", user=user, lessons=lessons, form=form, search_word=to_form)


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    # обработка формы
    if form.validate_on_submit():
        # Проверка на совпадение пароля
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        # Проверка на уникальность email
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        # Сохранение пользователя
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


# Страница входа в аккаунт
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # обработка формы входа
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        # проверка на совпадение логина и пароля
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        # обарботка ошибки
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# страница изменение пароля
@app.route('/changingpassword', methods=['GET', 'POST'])
def changingpassword():
    # проверка на то тчо на страницу заходит авторизированный пользователь
    if not current_user.is_authenticated:
        return redirect('/')
    form = ChangingPasswordForm()
    # обработка формы смены пароля
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.id == current_user.id)).first()
        # проверка на верный предыдущий пароль
        if user.check_password(form.last_password.data):
            # проверка на совпадение паролей
            if form.new_password.data != form.confirm_password.data:
                return render_template('changingpassword.html', title='Регистрация',
                                       form=form,
                                       message="Пароли не совпадают")
            # изменение пароля
            user.set_password(form.new_password.data)
            db_sess.commit()
            return redirect("/profile")
        return render_template('changingpassword.html',
                               message="Неправильный пароль",
                               form=form)
    return render_template('changingpassword.html', title='Авторизация', form=form)


# Страница изменение изображения профиля
@app.route('/changingimage', methods=['GET', 'POST'])
def changingimage():
    # Проверка на то что пользователь авторизован
    if not current_user.is_authenticated:
        return redirect('/')
    form = ChangeImageForm()
    # обработка формы изменения изображения
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.id == current_user.id)).first()
        # сохранение изображения на сервер
        f = form.picture.data
        filename = secure_filename(f.filename)
        f.save(os.path.join("C:\\\\Users\\\\dingo\\\\PycharmProjects\\\\REALPROJECT", "static", "profile", filename))
        # добавление имени изображения в базу данных
        user.picture = filename
        db_sess.commit()
        return redirect("/profile")
    return render_template('changingimage.html', title='Смена Изображения', form=form)


# Страница создания нового урока
@app.route('/createlesson', methods=['GET', 'POST'])
def create_lesson():
    # Проверка на то что пользователь авторизован
    if not current_user.is_authenticated:
        return redirect('/')
    db_sess = db_session.create_session()
    form = NewLessonForm()
    # Заполнение данных о языке
    languages = db_sess.query(Language)
    form.language_1.choices = [(lan.id, lan.name) for lan in languages]
    form.language_2.choices = [(lan.id, lan.name) for lan in languages]
    # обработка формы
    if form.validate_on_submit():
        # обработка поля приватности
        is_open = 1
        if form.is_open.data:
            is_open = 0
        # сохранение данных нового урока
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


# Страница создания карточки
@app.route('/createcard/<lesson_id>', methods=['GET', 'POST'])
def create_card(lesson_id):
    db_sess = db_session.create_session()
    # проверка на существование урока и доступ к нему у пользователя
    current_lesson = db_sess.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not current_user.is_authenticated or not current_lesson or current_lesson.who_done != current_user.id:
        return redirect('/')
    form = NewCardForm()
    # обработка формы
    if form.validate_on_submit():
        # сохранение карточки
        new_card = Card(
            word=form.word.data,
            definition=form.definition.data,
            translate=form.translate.data,
            lesson_id=lesson_id
        )
        db_sess.add(new_card)
        db_sess.commit()
        return redirect('/editlesson/' + str(lesson_id))
    return render_template('createcard.html', title='Создание новой карточки', form=form, lesson_id=lesson_id)


# Страница изменения урока
@app.route('/editlesson/<lesson_id>/<change_status>/<delete_card>/<delete_lesson>')
@app.route('/editlesson/<lesson_id>', defaults={'change_status': 0, 'delete_card': -1, 'delete_lesson': 0})
@app.route('/editlesson/<lesson_id>/<change_status>', defaults={'delete_card': -1, 'delete_lesson': 0})
@app.route('/editlesson/<lesson_id>/<change_status>/<delete_card>', defaults={'delete_lesson': 0})
def editlesson(lesson_id, change_status, delete_card, delete_lesson):
    db_sess = db_session.create_session()
    #проверка на существование урока
    current_lesson = db_sess.query(Lesson).filter((Lesson.id == lesson_id)).first()
    if not current_lesson:
        return redirect('/')
    # проверка на доступ пользователя к уроку
    if not current_user.is_authenticated or current_lesson.who_done != current_user.id:
        return redirect('/')
    # обработка удаления урока
    if delete_lesson:
        db_sess.query(Lesson).filter(Lesson.id == int(lesson_id)).delete()
        db_sess.commit()
        return redirect('/profile')
    # обработка удаления карточки
    if delete_card != -1:
        db_sess.query(Card).filter(Card.id == delete_card).delete()
        db_sess.commit()
    # обработка изменения статуса приватности
    lesson = db_sess.query(Lesson).filter(Lesson.id == int(lesson_id)).first()
    if change_status:
        lesson.is_open = abs(lesson.is_open - 1)
        db_sess.commit()
    # загрузка все карт урока
    cards = db_sess.query(Card).filter((Card.lesson_id == lesson_id))
    return render_template("editlesson.html", cards=cards, lesson=lesson)


# функция выхода из аккаунта
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# функция получения возможного перевода
@app.route('/offer_transfer/<value>/<lesson_id>')
@login_required
def offer_transfer(value, lesson_id):
    db_sess = db_session.create_session()
    # получения данных для запроса
    current_lesson = db_sess.query(Lesson).filter((Lesson.id == lesson_id)).first()
    language_code_1 = db_sess.query(Language).filter((Language.id == current_lesson.language_1)).first().lang_code
    language_code_2 = db_sess.query(Language).filter((Language.id == current_lesson.language_2)).first().lang_code
    params = {'key': "dict.1.1.20240424T093710Z.39946269ddd42240.92a69939608b880f717605415856a15b9e828818",
              "text": value, 'lang': language_code_1 + "-" + language_code_2}
    # запрос
    res = requests.get("https://dictionary.yandex.net/api/v1/dicservice.json/lookup", params=params).json()
    # проверка на пустой результат
    if res['def']:
        return '["' + res['def'][0]['tr'][0]['text'] + '"]'
    return '["Мы ничего не нашли :("]'


def main():
    db_session.global_init("db/FlipLingvo.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
    db_sess = db_session.create_session()
    db_sess.commit()
