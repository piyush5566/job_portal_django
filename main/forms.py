# main/forms.py
from django import forms
from django.core.validators import RegexValidator

class ContactForm(forms.Form):
    """
    Form for the contact page.
    Equivalent to Flask's ContactForm.
    """
    name_validator = RegexValidator(
        regex=r'^[A-Za-z\s\-\']+$',
        message='Name can only contain letters, spaces, hyphens, and apostrophes'
    )
    name = forms.CharField(
        label='Your Name',
        min_length=2,
        max_length=50,
        validators=[name_validator],
        widget=forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Your Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email', 'class': 'form-control'})
    )
    subject = forms.CharField(
        label='Subject',
        min_length=5,
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Subject', 'class': 'form-control'})
    )
    message = forms.CharField(
        label='Message',
        min_length=10,
        max_length=2000,
        widget=forms.Textarea(attrs={'placeholder': 'Leave a message here', 'style': 'height: 150px', 'class': 'form-control'})
    )
