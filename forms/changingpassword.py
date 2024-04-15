from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired


class ChangingPasswordForm(FlaskForm):
    last_password = PasswordField('Пароль', validators=[DataRequired()])
    new_password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')