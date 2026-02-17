from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, ValidationError
import re

# Custom email validator that doesn't depend on email_validator package
class SimpleEmail(object):
    """
    Simple email validator that uses regex instead of email_validator package.
    More reliable for form validation without external dependencies.
    """
    def __init__(self, message=None):
        self.message = message or 'Ugyldig e-postadresse'
        
    def __call__(self, form, field):
        # Simple but effective email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, field.data):
            raise ValidationError(self.message)


class LoginForm(FlaskForm):
    email = EmailField('E-post', validators=[DataRequired()])
    password = PasswordField('Passord', validators=[DataRequired()])
    remember_me = BooleanField('Husk meg')
    submit = SubmitField('Logg inn')


class RegistrationForm(FlaskForm):
    username = StringField('Brukernavn', validators=[
        DataRequired(),
        Length(min=3, max=20)
    ])
    email = EmailField('E-post', validators=[
        DataRequired()
    ])
    password = PasswordField('Passord', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Bekreft Passord', validators=[
        DataRequired(),
        EqualTo('password', message='Passordene må være like')
    ])
    referral_code = StringField('Invitasjonskode (valgfritt)', validators=[
        Length(min=0, max=20)
    ])
    submit = SubmitField('Registrer')


class ForgotPasswordForm(FlaskForm):
    email = StringField('E-postadresse', validators=[DataRequired()])
    submit = SubmitField('Send tilbakestillingslenke')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nytt passord', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Lagre nytt passord')


class ReferralForm(FlaskForm):
    """Form for referring friends"""
    email = EmailField('Vennens e-post', validators=[
        DataRequired(message='E-post er påkrevd')
    ])
    submit = SubmitField('Send invitasjon')


class UpdateReferralCodeForm(FlaskForm):
    """Form for updating referral code during registration"""
    referral_code = StringField('Invitasjonskode (valgfritt)', validators=[
        Length(min=0, max=20)
    ])
