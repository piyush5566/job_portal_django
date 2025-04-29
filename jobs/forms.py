# jobs/forms.py
from django import forms
from django.core.exceptions import ValidationError

class ApplicationForm(forms.Form):
    """
    Form for submitting job applications.
    Equivalent to Flask's ApplicationForm.
    """
    resume = forms.FileField(
        label='Upload Resume',
        help_text="PDF, DOC, or DOCX only.",
        widget=forms.FileInput(attrs={'class': 'form-control'}) # Add Bootstrap class
    )

    def clean_resume(self):
        """Validate resume file type."""
        resume = self.cleaned_data.get('resume', False)
        if resume:
            allowed_extensions = ['pdf', 'doc', 'docx']
            extension = resume.name.split('.')[-1].lower()
            if extension not in allowed_extensions:
                raise ValidationError("Invalid file type. PDF, DOC, or DOCX only!", code='invalid_resume_type')
            # Optional: Add file size validation
            # if resume.size > MAX_RESUME_SIZE:
            #     raise ValidationError(f"File size cannot exceed {MAX_RESUME_SIZE} bytes.")
        return resume

