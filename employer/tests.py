from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from portal_auth.models import User
from jobs.models import Job, Application

class EmployerTestCase(TestCase):
    """Base test case for employer tests with common setup"""
    
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
            username='jobseeker',
            email='jobseeker@example.com',
            role='job_seeker'
        )
        self.job_seeker.set_password('password123')
        self.job_seeker.save()
        
        # Create an admin user
        self.admin = User.objects.create(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        self.admin.set_password('password123')
        self.admin.save()
        
        # Create a client for making requests
        self.client = Client()
        
    def login_as_employer(self):
        """Helper method to log in as employer"""
        self.client.login(username='employer', password='password123')
        
    def login_as_job_seeker(self):
        """Helper method to log in as job seeker"""
        self.client.login(username='jobseeker', password='password123')
        
    def login_as_admin(self):
        """Helper method to log in as admin"""
        self.client.login(username='admin', password='password123')


class EmployerAccessTests(EmployerTestCase):
    """Tests for employer access to views"""
    
    def test_employer_my_jobs_requires_login(self):
        """Test that my_jobs view requires login"""
        # Try to access my_jobs without logging in
        response = self.client.get(reverse('employer:my_jobs'))
        # Should redirect to login page
        self.assertRedirects(
            response, 
            f"{reverse('portal_auth:login')}?next={reverse('employer:my_jobs')}"
        )
    
    def test_job_seeker_cannot_access_employer_views(self):
        """Test that job seekers cannot access employer views"""
        self.login_as_job_seeker()
        
        # Try to access my_jobs as job seeker
        response = self.client.get(reverse('employer:my_jobs'))
        # Should redirect to index with permission denied message
        self.assertRedirects(response, reverse('main:index'))
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('permission' in str(message) for message in messages))


