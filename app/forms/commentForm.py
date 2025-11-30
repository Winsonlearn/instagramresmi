from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class CommentForm(FlaskForm):
    content = TextAreaField("Add a comment...", validators=[
        DataRequired(message="Comment cannot be empty"),
        Length(max=2200, message="Comment must be less than 2200 characters")
    ])
    submit = SubmitField("Post")

