""" PagerMaid interface forms. """

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, DataRequired


class LoginForm(FlaskForm):
    username = StringField(u'Username', validators=[DataRequired()])
    password = PasswordField(u'Password', validators=[DataRequired()])


class SetupForm(FlaskForm):
    full_name = StringField(u'Full Name', validators=[DataRequired()])
    username = StringField(u'Full Name', validators=[DataRequired()])
    password = PasswordField(u'Full Name', validators=[DataRequired()])
    email = StringField(u'Full Name', validators=[DataRequired(), Email()])


class ModifyForm(FlaskForm):
    full_name = StringField(u'Full Name')
    username = StringField(u'Username')
    password = PasswordField(u'Password')
    email = StringField(u'Email Address', validators=[Email()])
