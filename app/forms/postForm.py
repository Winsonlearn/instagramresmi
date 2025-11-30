from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import TextAreaField, SubmitField, StringField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional

class MediaAltTextForm(FlaskForm):
    """Form for alt text of each media item"""
    alt_text = StringField("Alt Text", validators=[
        Length(max=100, message="Alt text must be less than 100 characters")
    ])

class PostForm(FlaskForm):
    # Support multiple images/videos (carousel)
    # Note: FileRequired doesn't work well with multiple files, we'll validate in the route
    media = FileField("Photos/Videos (up to 10)", validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi'], 
                   'Images and videos only!')
    ], render_kw={"multiple": True})
    
    caption = TextAreaField("Caption (Optional)", validators=[
        Length(max=2200, message="Caption must be less than 2200 characters")
    ], render_kw={"placeholder": "Write a caption..."})
    
    location = StringField("Location (Optional)", validators=[
        Length(max=255, message="Location must be less than 255 characters")
    ], render_kw={"placeholder": "Add location"})
    
    # Alt text for each media (will be handled in JavaScript)
    alt_texts = FieldList(StringField("Alt Text", validators=[
        Length(max=100, message="Alt text must be less than 100 characters")
    ]), min_entries=0)
    
    submit = SubmitField("Share")

