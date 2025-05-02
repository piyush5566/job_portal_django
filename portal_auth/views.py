# auth/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import logging # Import logging

# Import forms and models from the current app
from .forms import RegistrationForm, LoginForm, ProfileForm
from .models import User

logger = logging.getLogger(__name__) # Get logger for this module

# --- Decorators (Can be placed here or in a separate decorators.py) ---
# (role_required decorator remains the same)
def role_required(*roles):
    """
    Decorator for views that requires the user to have one of the specified roles.
    Requires @login_required to be used first or included.
    """
    def decorator(view_func):
        @login_required # Ensure user is logged in first
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.role not in roles:
                # Log permission denial
                logger.warning(f"Permission denied: User {request.user.id} (Role: {request.user.role}) attempted to access role-restricted view requiring {roles}.")
                messages.error(request, 'You do not have permission to access this page.')
                # Redirect to a default page, e.g., the main index
                return redirect('main:index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# --- Views ---

def register_view(request):
    """
    Handle user registration (Job Seekers and Employers).
    Equivalent to Flask's register route.
    """
    if request.user.is_authenticated:
        return redirect('main:index')

    logger.info("Registration page accessed.")
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            logger.info(f"Registration form submitted for email: {email}, username: {username}")
            try:
                # Check if email already exists (case-insensitive)
                if User.objects.filter(email__iexact=email).exists():
                    logger.warning(f"Registration failed: Email {email} already registered.")
                    messages.error(request, 'An account with this email already exists.')
                else:
                    user = User(
                        username=username,
                        email=email,
                        role=form.cleaned_data['role']
                        # Default profile picture is handled by the model's default
                    )
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    logger.info(f"New user registered: ID {user.id}, Email {email}, Role {user.role}")
                    messages.success(request, 'Registration successful! Please login.')
                    return redirect('portal_auth:login')
            except Exception as e:
                logger.error(f"Registration failed due to an unexpected error for email {email}: {str(e)}")
                messages.error(request, f'Registration failed due to an unexpected error.')
        else:
            # Log validation errors
            logger.warning(f"Registration form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                 for error in errors:
                     messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = RegistrationForm()
    return render(request, 'portal_auth/register.html', {'form': form})


def login_view(request):
    """
    Handle user login.
    Equivalent to Flask's login route.
    """
    if request.user.is_authenticated:
        return redirect('main:index')

    logger.info("Login page accessed.")
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remote_addr = request.META.get('REMOTE_ADDR', 'Unknown IP')
            logger.info(f"Login attempt for email: {email} from IP: {remote_addr}")
            try:
                # Case-insensitive email lookup
                user = User.objects.get(email__iexact=email)
                if user.check_password(password):
                    # Manually log in the user using Django's auth system
                    auth_login(request, user) # This sets session cookies etc.
                    logger.info(f"Successful login for user {user.id} (Email: {email}) from IP: {remote_addr}")
                    messages.success(request, 'Login successful!')
                    # Redirect to 'next' URL or default
                    next_url = request.GET.get('next')
                    # Basic security check for open redirect vulnerability
                    if next_url and not next_url.startswith('/'):
                        logger.warning(f"Potential open redirect attempt detected for user {user.id}. Next URL: {next_url}")
                        next_url = reverse('main:index')
                    return redirect(next_url or 'main:index')
                else:
                    logger.warning(f"Failed login attempt (invalid password) for email {email} from IP: {remote_addr}")
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                logger.warning(f"Failed login attempt (user not found) for email {email} from IP: {remote_addr}")
                messages.error(request, 'Invalid email or password.')
            except Exception as e:
                 logger.error(f"An error occurred during login for email {email}: {str(e)}")
                 messages.error(request, f'An error occurred during login.')
        else:
             logger.warning(f"Login form validation failed: {form.errors}")
             messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    return render(request, 'portal_auth/login.html', {'form': form})


def logout_view(request):
    """
    Handle user logout.
    Equivalent to Flask's logout route.
    """
    user_id_before_logout = None
    if request.user.is_authenticated:
        user_id_before_logout = request.user.id
        auth_logout(request)
        logger.info(f"User logged out: {user_id_before_logout}")
        messages.success(request, 'You have been logged out.')
    else:
        logger.info("Logout endpoint accessed by unauthenticated user.")
    # Redirect even if user wasn't logged in
    return redirect('main:index')


@login_required
def profile_view(request):
    """
    Handle user profile viewing and editing.
    Equivalent to Flask's profile route.
    """
    user = request.user # Get the currently logged-in user instance
    logger.info(f"Profile page accessed by user {user.id}")

    if request.method == 'POST':
        logger.info(f"Profile update form submitted by user {user.id}")
        # Pass instance for update, and request.FILES for file uploads
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            try:
                old_username = user.username
                old_email = user.email
                picture_changed = 'profile_picture' in request.FILES

                # Log specific change attempts before saving
                if form.cleaned_data['username'] != old_username:
                    logger.info(f"User {user.id} attempting to change username from '{old_username}' to '{form.cleaned_data['username']}'")
                if form.cleaned_data['email'] != old_email:
                     logger.info(f"User {user.id} attempting to change email from '{old_email}' to '{form.cleaned_data['email']}'")
                if picture_changed:
                    logger.info(f"User {user.id} attempting to upload new profile picture: {request.FILES['profile_picture'].name}")

                # ModelForm handles saving the instance and the uploaded file
                updated_user = form.save()
                logger.info(f"Profile updated successfully for user {user.id}. Changes: username: {old_username}->{updated_user.username}, email: {old_email}->{updated_user.email}, picture_updated: {picture_changed}")
                messages.success(request, 'Your profile has been updated!')
                return redirect('portal_auth:profile') # Redirect back to profile page
            except Exception as e:
                 logger.error(f"An error occurred while updating profile for user {user.id}: {str(e)}")
                 messages.error(request, f'An error occurred while updating your profile.')
        else:
             logger.warning(f"Profile update form validation failed for user {user.id}: {form.errors}")
             # Add form errors to messages if needed
             for field, errors in form.errors.items():
                 for error in errors:
                     messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        # Pre-populate form with current user data for GET request
        form = ProfileForm(instance=user)

    # Pass user separately if needed by template beyond form context
    return render(request, 'portal_auth/profile.html', {'form': form, 'user': user})
