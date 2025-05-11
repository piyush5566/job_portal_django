from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO

from portal_auth.models import User
from portal_auth.forms import RegistrationForm, LoginForm, ProfileForm

class AuthTestCase(TestCase):
    """Base test case for auth tests with common setup"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create a client for making requests
        self.client = Client()


class RegistrationTests(AuthTestCase):
    """Tests for user registration"""
    
    def test_register_page_loads(self):
        """Test that registration page loads successfully"""
        response = self.client.get(reverse('portal_auth:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal_auth/register.html')
        self.assertIsInstance(response.context['form'], RegistrationForm)
    
    def test_register_success(self):
        """Test successful user registration"""
        # Register a new user
        user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'TestPassword123!',
            'confirm_password': 'TestPassword123!',
            'role': 'job_seeker'
        }
        response = self.client.post(reverse('portal_auth:register'), user_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was created
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('successful' in str(message).lower() for message in messages))
    
    def test_register_duplicate_email(self):
        """Test registration with an email that already exists"""
        # Create a user
        User.objects.create(
            username='existinguser',
            email='existing@example.com',
            role='job_seeker'
        )
        
        # Try to register with the same email
        user_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'TestPassword123!',
            'confirm_password': 'TestPassword123!',
            'role': 'job_seeker'
        }
        response = self.client.post(reverse('portal_auth:register'), user_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was not created
        self.assertFalse(User.objects.filter(username='newuser').exists())
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already exists' in str(message).lower() for message in messages))
    
    def test_register_invalid_form(self):
        """Test registration with invalid form data"""
        # Try to register with invalid data
        user_data = {
            'username': '',
            'email': 'notanemail',
            'password': 'short',
            'confirm_password': 'different',
            'role': 'job_seeker'
        }
        response = self.client.post(reverse('portal_auth:register'), user_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        self.assertTrue(response.context['form'].errors)
        
        # Check that user was not created
        self.assertEqual(User.objects.count(), 0)
    
    def test_register_already_logged_in(self):
        """Test accessing registration page when already logged in"""
        # Create and log in a user
        user = User.objects.create_user(
            username='loggedin',
            email='loggedin@example.com',
            password='TestPassword123!',
            role='job_seeker'
        )
        self.client.login(username='loggedin', password='TestPassword123!')
        
        # Try to access registration page
        response = self.client.get(reverse('portal_auth:register'), follow=True)
        
        # Should redirect to index
        self.assertRedirects(response, reverse('main:index'))


class LoginTests(AuthTestCase):
    """Tests for user login"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create a user for login tests
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123!',
            role='job_seeker'
        )
    
    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get(reverse('portal_auth:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal_auth/login.html')
        self.assertIsInstance(response.context['form'], LoginForm)
    
    def test_login_success(self):
        """Test successful login"""
        # Log in
        login_data = {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!'
        }
        response = self.client.post(reverse('portal_auth:login'), login_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user is logged in
        self.assertTrue(response.context['user'].is_authenticated)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('successful' in str(message).lower() for message in messages))
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Try to log in with wrong password
        login_data = {
            'email': 'testuser@example.com',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(reverse('portal_auth:login'), login_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user is not logged in
        self.assertFalse(response.context['user'].is_authenticated)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(message).lower() for message in messages))
    
    def test_login_nonexistent_user(self):
        """Test login with email that doesn't exist"""
        # Try to log in with non-existent email
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPassword123!'
        }
        response = self.client.post(reverse('portal_auth:login'), login_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user is not logged in
        self.assertFalse(response.context['user'].is_authenticated)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(message).lower() for message in messages))
    
    def test_login_already_logged_in(self):
        """Test accessing login page when already logged in"""
        # Log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Try to access login page
        response = self.client.get(reverse('portal_auth:login'), follow=True)
        
        # Should redirect to index
        self.assertRedirects(response, reverse('main:index'))


