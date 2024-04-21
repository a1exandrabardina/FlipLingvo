from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class NewCardForm(FlaskForm):
    word = StringField("Слово", validators=[DataRequired()])
    definition = StringField("Описание", validators=[DataRequired()])
    translate = StringField("Перевод", validators=[DataRequired()])
    submit = SubmitField('Подтвердить')