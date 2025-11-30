from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length, EqualTo, Email

class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    submit = SubmitField("Send Reset Link")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[
        DataRequired(),
        EqualTo("confirm", message='Passwords must match'),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm = PasswordField("Confirm New Password", validators=[
        DataRequired(),
        Length(min=8)
    ])
    submit = SubmitField("Reset Password")


