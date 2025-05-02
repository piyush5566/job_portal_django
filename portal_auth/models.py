from django.db import models
from django.contrib.auth.hashers import make_password, check_password
# Note: For a real Django project, consider using Django's built-in User model
# or extending AbstractUser/AbstractBaseUser for more features and integration.
# This User model is a direct translation for equivalence demonstration.
# Import AbstractUser
from django.contrib.auth.models import AbstractUser

# Inherit from AbstractUser instead of models.Model
class User(AbstractUser):
    """
    User model representing all types of users in the system (Django ORM version).

    This model stores authentication information and basic user details.
    Users can have one of three roles: job_seeker, employer, or admin.

    Attributes:
        
        Inherited from AbstractUser:
            id, username, first_name, last_name, email, password,
            is_staff, is_active, is_superuser, last_login, date_joined
        Custom:
            role (CharField): User's role (job_seeker, employer, or admin)
        profile_picture (ImageField): Path to user's profile picture
        # jobs_posted: Reverse relation accessed via Job.poster or user.jobs_posted (if related_name is set)
        # applications: Reverse relation accessed via Application.applicant or user.applications (if related_name is set)
    """
    ROLE_CHOICES = [
        ('job_seeker', 'Job Seeker'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    ]

    email = models.EmailField(max_length=120, unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    # Use ImageField for images, requires Pillow installation
    # 'upload_to' specifies the subdirectory within MEDIA_ROOT
    profile_picture = models.ImageField(
        upload_to='img/profiles/', null=True, blank=True, default='img/profiles/default.jpg')

    # def set_password(self, raw_password):
    #     """
    #     Set the user's password by hashing it using Django's make_password.

    #     Args:
    #         raw_password (str): The plain text password to hash and store
    #     """
    #     self.password = make_password(raw_password)

    # def check_password(self, raw_password):
    #     """
    #     Verify if the provided password matches the stored hash using Django's check_password.

    #     Args:
    #         raw_password (str): The plain text password to check

    #     Returns:
    #         bool: True if password matches, False otherwise
    #     """
    #     return check_password(raw_password, self.password)

    # AbstractUser requires USERNAME_FIELD and REQUIRED_FIELDS
    # USERNAME_FIELD defaults to 'username', which is fine here.
    # REQUIRED_FIELDS defaults to ['email'], let's keep it explicit.
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        """String representation of the User object."""
        return f'{self.username} ({self.get_role_display()})'

    # Add verbose names for admin interface (optional but good practice)
    # Inherit Meta options from AbstractUser if needed, or define custom ones
    class Meta(AbstractUser.Meta):
        verbose_name = "User"
        verbose_name_plural = "Users"
