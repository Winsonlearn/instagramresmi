from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length, Email

class SignupForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), 
        Length(min=5, max=30, message='Username must be between 5 and 30 characters')
    ])
    email = EmailField("Email", validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    fullname = StringField("Fullname", validators=[
        DataRequired(), 
        Length(min=2, max=32, message='Full name must be between 2 and 32 characters')
    ])
    password = PasswordField("Password", validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters')
    ])
    agreement = BooleanField("I agree", validators=[
        DataRequired(message='You must agree to the terms')
    ])
    submit = SubmitField("Sign Up")