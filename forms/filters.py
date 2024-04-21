from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import Optional


class FilterForm(FlaskForm):
    language_filter = SelectField('Выбор языка', choices=[])
    search_bar = StringField('Поиск ', validators=[Optional()])
    submit = SubmitField('Подтвердить')