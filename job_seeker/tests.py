from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from portal_auth.models import User
from jobs.models import Job, Application

class JobSeekerTestCase(TestCase):
    """Base test case for job seeker tests with common setup"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create a job seeker user
        self.job_seeker = User.objects.create(
            username='jobseeker',
            email='jobseeker@example.com',
            role='job_seeker'
        )
        self.job_seeker.set_password('password123')
        self.job_seeker.save()
        
        # Create an employer user
        self.employer = User.objects.create(
            username='employer',
            email='employer@example.com',
            role='employer'
        )
        self.employer.set_password('password123')
        self.employer.save()
        
        # Create an admin user
        self.admin = User.objects.create(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        self.admin.set_password('password123')
        self.admin.save()
        
        # Create a job for testing applications
        self.job = Job.objects.create(
            title='Test Job',
            description='Test description',
            location='Test Location',
            category='IT',
            company='Test Company',
            poster=self.employer
        )
        
        # Create a client for making requests
        self.client = Client()
        
    def login_as_job_seeker(self):
        """Helper method to log in as job seeker"""
        self.client.login(username='jobseeker', password='password123')
        
    def login_as_employer(self):
        """Helper method to log in as employer"""
        self.client.login(username='employer', password='password123')
        
    def login_as_admin(self):
        """Helper method to log in as admin"""
        self.client.login(username='admin', password='password123')


class JobSeekerAccessTests(JobSeekerTestCase):
    """Tests for job seeker access to views"""
    
    def test_my_applications_requires_login(self):
        """Test that my_applications view requires login"""
        # Try to access my_applications without logging in
        response = self.client.get(reverse('job_seeker:my_applications'))
        # Should redirect to login page
        self.assertRedirects(
            response, 
            f"{reverse('portal_auth:login')}?next={reverse('job_seeker:my_applications')}"
        )
    
    def test_employer_cannot_access_job_seeker_views(self):
        """Test that employers cannot access job seeker views"""
        self.login_as_employer()
        
        # Try to access my_applications as employer
        response = self.client.get(reverse('job_seeker:my_applications'))
        # Should redirect to index with permission denied message
        self.assertRedirects(response, reverse('main:index'))
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('permission' in str(message) for message in messages))


class MyApplicationsTests(JobSeekerTestCase):
    """Tests for my_applications view"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create some applications for the job seeker
        self.application1 = Application.objects.create(
            job=self.job,
            applicant=self.job_seeker,
            status='applied'
        )
        
        # Create another job
        self.job2 = Job.objects.create(
            title='Another Job',
            description='Another description',
            location='Another Location',
            category='Marketing',
            company='Another Company',
            poster=self.employer
        )
        
        # Create another application
        self.application2 = Application.objects.create(
            job=self.job2,
            applicant=self.job_seeker,
            status='reviewed'
        )
    
    def test_my_applications_view(self):
        """Test my_applications view shows all applications for the job seeker"""
        self.login_as_job_seeker()
        response = self.client.get(reverse('job_seeker:my_applications'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_seeker/my_applications.html')
        
        # Check that both applications are shown
        self.assertEqual(len(response.context['applications']), 2)
        
        # Check that applications are ordered by application_date (newest first)
        self.assertEqual(list(response.context['applications']), [self.application2, self.application1])
        
        # Check that application details are in the response
        self.assertContains(response, 'Test Job')
        self.assertContains(response, 'Another Job')
        self.assertContains(response, 'applied')
        self.assertContains(response, 'reviewed')


class JobApplicationTests(JobSeekerTestCase):
    """Tests for job application functionality"""
    
    def test_apply_job_view_get(self):
        """Test GET request to apply_job view"""
        self.login_as_job_seeker()
        response = self.client.get(reverse('jobs:apply_job', kwargs={'job_id': self.job.id}))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/apply_job.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['job'], self.job)
    
    def test_apply_job_post(self):
        """Test applying for a job"""
        self.login_as_job_seeker()
        
        # Create a simple resume file for testing
        resume = SimpleUploadedFile(
            "resume.pdf", 
            b"file content", 
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
    
    def test_apply_job_already_applied(self):
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
    
    def test_job_detail_view_shows_application_status(self):
        """Test that job detail view shows application status for job seekers"""
        self.login_as_job_seeker()
        
        # View job detail before applying
        response = self.client.get(reverse('jobs:job_detail', kwargs={'job_id': self.job.id}))
        
        # Check that has_applied is False
        self.assertFalse(response.context['has_applied'])
        
        # Create an application
        Application.objects.create(
            job=self.job,
            applicant=self.job_seeker,
            status='applied'
        )
        
        # View job detail after applying
        response = self.client.get(reverse('jobs:job_detail', kwargs={'job_id': self.job.id}))
        
        # Check that has_applied is True
        self.assertTrue(response.context['has_applied'])


class JobSearchTests(JobSeekerTestCase):
    """Tests for job search functionality"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create additional jobs for testing search
        Job.objects.create(
            title='Python Developer',
            description='Python development job',
            location='New York',
            category='IT',
            company='Tech Co',
            poster=self.employer
        )
        
        Job.objects.create(
            title='Marketing Manager',
            description='Marketing job',
            location='Chicago',
            category='Marketing',
            company='Marketing Co',
            poster=self.employer
        )
        
        Job.objects.create(
            title='Python Analyst',
            description='Python analysis job',
            location='New York',
            category='Data Science',
            company='Data Co',
            poster=self.employer
        )
    
    def test_jobs_list_view_no_filters(self):
        """Test jobs_list view with no filters"""
        response = self.client.get(reverse('jobs:jobs_list'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/list.html')
        
        # Check that all jobs are shown
        self.assertEqual(len(response.context['jobs']), 4)  # 3 new jobs + 1 from base setup
    
    def test_jobs_list_view_with_filters(self):
        """Test jobs_list view with filters"""
        # Filter by location
        response = self.client.get(reverse('jobs:jobs_list'), {'location': 'New York'})
        self.assertEqual(len(response.context['jobs']), 2)
        
        # Filter by category
        response = self.client.get(reverse('jobs:jobs_list'), {'category': 'IT'})
        self.assertEqual(len(response.context['jobs']), 2)  # Test Job + Python Developer
        
        # Filter by company
        response = self.client.get(reverse('jobs:jobs_list'), {'company': 'Data'})
        self.assertEqual(len(response.context['jobs']), 1)
        
        # Filter by multiple criteria
        response = self.client.get(
            reverse('jobs:jobs_list'), 
            {'location': 'New York', 'category': 'IT'}
        )
        self.assertEqual(len(response.context['jobs']), 1)  # Only Python Developer
    
    def test_search_jobs_api(self):
        """Test search_jobs_api view"""
        # Search with no filters
        response = self.client.get(reverse('jobs:search_jobs_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['jobs']), 4)
        
        # Search by location
        response = self.client.get(reverse('jobs:search_jobs_api'), {'location': 'New York'})
        self.assertEqual(len(response.json()['jobs']), 2)
        
        # Search by category
        response = self.client.get(reverse('jobs:search_jobs_api'), {'category': 'Marketing'})
        self.assertEqual(len(response.json()['jobs']), 1)
        
        # Search by company
        response = self.client.get(reverse('jobs:search_jobs_api'), {'company': 'Tech'})
        self.assertEqual(len(response.json()['jobs']), 1)
        
        # Check response format
        response = self.client.get(reverse('jobs:search_jobs_api'), {'company': 'Tech'})
        job_data = response.json()['jobs'][0]
        self.assertIn('id', job_data)
        self.assertIn('title', job_data)
        self.assertIn('company', job_data)
        self.assertIn('location', job_data)
        self.assertIn('category', job_data)
        self.assertIn('salary', job_data)
        self.assertIn('company_logo_url', job_data)
        self.assertIn('posted_date', job_data)