class LogoutTests(AuthTestCase):
    """Tests for user logout"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create a user for logout tests
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123!',
            role='job_seeker'
        )
    
    def test_logout(self):
        """Test user logout"""
        # Log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Log out
        response = self.client.get(reverse('portal_auth:logout'), follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user is logged out
        self.assertFalse(response.context['user'].is_authenticated)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('logged out' in str(message).lower() for message in messages))


class ProfileTests(AuthTestCase):
    """Tests for user profile"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create a user for profile tests
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123!',
            role='job_seeker'
        )
        
        # Create another user for duplicate tests
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='TestPassword123!',
            role='job_seeker'
        )
    
    def test_profile_requires_login(self):
        """Test that profile page requires login"""
        # Try to access profile without logging in
        response = self.client.get(reverse('portal_auth:profile'))
        
        # Should redirect to login page
        self.assertRedirects(
            response, 
            f"{reverse('portal_auth:login')}?next={reverse('portal_auth:profile')}"
        )
    
    def test_profile_page_loads(self):
        """Test that profile page loads successfully"""
        # Log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Access profile page
        response = self.client.get(reverse('portal_auth:profile'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal_auth/profile.html')
        self.assertIsInstance(response.context['form'], ProfileForm)
    
    def test_profile_update(self):
        """Test updating profile information"""
        # Log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Update profile
        profile_data = {
            'username': 'updateduser',
            'email': 'updated@example.com'
        }
        response = self.client.post(reverse('portal_auth:profile'), profile_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that profile was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('updated' in str(message).lower() for message in messages))
    
    def test_profile_duplicate_username(self):
        """Test updating profile with a username that already exists"""
        # Log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Try to update with duplicate username
        profile_data = {
            'username': 'otheruser',  # Already exists
            'email': 'testuser@example.com'
        }
        response = self.client.post(reverse('portal_auth:profile'), profile_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        self.assertIn('username', response.context['form'].errors)
        
        # Check that profile was not updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')
    
    def test_profile_duplicate_email(self):
        """Test updating profile with an email that already exists"""
        # Log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Try to update with duplicate email
        profile_data = {
            'username': 'testuser',
            'email': 'otheruser@example.com'  # Already exists
        }
        response = self.client.post(reverse('portal_auth:profile'), profile_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        self.assertIn('email', response.context['form'].errors)
        
        # Check that profile was not updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'testuser@example.com')
    
    def test_profile_invalid_picture(self):
        """Test updating profile with an invalid picture file"""
        # Log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Create an invalid file
        invalid_file = SimpleUploadedFile(
            "file.exe",
            b"file_content",
            content_type="application/octet-stream"
        )
        
        # Try to update with invalid picture
        profile_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'profile_picture': invalid_file
        }
        response = self.client.post(reverse('portal_auth:profile'), profile_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        self.assertIn('profile_picture', response.context['form'].errors)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(message).lower() for message in messages))


class RegistrationLoginLogoutFlowTests(AuthTestCase):
    """Tests for the complete registration, login, and logout flow"""
    
    def test_register_login_logout_flow(self):
        """Test the complete user flow: register, login, and logout"""
        # 1. Register a new user
        register_data = {
            'username': 'flowuser',
            'email': 'flowuser@example.com',
            'password': 'TestPassword123!',
            'confirm_password': 'TestPassword123!',
            'role': 'job_seeker'
        }
        response = self.client.post(reverse('portal_auth:register'), register_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='flowuser').exists())
        
        # 2. Login with the new user
        login_data = {
            'email': 'flowuser@example.com',
            'password': 'TestPassword123!'
        }
        response = self.client.post(reverse('portal_auth:login'), login_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        
        # 3. Logout
        response = self.client.get(reverse('portal_auth:logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        
        
class ModelTests(TestCase):
    """Tests for Django models"""
    
    def test_user_model(self):
        """Test creating a User model instance"""
        user = User.objects.create(
            username='testuser',
            email='test@example.com',
            role='job_seeker'
        )
        user.set_password('TestPassword123!')
        user.save()
        
        # Check that user was created
        retrieved_user = User.objects.get(username='testuser')
        self.assertEqual(retrieved_user.email, 'test@example.com')
        self.assertEqual(retrieved_user.role, 'job_seeker')
    
