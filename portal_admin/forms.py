# admin/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
# Import User model (assuming it's in 'auth' app)
from portal_auth.models import User

class UserEditForm(forms.ModelForm):
    """
    Form for administrators to edit user details.
    Using ModelForm for easier integration.
    Equivalent to Flask's UserEditForm.
    """
    username_validator = RegexValidator(
        regex=r'^[A-Za-z0-9_]+$',
        message='Username can only contain letters, numbers, and underscores'
    )
    username = forms.CharField(
        label='Username',
        max_length=50,
        min_length=3,
        validators=[username_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    # Include 'admin' choice here
    role = forms.ChoiceField(
        label='Role',
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

    def __init__(self, *args, **kwargs):
        # Store the instance being edited to exclude it from unique checks
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean_username(self):
        """Validate that the username is unique (excluding self)."""
        username = self.cleaned_data.get('username')
        if username and self.instance:
            if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError("That username is already taken.", code='username_taken')
        return username

    def clean_email(self):
        """Validate that the email is unique (excluding self)."""
        email = self.cleaned_data.get('email')
        if email and self.instance:
            if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError("That email is already registered.", code='email_exists')
        return email

