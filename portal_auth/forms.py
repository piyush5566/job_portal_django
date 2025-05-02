# auth/forms.py
import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
# Import your User model from where you placed it (assuming auth/models.py)
from .models import User

# --- Custom Validators (can be kept similar) ---
def validate_password_strength(password):
    """
    Validate password strength according to security requirements.
    (Same logic as Flask version, adapted for Django's ValidationError)
    """
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long', code='password_too_short')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter', code='password_no_upper')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter', code='password_no_lower')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Password must contain at least one number', code='password_no_digit')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character', code='password_no_symbol')

# --- Form Definitions ---

class RegistrationForm(forms.Form):
    """
    Form for user registration (Job Seekers and Employers).
    Equivalent to Flask's RegistrationForm.
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
        widget=forms.TextInput(attrs={'placeholder': 'Choose a username', 'autocomplete': 'username'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'name@example.com', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a password', 'autocomplete': 'new-password'}),
        min_length=8,
        max_length=72, # Django password hashers might exceed this, consider removing max_length or increasing
        validators=[validate_password_strength]
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password', 'autocomplete': 'new-password'})
    )
    # Get choices directly from the User model
    role = forms.ChoiceField(
        label='Role',
        choices=[(r[0], r[1]) for r in User.ROLE_CHOICES if r[0] != 'admin'], # Exclude admin for regular registration
        widget=forms.Select(attrs={'class': 'form-select'}) # Add Bootstrap class
    )

    def clean_email(self):
        """Validate that the email is unique."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.", code='email_exists')
        return email

    def clean(self):
        """Validate that passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.") # Use add_error for non-field specific errors tied to a field
            # raise ValidationError("Passwords do not match.", code='password_mismatch') # Or raise general validation error

        return cleaned_data


class AdminRegistrationForm(forms.Form):
    """
    Form for admin-created user registration.
    Equivalent to Flask's AdminRegistrationForm.
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
        widget=forms.TextInput(attrs={'placeholder': 'Choose a username'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'name@example.com'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a password'}),
        min_length=8,
        max_length=72,
        validators=[validate_password_strength]
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'})
    )
    # Include 'admin' choice here
    role = forms.ChoiceField(
        label='Role',
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_email(self):
        """Validate that the email is unique."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.", code='email_exists')
        return email

    def clean(self):
        """Validate that passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class LoginForm(forms.Form):
    """
    Form for user login.
    Equivalent to Flask's LoginForm.
    """
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'autocomplete': 'current-password'})
    )


class ProfileForm(forms.ModelForm):
    """
    Form for users to edit their own profile.
    Using ModelForm for easier integration with the User model.
    Equivalent to Flask's ProfileForm.
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
        widget=forms.TextInput(attrs={'class': 'form-control'}) # Add Bootstrap class
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    # Use ImageField for better image handling (requires Pillow)
    profile_picture = forms.ImageField(
        label='Profile Picture',
        required=False, # Equivalent to Optional()
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), # Allows clearing/changing
        help_text="(Optional: jpg, png, jpeg)"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'profile_picture']

    def __init__(self, *args, **kwargs):
        # Store the instance being edited to exclude it from unique checks
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean_username(self):
        """Validate that the username is unique (excluding self)."""
        username = self.cleaned_data.get('username')
        if username and self.instance:
            # Check if another user (excluding the current instance) has this username
            if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError("That username is already taken. Please choose a different one.", code='username_taken')
        return username

    def clean_email(self):
        """Validate that the email is unique (excluding self)."""
        email = self.cleaned_data.get('email')
        if email and self.instance:
            # Check if another user (excluding the current instance) has this email
            if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError("That email is already registered. Please choose a different one.", code='email_exists')
        return email

    def clean_profile_picture(self):
        """Validate file type (redundant with ImageField but good practice)."""
        picture = self.cleaned_data.get('profile_picture', False)
        if picture:
            allowed_extensions = ['jpg', 'jpeg', 'png']
            extension = picture.name.split('.')[-1].lower()
            if extension not in allowed_extensions:
                raise ValidationError("Invalid profile picture file type. Allowed: jpg, png, jpeg", code='invalid_image_type')
            # Optional: Add file size validation
            # if picture.size > MAX_UPLOAD_SIZE:
            #     raise ValidationError(f"File size cannot exceed {MAX_UPLOAD_SIZE} bytes.")
        return picture

