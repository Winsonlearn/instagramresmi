from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired()
        # No length restriction for login - allow email or username
    ])
    password = PasswordField("Password", validators=[
        DataRequired()
        # No length restriction for login validation
    ])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Log In")