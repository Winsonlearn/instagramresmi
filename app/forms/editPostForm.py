from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Length

class EditPostForm(FlaskForm):
    caption = TextAreaField("Caption", validators=[
        Length(max=2200, message="Caption must be less than 2200 characters")
    ])
    submit = SubmitField("Update Post")