class JobPostingTests(EmployerTestCase):
    """Tests for job posting functionality"""
    
    def test_post_job_redirect_employer(self):
        """Test post_job_redirect view for employer"""
        self.login_as_employer()
        response = self.client.get(reverse('employer:post_job_redirect'))
        self.assertRedirects(response, reverse('employer:new_job'))
    
    def test_post_job_redirect_admin(self):
        """Test post_job_redirect view for admin"""
        self.login_as_admin()
        response = self.client.get(reverse('employer:post_job_redirect'))
        self.assertRedirects(response, reverse('portal_admin:admin_create_job'))
    
    def test_new_job_get(self):
        """Test GET request to new_job view"""
        self.login_as_employer()
        response = self.client.get(reverse('employer:new_job'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer/new_job.html')
        self.assertIn('form', response.context)
    
    def test_post_job(self):
        """Test posting a new job"""
        self.login_as_employer()
        
        # Create job data
        job_data = {
            'title': 'Employer Job',
            'description': 'Job desc Joob deessc Job desc Job desc',
            'location': 'Remote',
            'company': 'EmpCo',
            'salary': '90000',
            'category': 'IT'
        }
        
        # Post the job
        response = self.client.post(reverse('employer:new_job'), job_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that job was created
        self.assertTrue(Job.objects.filter(title='Employer Job').exists())
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('success' in str(message).lower() for message in messages))
    
    def test_new_job_post_invalid(self):
        """Test posting a job with invalid data"""
        self.login_as_employer()
        
        # Post with empty data
        response = self.client.post(reverse('employer:new_job'), {}, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        self.assertTrue(response.context['form'].errors)
        
        # Check that no job was created
        self.assertEqual(Job.objects.count(), 0)


class JobManagementTests(EmployerTestCase):
    """Tests for job management functionality"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create a job for the employer
        self.job = Job.objects.create(
            title='Test Job',
            description='Test description',
            location='Test Location',
            category='IT',
            company='Test Company',
            poster=self.employer
        )
        
        # Create a job for another employer
        self.other_employer = User.objects.create(
            username='other_employer',
            email='other@example.com',
            role='employer'
        )
        self.other_job = Job.objects.create(
            title='Other Job',
            description='Other description',
            location='Other Location',
            category='Marketing',
            company='Other Company',
            poster=self.other_employer
        )
    
    def test_my_jobs(self):
        """Test my_jobs view"""
        self.login_as_employer()
        response = self.client.get(reverse('employer:my_jobs'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer/my_jobs.html')
        
        # Check that only employer's jobs are shown
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0], self.job)
    
    def test_delete_job(self):
        """Test deleting a job"""
        self.login_as_employer()
        
        # Delete the job
        response = self.client.post(
            reverse('employer:delete_job', kwargs={'job_id': self.job.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that job was deleted
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('deleted' in str(message).lower() for message in messages))
    
    def test_delete_job_unauthorized(self):
        """Test attempting to delete another employer's job"""
        self.login_as_employer()
        
        # Try to delete another employer's job
        response = self.client.post(
            reverse('employer:delete_job', kwargs={'job_id': self.other_job.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that job was not deleted
        self.assertTrue(Job.objects.filter(id=self.other_job.id).exists())
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('permission' in str(message).lower() for message in messages))


class ApplicationManagementTests(EmployerTestCase):
    """Tests for application management functionality"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create a job for the employer
        self.job = Job.objects.create(
            title='Test Job',
            description='Test description',
            location='Test Location',
            category='IT',
            company='Test Company',
            poster=self.employer
        )
        
        # Create an application for the job
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.job_seeker,
            status='applied'
        )
        
        # Create a job for another employer
        self.other_employer = User.objects.create(
            username='other_employer',
            email='other@example.com',
            role='employer'
        )
        self.other_job = Job.objects.create(
            title='Other Job',
            description='Other description',
            location='Other Location',
            category='Marketing',
            company='Other Company',
            poster=self.other_employer
        )
        
        # Create an application for the other job
        self.other_application = Application.objects.create(
            job=self.other_job,
            applicant=self.job_seeker,
            status='applied'
        )
    
    def test_job_applications_permission(self):
        """Test viewing applications for employer's job"""
        self.login_as_employer()
        
        # View applications for the job
        response = self.client.get(
            reverse('employer:job_applications', kwargs={'job_id': self.job.id})
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer/job_applications.html')
        
        # Check that applications are shown
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0], self.application)
    
    def test_job_applications_unauthorized(self):
        """Test attempting to view applications for another employer's job"""
        self.login_as_employer()
        
        # Try to view applications for another employer's job
        response = self.client.get(
            reverse('employer:job_applications', kwargs={'job_id': self.other_job.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('permission' in str(message).lower() for message in messages))
    
    def test_update_application_status(self):
        """Test updating application status"""
        self.login_as_employer()
        
        # Update application status
        response = self.client.post(
            reverse('employer:update_application_status', kwargs={'application_id': self.application.id}),
            {'status': 'reviewed'},
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that application status was updated
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'reviewed')
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('status updated' in str(message).lower() for message in messages))
    
    def test_update_application_invalid_status(self):
        """Test updating application with invalid status"""
        self.login_as_employer()
        
        # Try to update with invalid status
        response = self.client.post(
            reverse('employer:update_application_status', kwargs={'application_id': self.application.id}),
            {'status': 'invalid_status'},
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that application status was not updated
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'applied')
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(message).lower() for message in messages))
    
    def test_update_application_unauthorized(self):
        """Test attempting to update application for another employer's job"""
        self.login_as_employer()
        
        # Try to update application for another employer's job
        response = self.client.post(
            reverse('employer:update_application_status', kwargs={'application_id': self.other_application.id}),
            {'status': 'reviewed'},
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that application status was not updated
        self.other_application.refresh_from_db()
        self.assertEqual(self.other_application.status, 'applied')
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('permission' in str(message).lower() for message in messages))


class AdminAccessTests(EmployerTestCase):
    """Tests for admin access to employer views"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create a job
        self.job = Job.objects.create(
            title='Test Job',
            description='Test description',
            location='Test Location',
            category='IT',
            company='Test Company',
            poster=self.employer
        )
        
        # Create an application
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.job_seeker,
            status='applied'
        )
    
    def test_admin_can_access_employer_views(self):
        """Test that admin can access employer views"""
        self.login_as_admin()
        
        # Access my_jobs view
        response = self.client.get(reverse('employer:my_jobs'))
        self.assertEqual(response.status_code, 200)
        
        # Access job applications view
        response = self.client.get(
            reverse('employer:job_applications', kwargs={'job_id': self.job.id})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_admin_can_delete_any_job(self):
        """Test that admin can delete any job"""
        self.login_as_admin()
        
        # Delete the job
        response = self.client.post(
            reverse('employer:delete_job', kwargs={'job_id': self.job.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that job was deleted
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())
    
    def test_admin_can_update_any_application(self):
        """Test that admin can update any application"""
        self.login_as_admin()
        
        # Update application status
        response = self.client.post(
            reverse('employer:update_application_status', kwargs={'application_id': self.application.id}),
            {'status': 'reviewed'},
            follow=True
        )
        
        # Check that application status was updated
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'reviewed')