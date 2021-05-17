from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import PasswordInput

class LoginForm(FlaskForm):
    Email_ID = StringField('Email_ID', validators=[DataRequired()])
    Password = StringField('Password', widget=PasswordInput(hide_value=False), validators=[DataRequired()])
    submit = SubmitField('Log in')

class RegistrationForm(FlaskForm):
    Email_ID = StringField('Email_ID', validators=[DataRequired()])
    user_name = StringField('user_name', validators=[DataRequired(), Length(min=2, max=20)])
    Password = StringField('Password', widget=PasswordInput(hide_value=False), validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class QueryForm(FlaskForm) :
    Title = StringField('Title')
    Year = StringField('Year')
    Artist = StringField('Artist')
    submit = SubmitField('Query')