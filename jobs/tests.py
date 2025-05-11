from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock

from portal_auth.models import User
from jobs.models import Job, Application

class JobsTestCase(TestCase):
    """Base test case for jobs tests with common setup"""
    
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
        
        # Create a job seeker user
        self.job_seeker = User.objects.create(
            username='seeker',
            email='seeker@example.com',
            role='job_seeker'
        )
        self.job_seeker.set_password('password123')
        self.job_seeker.save()
        
        # Create a test job
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
        
    def login_as_job_seeker(self):
        """Helper method to log in as job seeker"""
        self.client.login(username='seeker', password='password123')
        
    def login_as_employer(self):
        """Helper method to log in as employer"""
        self.client.login(username='employer', password='password123')


class JobsListTests(JobsTestCase):
    """Tests for jobs list functionality"""
    
    def test_jobs_list_page_loads(self):
        """Test that jobs list page loads successfully"""
        response = self.client.get(reverse('jobs:jobs_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/list.html')
        self.assertContains(response, 'TestJob')
    
    def test_jobs_list_with_filters(self):
        """Test jobs list with filters"""
        response = self.client.get(
            reverse('jobs:jobs_list'),
            {'location': 'Remote', 'category': 'IT', 'company': 'TestCo'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TestJob')
        
        # Test with filter that should return no results
        response = self.client.get(
            reverse('jobs:jobs_list'),
            {'location': 'NonExistent'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'TestJob')


class JobSearchAPITests(JobsTestCase):
    """Tests for job search API"""
    
    def test_job_search_api(self):
        """Test job search API endpoint"""
        response = self.client.get(
            reverse('jobs:search_jobs_api'),
            {'location': 'Remote'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('jobs', response.json())
        self.assertEqual(len(response.json()['jobs']), 1)
        
        # Test with filter that should return no results
        response = self.client.get(
            reverse('jobs:search_jobs_api'),
            {'location': 'NonExistent'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['jobs']), 0)


class JobDetailTests(JobsTestCase):
    """Tests for job detail functionality"""
    
    def test_job_detail_page_loads(self):
        """Test that job detail page loads successfully"""
        response = self.client.get(
            reverse('jobs:job_detail', kwargs={'job_id': self.job.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_detail.html')
        self.assertContains(response, 'TestJob')
    
    def test_job_detail_page_not_found(self):
        """Test job detail page with non-existent job ID"""
        response = self.client.get(
            reverse('jobs:job_detail', kwargs={'job_id': 9999})
        )
        self.assertEqual(response.status_code, 404)


class JobApplicationTests(JobsTestCase):
    """Tests for job application functionality"""
    
    def test_apply_job_get(self):
        """Test GET request to apply_job view"""
        self.login_as_job_seeker()
        response = self.client.get(
            reverse('jobs:apply_job', kwargs={'job_id': self.job.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/apply_job.html')
        self.assertIn('form', response.context)
    
    def test_apply_job_post_success(self):
        """Test successful job application submission"""
        self.login_as_job_seeker()
        
        # Create a simple resume file for testing
        resume = SimpleUploadedFile(
            "resume.pdf", 
            b"my resume", 
            content_type="application/pdf"
        )
        
        # Apply for the job
        response = self.client.post(
            reverse('jobs:apply_job', kwargs={'job_id': self.job.id}),
            {'resume': resume},
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that application was created
        self.assertTrue(
            Application.objects.filter(
                job=self.job, 
                applicant=self.job_seeker
            ).exists()
        )
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('submitted' in str(message).lower() for message in messages))
    
    def test_apply_job_duplicate(self):
        """Test attempting to apply for a job that the user has already applied for"""
        self.login_as_job_seeker()
        
        # Create an existing application
        Application.objects.create(
            job=self.job,
            applicant=self.job_seeker,
            status='applied'
        )
        
        # Try to apply again
        response = self.client.get(
            reverse('jobs:apply_job', kwargs={'job_id': self.job.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check for warning message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already applied' in str(message).lower() for message in messages))
    
    def test_apply_job_post_invalid(self):
        """Test applying for a job with no resume (should show form validation error)"""
        self.login_as_job_seeker()
        
        # Apply for the job with no resume
        response = self.client.post(
            reverse('jobs:apply_job', kwargs={'job_id': self.job.id}),
            {},
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that the form is invalid and we're still on the apply page
        self.assertTemplateUsed(response, 'jobs/apply_job.html')
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
        
        # Check that no application was created
        self.assertFalse(
            Application.objects.filter(
                job=self.job, 
                applicant=self.job_seeker
            ).exists()
        )
    
    @patch('jobs.views.Application.save')
    def test_apply_job_post_error(self, mock_save):
        """Test error handling when application submission fails"""
        self.login_as_job_seeker()
        
        # Make the save method raise an exception
        mock_save.side_effect = Exception('Database error')
        
        # Create a simple resume file for testing
        resume = SimpleUploadedFile(
            "resume.pdf", 
            b"my resume", 
            content_type="application/pdf"
        )
        
        # Apply for the job
        response = self.client.post(
            reverse('jobs:apply_job', kwargs={'job_id': self.job.id}),
            {'resume': resume},
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('error' in str(message).lower() for message in messages))
        
        # Check that no application was created
        self.assertFalse(
            Application.objects.filter(
                job=self.job, 
                applicant=self.job_seeker
            ).exists()
        )


class ModelTests(TestCase):
    """Tests for Django models"""
    
    def test_job_model(self):
        """Test creating a Job model instance"""
        # Create an employer
        employer = User.objects.create(
            username='employer',
            email='emp@example.com',
            role='employer'
        )
        
        # Create a job
        job = Job.objects.create(
            title='Developer',
            description='Job desc',
            location='New Delhi',
            category='Software Development',
            company='Coca Cola',
            poster=employer
        )
        
        # Check that job was created
        retrieved_job = Job.objects.get(title='Developer')
        self.assertEqual(retrieved_job.company, 'Coca Cola')
        self.assertEqual(retrieved_job.poster, employer)
    
    def test_application_model(self):
        """Test creating an Application model instance"""
        # Create a job seeker
        job_seeker = User.objects.create(
            username='seeker',
            email='seek@example.com',
            role='job_seeker'
        )
        
        # Create an employer
        employer = User.objects.create(
            username='employer2',
            email='emp2@example.com',
            role='employer'
        )
        
        # Create a job
        job = Job.objects.create(
            title='QA',
            description='QA desc',
            location='New Delhi',
            category='Software Development',
            company='Coca Cola',
            poster=employer
        )
        
        # Create an application
        application = Application.objects.create(
            job=job,
            applicant=job_seeker,
            status='applied'
        )
        
        # Check that application was created
        retrieved_application = Application.objects.get(job=job, applicant=job_seeker)
        self.assertEqual(retrieved_application.status, 'applied')
