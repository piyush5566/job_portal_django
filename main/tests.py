from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from unittest.mock import patch

from jobs.models import Job
from portal_auth.models import User
from main.forms import ContactForm

class MainTestCase(TestCase):
    """Base test case for main app tests with common setup"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create an employer user
        self.employer = User.objects.create(
            username='employer',
            email='employer@example.com',
            role='employer'
        )
        self.employer.set_password('password123')
        self.employer.save()
        
        # Create a test job for featured jobs
        self.job = Job.objects.create(
            title='TestJob',
            description='desc',
            location='Remote',
            category='IT',
            company='TestCo',
            salary='$100',
            poster=self.employer
        )
        
        # Create a client for making requests
        self.client = Client()


class MainPageTests(MainTestCase):
    """Tests for main pages"""
    
    def test_home_page(self):
        """Test that home page loads successfully"""
        response = self.client.get(reverse('main:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/index.html')
        
        # Check that featured jobs are in the context
        self.assertIn('featured_jobs', response.context)
        self.assertEqual(len(response.context['featured_jobs']), 1)
        self.assertEqual(response.context['featured_jobs'][0], self.job)
        
        # Check that job categories are in the context
        self.assertIn('job_categories', response.context)
        self.assertEqual(len(response.context['job_categories']), 1)
        self.assertEqual(response.context['job_categories'][0]['category'], 'IT')
        self.assertEqual(response.context['job_categories'][0]['count'], 1)
    
    def test_about_page(self):
        """Test that about page loads successfully"""
        response = self.client.get(reverse('main:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/about.html')
        self.assertContains(response, 'About')
    
    def test_privacy_page(self):
        """Test that privacy page loads successfully"""
        response = self.client.get(reverse('main:privacy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/privacy.html')
        self.assertContains(response, 'Privacy')
        
        # Check that current date is in the context
        self.assertIn('current_date', response.context)
    
    def test_terms_page(self):
        """Test that terms page loads successfully"""
        response = self.client.get(reverse('main:terms'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/terms.html')
        self.assertContains(response, 'Terms')
        
        # Check that current date is in the context
        self.assertIn('current_date', response.context)


class ContactFormTests(MainTestCase):
    """Tests for contact form functionality"""
    
    def test_contact_page_get(self):
        """Test GET request to contact page"""
        response = self.client.get(reverse('main:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/contact.html')
        self.assertIsInstance(response.context['form'], ContactForm)
    
    @patch('main.views.send_mail')
    def test_contact_page_post_success(self, mock_send_mail):
        """Test successful contact form submission"""
        # Configure the mock to return True (success)
        mock_send_mail.return_value = 1
        
        # Submit the contact form
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Hello! This is a test message.'
        }
        response = self.client.post(reverse('main:contact'), data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that send_mail was called
        mock_send_mail.assert_called_once()
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('sent' in str(message).lower() for message in messages))
    
    @patch('main.views.send_mail')
    def test_contact_page_post_failure(self, mock_send_mail):
        """Test error handling when email sending fails"""
        # Configure the mock to raise an exception
        mock_send_mail.side_effect = Exception('Email sending failed')
        
        # Submit the contact form
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Hello! This is a test message.'
        }
        response = self.client.post(reverse('main:contact'), data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('error' in str(message).lower() for message in messages))
    
    def test_contact_page_post_invalid(self):
        """Test contact form with invalid data"""
        # Submit the contact form with invalid data
        data = {
            'name': '',  # Empty name (required)
            'email': 'notanemail',  # Invalid email
            'subject': '',  # Empty subject (required)
            'message': ''  # Empty message (required)
        }
        response = self.client.post(reverse('main:contact'), data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(response.context['form'].is_valid())
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('errors' in str(message).lower() for message in messages))
    
    def test_contact_form_validation(self):
        """Test contact form validation rules"""
        # Test with valid data
        form = ContactForm({
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Hello! This is a test message.'
        })
        self.assertTrue(form.is_valid())
        
        # Test with invalid name (contains numbers)
        form = ContactForm({
            'name': 'Test123',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Hello! This is a test message.'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
        # Test with invalid email
        form = ContactForm({
            'name': 'Test User',
            'email': 'notanemail',
            'subject': 'Test Subject',
            'message': 'Hello! This is a test message.'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        
        # Test with short message
        form = ContactForm({
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Hi'  # Too short
        })
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)