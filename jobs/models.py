from django.db import models
from django.utils import timezone
from django.conf import settings

class Job(models.Model):
    """
    Job model representing job listings posted by employers (Django ORM version).

    Attributes:
        id (AutoField): Primary key for the job (automatically added by Django)
        title (CharField): Job title
        description (TextField): Detailed job description
        salary (CharField): Salary information (optional)
        location (CharField): Job location
        category (CharField): Job category
        company (CharField): Company name
        company_logo (ImageField): Path to company logo
        posted_date (DateTimeField): When the job was posted
        poster (ForeignKey): Reference to the employer (User) who posted the job
        # applications: Reverse relation accessed via Application.job or job.applications (if related_name is set)
    """
    title = models.CharField(max_length=100)
    description = models.TextField()
    salary = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=50, db_index=True)
    company = models.CharField(max_length=100, db_index=True)
    # Use ImageField for images
    company_logo = models.ImageField(
        upload_to='img/company_logos/', null=True, blank=True, default='img/company_logos/default.png')
    # Use timezone.now for timezone-aware datetime
    posted_date = models.DateTimeField(default=timezone.now, db_index=True)
    # ForeignKey links to the User model.
    # on_delete=models.CASCADE mimics the 'cascade="all, delete-orphan"' behavior
    # related_name allows accessing jobs from user object like user.jobs_posted
    poster = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='jobs_posted', db_index=True)

    # Property to easily get application count
    @property
    def application_count(self):
        # Access related applications via the related_name set in Application model
        # Use Django's efficient count() method
        return self.applications.count()

    def __str__(self):
        """String representation of the Job object."""
        return f'{self.title} at {self.company}'

    class Meta:
        # Equivalent to SQLAlchemy's UniqueConstraint
        constraints = [
            models.UniqueConstraint(fields=['title', 'company', 'poster', 'location'],
                                    name='uq_job_title_company_poster_location')
        ]
        # Order jobs by posted date descending by default in queries (optional)
        ordering = ['-posted_date']
        verbose_name = "Job"
        verbose_name_plural = "Jobs"


class Application(models.Model):
    """
    Application model representing job applications submitted by job seekers (Django ORM version).

    Attributes:
        id (AutoField): Primary key for the application (automatically added by Django)
        job (ForeignKey): Reference to the job being applied for
        applicant (ForeignKey): Reference to the user applying for the job
        application_date (DateTimeField): When the application was submitted
        status (CharField): Current status of the application
        resume_path (FileField): Path to the uploaded resume file
    """
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('rejected', 'Rejected'),
        ('shortlisted', 'Shortlisted'),
        ('hired', 'Hired'),
    ]

    # related_name allows accessing applications from job object like job.applications
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='applications', db_index=True)
    # related_name allows accessing applications from user object like user.applications
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications', db_index=True)
    application_date = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='applied', db_index=True)
    # Use FileField for general file uploads like resumes
    resume_path = models.FileField(upload_to='resumes/', null=True, blank=True)

    def __str__(self):
        """String representation of the Application object."""
        # Access related fields using Django's ORM traversal
        return f'Application by {self.applicant.username} for {self.job.title}'

    class Meta:
        # Equivalent to SQLAlchemy's UniqueConstraint
        constraints = [
            models.UniqueConstraint(fields=['job', 'applicant'], name='_job_applicant_uc')
        ]
        # Order applications by date descending by default (optional)
        ordering = ['-application_date']
        verbose_name = "Application"
        verbose_name_plural = "Applications"

