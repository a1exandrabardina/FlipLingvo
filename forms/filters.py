from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired


class FilterForm(FlaskForm):
    language_filter = SelectField('Выбор языка', choices=[])
    search_bar = StringField()
    submit = SubmitField('Подтвердить')