from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, InputRequired, ValidationError
from fuprox.models import User
from flask import flash


class RegisterForm(FlaskForm):
    key = StringField("Activation Key")
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=12), ])
    password = PasswordField("Password", validators=[DataRequired(), EqualTo('confirm_password', message='Passwords do '
                                                                                                         'not match')])
    confirm_password = PasswordField("Confirm Password")
    submit = SubmitField("Activate Application")

    # validation  for checking if the username
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username Already Taken. Please Choose Another One")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remmember = BooleanField("Remember me")
    submit = SubmitField("Login")


class PasswordCode(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Verification Code")


class Code(FlaskForm):
    code = StringField("Enter Code", validators=[DataRequired()])
    submit = SubmitField("Send Verification Code")


class Passwords(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired(), EqualTo('confirm_password', message='Passwords do '
                                                                                                         'not match')])
    confirm_password = PasswordField("Confirm Password")
    submit = SubmitField("Change Password")


class WallpaperForm(FlaskForm):
    picture = FileField("Wallpaper", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("Upload Wallpaper")


class LogoForm(FlaskForm):
    logo = FileField("Logo", validators=[FileAllowed(["jpg", "png"])])
    upload = SubmitField("Upload Logo")


# form for request user toe nter email for reset
class ResetRequest(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    submit = SubmitField("Request Email Reset")

    # validate password
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            flash("Email not found please Create an Account")


# form to confirm password
class ResetPassword(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired(), Length(min=2, max=12)])
    verify = PasswordField("Repeat Password", validators=[DataRequired(), Length(min=2, max=12)])
    submit = SubmitField("Request Email Reset")


class TellerForm(FlaskForm):
    number = StringField("Teller Number", validators=[DataRequired()])
    service = StringField("Service", validators=[DataRequired()])
    users = StringField('User', validators=[DataRequired()])
    submit = SubmitField("Submit")


class ServiceForm(FlaskForm):
    name = StringField("Service Name", validators=[DataRequired()])
    teller = StringField("Teller Number", validators=[DataRequired()])
    code = StringField("Initials", validators=[DataRequired()])
    icon = StringField('Service Icon', validators=[DataRequired()])
    visible = RadioField('Available Online', choices=[('True', 'Yes'), ('False', 'No')])
    active = RadioField('Active For booking', choices=[('True', 'Yes'), ('False', 'No')])
    is_special = RadioField('Specialist', choices=[('True', 'Yes'), ('False', 'No')])
    submit = SubmitField("Add Service")


class SolutionForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    topic = StringField("Topic", validators=[DataRequired()])
    solution = TextAreaField("Solution", validators=[DataRequired()])
    submit = SubmitField("Add Solution")


class ActivateForm(FlaskForm):
    # address = StringField("Server Address", validators=[DataRequired()])
    key = StringField("Key", validators=[DataRequired()])
    submit = SubmitField("Activate Branch Applications")


class TicketResetForm(FlaskForm):
    # address = StringField("Server Address", validators=[DataRequired()])
    Time = StringField("Key", validators=[DataRequired()])
    reset = RadioField('Should the tickets reset?', choices=[('True', 'Yes'), ('False', 'No')])
    submit = SubmitField("Activate Branch Applications")


class PhraseForm(FlaskForm):
    phrase = StringField("Phrase", validators=[DataRequired()])
    type = RadioField("Callout final phrase", validators=[DataRequired()], choices=["Service Name",
                                                                                    "Counter Number"])
    submit = SubmitField("Add Phrase")


class DeleteWallpaper(FlaskForm):
    submit = SubmitField("Delete Wallpaper")


class ReportForm(FlaskForm):
    format = RadioField("Format", validators=[DataRequired()], Type=str, choices=["PDF", "Excel"])
    type = SelectField("Type", validators=[DataRequired()], Type=str, choices=["Bookings", "Branch", "Payments", "All"])
    period = SelectField("Period", validators=[DataRequired()], Type=str,
                         choices=["Daily", "Weekly", "Monthly", "Yearly", "All"])
    duration = SelectField("Duration", validators=[DataRequired()], Type=str,
                           choices=["Daily", "Weekly", "Monthly", "Yearly", "All"])
    week = SelectField("Week", validators=[DataRequired()], Type=str, choices=["One", "Two", "Three", "Four"])
    monthly = SelectField("Monthly", validators=[DataRequired()], Type=str,
                          choices=["January", "February", "March", "April", "May", "June", "July", "August",
                                   "September", "October", "November", "December"])
    submit = SubmitField("Generate Report")


# class RegisterForm(FlaskForm):
#     username = StringField("Username", validators=[DataRequired(), Length(min=2, max=12)])
#     email = StringField("Email", validators=[DataRequired(), Email()])
#     password = PasswordField("Password",
#                              validators=[DataRequired(), EqualTo('confirm_password', message='Passwords must match')])
#     confirm_password = PasswordField("Confirm Password")
#     submit = SubmitField("Register")

#     # validation  for checking if the username
#     def validate_username(self, username):
#         user = User.query.filter_by(username=username.data).first()
#         if user:
#             raise ValidationError("Username Already Taken. Please Choose Another One")

#     # validation from checking the email
#     def validate_email(self, email):
#         email = User.query.filter_by(email=email.data).first()
#         if email:
#             raise ValidationError("Email Already Taken. Please Choose Another One")


class AddUser(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=12), ])
    email = StringField("Email", validators=[DataRequired(), Email()])
    teller = StringField("Teller", validators=[DataRequired()])
    password = PasswordField("Password",
                             validators=[DataRequired(), EqualTo('confirm_password', message='Passwords must match')])
    specialist = RadioField('Specialist', choices=[('True', 'Yes'), ('False', 'No')])
    confirm_password = PasswordField("Confirm Password")
    submit = SubmitField("Register")

    # validation  for checking if the username
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username Already Taken. Please Choose Another One")

    # validation from checking the email
    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError("Email Already Taken. Please Choose Another One")


class EditUsers(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=12), ])
    email = StringField("Email", validators=[DataRequired(), Email()])
    teller = StringField("teller", validators=[DataRequired()])
    specialist = RadioField('Specialist', choices=[('True', 'Yes'), ('False', 'No')])
    password = PasswordField("Password",
                             validators=[DataRequired(), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField("Confirm Password")
    submit = SubmitField("Edit User")
