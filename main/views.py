# main/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from datetime import date
import logging # Import logging
import time # For email retry delay

# Import models from the 'jobs' app
from jobs.models import Job
# Import forms from the current app
from .forms import ContactForm

logger = logging.getLogger(__name__) # Get logger for this module

# --- Views ---

def index_view(request):
    """
    Display the application home page.
    Equivalent to Flask's index route.
    """
    logger.info("Home page accessed")
    # Get featured jobs (e.g., 5 most recent)
    featured_jobs = Job.objects.order_by('-posted_date')[:5]

    # Get job categories with counts using Django ORM aggregation
    job_categories = Job.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count', 'category')
    logger.info(f"Featured jobs: {featured_jobs}")
    logger.info(f"Job categories: {job_categories}")

    context = {
        'featured_jobs': featured_jobs,
        'job_categories': job_categories,
    }
    return render(request, 'main/index.html', context)


def about_view(request):
    """Display the About Us page."""
    logger.info("About page accessed")
    return render(request, 'main/about.html')


def privacy_view(request):
    """Display the Privacy Policy page."""
    logger.info("Privacy policy page accessed")
    context = {'current_date': date.today().strftime("%B %d, %Y")}
    return render(request, 'main/privacy.html', context)


def terms_view(request):
    """Display the Terms & Conditions page."""
    logger.info("Terms of service page accessed")
    context = {'current_date': date.today().strftime("%B %d, %Y")}
    return render(request, 'main/terms.html', context)


def contact_view(request):
    """
    Display the contact form and handle submissions.
    Equivalent to Flask's contact route.
    """
    logger.info("Contact page accessed")
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message_body = form.cleaned_data['message']

            logger.info(f"Contact form submitted by {name} <{email}> with subject: '{subject}'")

            try:
                # Construct email subject and body
                full_subject = f"Job Portal Contact: {subject}"
                full_message = f"From: {name} <{email}>\n\n{message_body}"

                # Send email using Django's send_mail function
                # Add retry logic similar to Flask example
                max_retries = 3
                sent_successfully = False
                for attempt in range(max_retries):
                    try:
                        send_mail(
                            subject=full_subject,
                            message=full_message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[settings.CONTACT_EMAIL_RECIPIENT],
                            fail_silently=False, # Raise exception on failure
                        )
                        logger.info(f"Contact email sent successfully from {email} (attempt {attempt + 1})")
                        messages.success(request, 'Your message has been sent! We will get back to you soon.')
                        sent_successfully = True
                        break # Exit retry loop on success
                    except Exception as mail_error:
                        if attempt == max_retries - 1: # Last attempt failed
                            logger.error(f"Failed to send contact email from {email} after {max_retries} attempts: {str(mail_error)}")
                            messages.error(request, 'An error occurred while sending your message. Please try again later.')
                        else:
                            logger.warning(f"Email send attempt {attempt + 1} for {email} failed, retrying... Error: {str(mail_error)}")
                            time.sleep(1) # Wait before retrying
                            continue

                if sent_successfully:
                    return redirect('main:contact') # Redirect back to contact page

            except Exception as e:
                # Catch potential errors outside the mail sending loop
                logger.error(f"Unexpected error processing contact form from {email}: {str(e)}")
                messages.error(request, f'An unexpected error occurred.')
                # Stay on the contact page with the form data
        else:
            logger.warning(f"Contact form validation failed: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request
        form = ContactForm()

    context = {
        'form': form,
        'contact_email': settings.CONTACT_EMAIL_RECIPIENT
    }
    return render(request, 'main/contact.html', context)

