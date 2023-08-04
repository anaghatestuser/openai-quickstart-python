from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[validators.DataRequired(), validators.Length(min=3, max=80)])
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', validators=[validators.DataRequired(), validators.Length(min=6)])
