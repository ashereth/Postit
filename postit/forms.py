from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField, TextAreaField, URLField, PasswordField
from wtforms.validators import InputRequired, NumberRange, Email, Length, EqualTo

#create a class for the form to create a post
class PostForm(FlaskForm):
    #each post should have a title and a body
    title = StringField("Title", validators=[InputRequired()])
    body = StringField("Body", validators=[InputRequired()])

    submit = SubmitField("Post it")


#form for user signups
class RegisterForm(FlaskForm):
    # Email() validator makes sure the email provided is a valid email
    email = StringField("Email", validators=[InputRequired(), Email()])
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField(
        "Password", 
        validators=[InputRequired(),
                    Length(
                        min=4, 
                        message="Your password must be at least 4 characters long."
                        )
                    ]
                )
    confirm_password = PasswordField(
        "Confirm password", 
        validators=[InputRequired(),
                    EqualTo(#validator to make sure the passwords match
                        "password", 
                        message="Please make sure your passwords match."
                        )
                    ]
                )
    submit = SubmitField("Register")


#create a form for loggin in
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")