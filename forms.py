from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6), DataRequired()])
    image_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6), DataRequired()])


class UserUpdateForm(FlaskForm):
    """Form for updating profile"""

    username = StringField('Username')
    email = StringField('E-mail', validators=[Email()])
    image_url = StringField('Image URL')
    header_image_url = StringField('Header Image URL')
    bio = StringField('Bio')
    
    
    password = PasswordField('Password', validators=[DataRequired()])