from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages

from portal_auth.models import User
from jobs.models import Job, Application

class AdminTestCase(TestCase):
    """Base test case for admin tests with common setup"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create an admin user
        self.admin = User.objects.create(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        self.admin.set_password('password123')
        self.admin.save()
        
        # Create a job seeker user
        self.job_seeker = User.objects.create(
            username='seeker',
            email='seeker@example.com',
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
        
        # Create a client for making requests
        self.client = Client()
        
    def login_as_admin(self):
        """Helper method to log in as admin"""
        self.client.login(username='admin', password='password123')
        
    def login_as_job_seeker(self):
        """Helper method to log in as job seeker"""
        self.client.login(username='seeker', password='password123')
        
    def login_as_employer(self):
        """Helper method to log in as employer"""
        self.client.login(username='employer', password='password123')


class AdminAccessTests(AdminTestCase):
    """Tests for admin access to views"""
    
    def test_admin_dashboard_requires_login(self):
        """Test that admin dashboard requires login"""
        response = self.client.get(reverse('portal_admin:admin_dashboard'))
        self.assertRedirects(
            response, 
            f"{reverse('portal_auth:login')}?next={reverse('portal_admin:admin_dashboard')}"
        )
    
    def test_admin_users_requires_login(self):
        """Test that admin users view requires login"""
        response = self.client.get(reverse('portal_admin:admin_users'))
        self.assertRedirects(
            response, 
            f"{reverse('portal_auth:login')}?next={reverse('portal_admin:admin_users')}"
        )
    
    def test_non_admin_cannot_access_admin_views(self):
        """Test that non-admin users cannot access admin views"""
        self.login_as_job_seeker()
        
        # Try to access admin dashboard as job seeker
        response = self.client.get(reverse('portal_admin:admin_dashboard'))
        # Should redirect to index with permission denied message
        self.assertRedirects(response, reverse('main:index'))
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('permission' in str(message) for message in messages))


class AdminDashboardTests(AdminTestCase):
    """Tests for admin dashboard"""
    
    def test_admin_dashboard(self):
        """Test admin dashboard view"""
        self.login_as_admin()
        response = self.client.get(reverse('portal_admin:admin_dashboard'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal_admin/dashboard.html')
        
        # Check context data
        self.assertIn('user_count', response.context)
        self.assertIn('job_count', response.context)
        self.assertIn('app_count', response.context)
        
        # Check counts
        self.assertEqual(response.context['user_count'], 3)  # admin, job_seeker, employer
        self.assertEqual(response.context['job_count'], 0)
        self.assertEqual(response.context['app_count'], 0)


class AdminUserManagementTests(AdminTestCase):
    """Tests for admin user management"""
    
    def test_admin_users(self):
        """Test admin users view"""
        self.login_as_admin()
        response = self.client.get(reverse('portal_admin:admin_users'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal_admin/users.html')
        
        # Check that all users are shown
        self.assertEqual(len(response.context['users']), 3)
    
    def test_admin_create_user(self):
        """Test creating a new user as admin"""
        self.login_as_admin()
        
        # Create user data
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'TestPassword123!',
            'confirm_password': 'TestPassword123!',
            'role': 'job_seeker'
        }
        
        # Create the user
        response = self.client.post(
            reverse('portal_admin:admin_new_user'),
            user_data,
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('created' in str(message).lower() for message in messages))
    
    def test_admin_create_user_duplicate_email(self):
        """Test creating a user with an email that already exists"""
        self.login_as_admin()
        
        # Create user data with duplicate email
        user_data = {
            'username': 'newuser',
            'email': 'seeker@example.com',  # Already exists
            'password': 'TestPassword123!',
            'confirm_password': 'TestPassword123!',
            'role': 'job_seeker'
        }
        
        # Try to create the user
        response = self.client.post(
            reverse('portal_admin:admin_new_user'),
            user_data,
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was not created
        self.assertFalse(User.objects.filter(username='newuser').exists())
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already exists' in str(message).lower() for message in messages))
    
    def test_admin_edit_user(self):
        """Test editing a user as admin"""
        self.login_as_admin()
        
        # Edit user data
        user_data = {
            'username': 'edited',
            'email': 'edited@example.com',
            'role': 'employer'
        }
        
        # Edit the user
        response = self.client.post(
            reverse('portal_admin:admin_edit_user', kwargs={'user_id': self.job_seeker.id}),
            user_data,
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was updated
        self.job_seeker.refresh_from_db()
        self.assertEqual(self.job_seeker.username, 'edited')
        self.assertEqual(self.job_seeker.email, 'edited@example.com')
        self.assertEqual(self.job_seeker.role, 'employer')
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('updated' in str(message).lower() for message in messages))
    
    def test_admin_edit_user_duplicate_email(self):
        """Test editing a user with an email that already exists"""
        self.login_as_admin()
        
        # Edit user data with duplicate email
        user_data = {
            'username': 'edited',
            'email': 'employer@example.com',  # Already exists
            'role': 'employer'
        }
        
        # Try to edit the user
        response = self.client.post(
            reverse('portal_admin:admin_edit_user', kwargs={'user_id': self.job_seeker.id}),
            user_data,
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was not updated
        self.job_seeker.refresh_from_db()
        self.assertEqual(self.job_seeker.username, 'seeker')
        self.assertEqual(self.job_seeker.email, 'seeker@example.com')
        
        # Check for error message
        self.assertIn('email', response.context['form'].errors)
    
    def test_admin_delete_user(self):
        """Test deleting a user as admin"""
        self.login_as_admin()
        
        # Delete the user
        response = self.client.post(
            reverse('portal_admin:admin_delete_user', kwargs={'user_id': self.job_seeker.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was deleted
        self.assertFalse(User.objects.filter(id=self.job_seeker.id).exists())
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('deleted' in str(message).lower() for message in messages))
    
    def test_admin_delete_self(self):
        """Test admin attempting to delete their own account"""
        self.login_as_admin()
        
        # Try to delete own account
        response = self.client.post(
            reverse('portal_admin:admin_delete_user', kwargs={'user_id': self.admin.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that admin was not deleted
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('cannot delete your own account' in str(message).lower() for message in messages))


class AdminJobManagementTests(AdminTestCase):
    """Tests for admin job management"""
    
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
            poster=self.admin
        )
    
    def test_admin_jobs(self):
        """Test admin jobs view"""
        self.login_as_admin()
        response = self.client.get(reverse('portal_admin:admin_jobs'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal_admin/jobs.html')
        
        # Check that job is shown
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0], self.job)
    
    def test_admin_create_job(self):
        """Test creating a new job as admin"""
        self.login_as_admin()
        
        # Count jobs before creating
        jobs_before = Job.objects.count()
        
        # Create job data with all required fields
        job_data = {
            'title': 'Admin Job',
            'description': 'Admin job desc with sufficient length to pass validation',
            'location': 'Remote',
            'company': 'AdminCo',
            'salary': '100000',
            'category': 'IT'
        }
        
        # Create the job
        response = self.client.post(
            reverse('portal_admin:admin_create_job'),
            job_data,
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that job was created
        self.assertEqual(Job.objects.count(), jobs_before + 1)
        new_job = Job.objects.filter(title='Admin Job').first()
        self.assertIsNotNone(new_job)
        self.assertEqual(new_job.description, 'Admin job desc with sufficient length to pass validation')
        self.assertEqual(new_job.company, 'AdminCo')
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('created' in str(message).lower() for message in messages))
    
    def test_admin_edit_job(self):
        """Test editing a job as admin"""
        self.login_as_admin()
        
        # Get the job from the database to ensure we have the latest version
        job = Job.objects.get(id=self.job.id)
        
        # Edit job data
        job_data = {
            'title': 'EditedJob',
            'description': 'desc',
            'location': 'Remote',
            'company': 'AdminCo',
            'salary': '100000',
            'category': 'IT'
        }
        
        # Edit the job
        response = self.client.post(
            reverse('portal_admin:admin_edit_job', kwargs={'job_id': job.id}),
            job_data,
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Get a fresh instance from the database
        updated_job = Job.objects.get(id=job.id)
        
        # Check that job was updated
        self.assertEqual(updated_job.title, 'EditedJob')
        self.assertEqual(updated_job.company, 'AdminCo')
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('updated' in str(message).lower() for message in messages))
    
    def test_admin_delete_job(self):
        """Test deleting a job as admin"""
        self.login_as_admin()
        
        # Delete the job
        response = self.client.post(
            reverse('portal_admin:admin_delete_job', kwargs={'job_id': self.job.id}),
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that job was deleted
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('deleted' in str(message).lower() for message in messages))


class AdminApplicationManagementTests(AdminTestCase):
    """Tests for admin application management"""
    
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
    
    def test_admin_applications(self):
        """Test admin applications view"""
        self.login_as_admin()
        response = self.client.get(reverse('portal_admin:admin_applications'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal_admin/applications.html')
        
        # Check that application is shown
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0], self.application)
    
    def test_admin_update_application(self):
        """Test updating application status as admin"""
        self.login_as_admin()
        
        # Update application status
        response = self.client.post(
            reverse('portal_admin:admin_update_application', kwargs={'application_id': self.application.id}),
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
        self.assertTrue(any('updated' in str(message).lower() for message in messages))
    
    def test_admin_update_application_invalid_status(self):
        """Test updating application with invalid status"""
        self.login_as_admin()
        
        # Try to update with invalid status
        response = self.client.post(
            reverse('portal_admin:admin_update_application', kwargs={'application_id': self.application.id}),
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