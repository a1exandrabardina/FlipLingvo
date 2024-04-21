from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class NewLessonForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired()])
    description = StringField("Описание", validators=[DataRequired()])
    language_1 = SelectField("Первый язык", validators=[DataRequired()])
    language_2 = SelectField("Второй язык", validators=[DataRequired()])
    colores = [('red', 'красный'), ('orange', 'ораньжевый'), ('yellow', 'желтый'), ('lime', 'светло-зеленый'),
               ('green', 'зеленый'), ('turquoise', 'бирюзовый'), ('light-blue', 'голубой'), ('blue', 'синий'),
               ('violet', 'фиолетовый'), ('pink', 'розовый')]
    color = SelectField("Выбор Цвета Обложки", validators=[DataRequired()], choices=colores)
    is_open = BooleanField('Сделать Урок Приватным')
    submit = SubmitField('Подтвердить')