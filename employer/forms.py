# employer/forms.py
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
# Import Job and Application models (assuming they are in 'jobs' app)
from jobs.models import Job, Application

class JobForm(forms.ModelForm):
    """
    Form for creating and editing job listings.
    Using ModelForm for easier integration with the Job model.
    Equivalent to Flask's JobForm.
    """
    salary_validator = RegexValidator(
        regex=r'^[$€£¥₹]?[\d,]+(\s*-\s*[$€£¥₹]?[\d,]+)?$',
        message='Invalid salary format (e.g., $50,000, $60k - $70k)'
    )
    title = forms.CharField(
        label='Job Title', min_length=5, max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        label='Job Description', min_length=20, max_length=5000,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )
    salary = forms.CharField(
        label='Salary', required=False, validators=[salary_validator],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., $50,000 - $60,000'})
    )
    location = forms.CharField(
        label='Location', min_length=2, max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    category = forms.CharField(
        label='Category', min_length=2, max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    company = forms.CharField(
        label='Company Name', min_length=2, max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    company_logo = forms.ImageField(
        label='Company Logo', required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="(Optional: jpg, png, jpeg)"
    )

    class Meta:
        model = Job
        # Fields that the employer/admin should fill
        fields = ['title', 'description', 'salary', 'location', 'category', 'company', 'company_logo']

    def clean_company_logo(self):
        """Validate file type (redundant with ImageField but good practice)."""
        logo = self.cleaned_data.get('company_logo', False)
        if logo:
            allowed_extensions = ['jpg', 'jpeg', 'png']
            extension = logo.name.split('.')[-1].lower()
            if extension not in allowed_extensions:
                raise ValidationError("Invalid company logo file type. Allowed: jpg, png, jpeg", code='invalid_image_type')
        return logo


class ApplicationStatusForm(forms.Form):
    """
    Form for updating job application status.
    Equivalent to Flask's ApplicationStatusForm.
    """
    # Get choices directly from the Application model
    status = forms.ChoiceField(
        label='Status',
        choices=Application.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}) # Add Bootstrap classes
    )
    # application_id = forms.IntegerField(widget=forms.HiddenInput()) # Usually not needed if ID is in URL
