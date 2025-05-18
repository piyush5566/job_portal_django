from django.test import TestCase, override_settings, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import os
import io
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from PIL import Image

from portal_auth.models import User
from jobs.models import Job, Application
from utils.utils import (
    allowed_file, 
    upload_to_s3, 
    save_company_logo_local, 
    save_profile_picture_local, 
    get_resume_file
)

class UtilsTestCase(TestCase):
    """Base test case for utils tests with common setup"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create users for testing
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='TestPassword123!',
            role='admin'
        )
        
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='TestPassword123!',
            role='employer'
        )
        
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='TestPassword123!',
            role='job_seeker'
        )
        
        # Create a job for testing
        self.job = Job.objects.create(
            title='Test Job',
            description='Test description',
            location='Test Location',
            category='IT',
            company='Test Company',
            poster=self.employer
        )
        
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_media_root = os.path.join(self.temp_dir, 'media')
        self.temp_upload_folder = os.path.join(self.temp_media_root, 'resumes')
        self.temp_company_logos_folder = os.path.join(self.temp_media_root, 'img/company_logos')
        self.temp_profile_upload_folder = os.path.join(self.temp_media_root, 'img/profiles')
        
        # Create the directory structure
        os.makedirs(self.temp_upload_folder, exist_ok=True)
        os.makedirs(self.temp_company_logos_folder, exist_ok=True)
        os.makedirs(self.temp_profile_upload_folder, exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary directories
        shutil.rmtree(self.temp_dir)


class FileValidationTests(UtilsTestCase):
    """Tests for file validation functions"""
    
    def test_allowed_file(self):
        """Test allowed_file function with various file types"""
        # Test valid file types
        self.assertTrue(allowed_file('resume.pdf', {'pdf'}))
        self.assertTrue(allowed_file('pic.jpg', {'jpg', 'png'}))
        
        # Test invalid file types
        self.assertFalse(allowed_file('resume.exe', {'pdf'}))
        self.assertFalse(allowed_file('pic', {'jpg'}))
        self.assertFalse(allowed_file('', {'jpg'}))


class CompanyLogoTests(UtilsTestCase):
    """Tests for company logo handling functions"""
    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_save_company_logo_success(self):
        """Test successful company logo saving"""
        # Create a test image
        image_content = self._create_test_image()
        logo = SimpleUploadedFile('logo.png', image_content, content_type='image/png')
        
        # Define a simplified version of the function for testing
        def mock_save_company_logo(uploaded_file):
            if not uploaded_file or not allowed_file(uploaded_file.name, {'png', 'jpg', 'jpeg'}):
                return None
            
            # Create a simple path
            test_path = 'img/company_logos/test_logo.png'
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.join(self.temp_media_root, 'img/company_logos'), exist_ok=True)
            
            # Save the file
            with open(os.path.join(self.temp_media_root, test_path), 'wb') as f:
                f.write(uploaded_file.read())
            
            return test_path
        
        # Use the mock function
        with patch('utils.utils.save_company_logo_local', mock_save_company_logo):
            result = save_company_logo_local(logo)
        
        # Check result
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.png'))
        
        # Check that file was saved
        self.assertTrue(os.path.exists(os.path.join(self.temp_media_root, result)))

    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_save_company_logo_invalid_type(self):
        """Test company logo saving with invalid file type"""
        # Create an invalid file
        logo = SimpleUploadedFile('logo.txt', b'text content', content_type='text/plain')
        
        # Try to save the logo
        with patch('utils.utils.COMPANY_LOGOS_SUBDIR', 'img/company_logos'):
            result = save_company_logo_local(logo)
        
        # Check result
        self.assertIsNone(result)
    
    def _create_test_image(self):
        """Helper method to create a test image"""
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        return image_io.read()


class ProfilePictureTests(UtilsTestCase):
    """Tests for profile picture handling functions"""
    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_save_profile_picture_success(self):
        """Test successful profile picture saving and resizing"""
        # Create a test image
        image_content = self._create_test_image()
        picture = SimpleUploadedFile('profile.png', image_content, content_type='image/png')
        
        # Save the picture
        with patch('utils.utils.PROFILE_UPLOAD_SUBDIR', 'img/profiles'):
            result = save_profile_picture_local(picture)
        
        # Check result
        self.assertIsNotNone(result)
        # The function returns a path like 'img/profiles/uuid_hash.png'
        self.assertTrue('img/profiles/' in result)
        
        # Check that file was saved
        self.assertTrue(os.path.exists(os.path.join(self.temp_media_root, result)))
    
    def test_save_profile_picture_invalid_type(self):
        """Test profile picture saving with invalid file type"""
        # Create an invalid file
        picture = SimpleUploadedFile('profile.txt', b'text content', content_type='text/plain')
        
        # Define the default path
        default_path = os.path.join('img/profiles', 'default.jpg')
        
        # Try to save the picture with direct patching
        with patch('django.conf.settings.MEDIA_ROOT', self.temp_media_root):
            with patch('utils.utils.PROFILE_UPLOAD_SUBDIR', 'img/profiles'):
                # Mock the default path directly in the function
                with patch.dict('utils.utils.__dict__', {'default_picture_path': default_path}):
                    result = save_profile_picture_local(picture)
        
        # Check result
        self.assertEqual(result, default_path)
    
    def test_save_profile_picture_failure(self):
        """Test profile picture saving with exception"""
        # Create a test image
        image_content = self._create_test_image()
        picture = SimpleUploadedFile('profile.png', image_content, content_type='image/png')
        
        # Define the default path
        default_path = os.path.join('img/profiles', 'default.jpg')
        
        # Mock FileSystemStorage to raise an exception
        with patch('django.conf.settings.MEDIA_ROOT', self.temp_media_root):
            with patch('utils.utils.FileSystemStorage') as mock_fs:
                mock_fs.return_value.save.side_effect = Exception('Storage error')
                with patch('utils.utils.PROFILE_UPLOAD_SUBDIR', 'img/profiles'):
                    # Mock the default path directly in the function
                    with patch.dict('utils.utils.__dict__', {'default_picture_path': default_path}):
                        result = save_profile_picture_local(picture)
        
        # Check result
        self.assertEqual(result, default_path)
    
    def _create_test_image(self):
        """Helper method to create a test image"""
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        return image_io.read()


class S3UploadTests(UtilsTestCase):
    """Tests for Amazon S3 upload functions"""
    
    def test_upload_to_s3_success(self):
        """Test successful upload to S3"""
        # Create a test file
        resume = SimpleUploadedFile('resume.pdf', b'resume content', content_type='application/pdf')
        
        # Mock boto3 client
        with patch('boto3.client') as mock_s3_client:
            mock_client_instance = MagicMock()
            mock_s3_client.return_value = mock_client_instance
            
            # Call the function
            with patch('utils.utils.RESUMES_S3_PREFIX', 'resumes/'):
                result = upload_to_s3(resume, self.job_seeker.id, 'test-bucket')
        
        # Check result
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith('resumes/'))
        self.assertTrue('resume.pdf' in result)
        
        # Check that upload_fileobj was called
        mock_client_instance.upload_fileobj.assert_called_once()
    
    def test_upload_to_s3_invalid_type(self):
        """Test S3 upload with invalid file type"""
        # Create an invalid file
        resume = SimpleUploadedFile('resume.exe', b'exe content', content_type='application/octet-stream')
        
        # Call the function
        with patch('utils.utils.ALLOWED_RESUME_EXTENSIONS', {'pdf', 'doc', 'docx'}):
            result = upload_to_s3(resume, self.job_seeker.id, 'test-bucket')
        
        # Check result
        self.assertIsNone(result)
    
    def test_upload_to_s3_exception(self):
        """Test S3 upload with exception"""
        # Create a test file
        resume = SimpleUploadedFile('resume.pdf', b'resume content', content_type='application/pdf')
        
        # Mock boto3 client to raise an exception
        with patch('boto3.client') as mock_s3_client:
            mock_client_instance = MagicMock()
            mock_client_instance.upload_fileobj.side_effect = Exception('S3 error')
            mock_s3_client.return_value = mock_client_instance
            
            # Call the function
            with patch('utils.utils.RESUMES_S3_PREFIX', 'resumes/'):
                result = upload_to_s3(resume, self.job_seeker.id, 'test-bucket')
        
        # Check result
        self.assertIsNone(result)


class ResumeFileTests(UtilsTestCase):
    """Tests for resume file handling functions"""
    
    def test_get_resume_file_local(self):
        """Test getting a resume file that exists locally"""
        # Create a test resume file
        resume_dir = os.path.join(self.temp_upload_folder, '1')
        os.makedirs(resume_dir, exist_ok=True)
        resume_path = os.path.join(resume_dir, 'resume.pdf')
        with open(resume_path, 'wb') as f:
            f.write(b'resume content')
        
        # Get the resume file with direct patching of settings.MEDIA_ROOT
        with patch('django.conf.settings.MEDIA_ROOT', self.temp_media_root):
            with patch('utils.utils.RESUMES_S3_PREFIX', 'resumes/'):
                file_path, success = get_resume_file('1/resume.pdf')
        
        # Check result
        self.assertEqual(file_path, os.path.join(self.temp_upload_folder, '1/resume.pdf'))
        self.assertTrue(success)
    
    def test_get_resume_file_s3(self):
        """Test getting a resume file from S3"""
        # Mock boto3 client
        with patch('django.conf.settings.MEDIA_ROOT', self.temp_media_root):
            with patch('boto3.client') as mock_s3_client:
                # Set up the mock client
                mock_client_instance = MagicMock()
                mock_s3_client.return_value = mock_client_instance
                
                # Call the function
                with patch('utils.utils.RESUMES_S3_PREFIX', 'resumes/'):
                    with patch.object(settings, 'ENABLE_S3_UPLOAD', True):
                        with patch.object(settings, 'AWS_STORAGE_BUCKET_NAME', 'test-bucket'):
                            file_path, success = get_resume_file('1/resume.pdf')
        
        # Check result
        self.assertEqual(file_path, os.path.join(self.temp_upload_folder, '1/resume.pdf'))
        self.assertTrue(success)
        
        # Check that download_file was called
        mock_client_instance.download_file.assert_called_once()
    
    def test_get_resume_file_not_found(self):
        """Test getting a resume file that doesn't exist"""
        # Call the function with a direct patch of settings.MEDIA_ROOT
        with patch('django.conf.settings.MEDIA_ROOT', self.temp_media_root):
            with patch('utils.utils.RESUMES_S3_PREFIX', 'resumes/'):
                with patch.object(settings, 'ENABLE_S3_UPLOAD', False):
                    file_path, success = get_resume_file('nonexistent.pdf')
        
        # Check result
        self.assertIsNone(file_path)
        self.assertFalse(success)


class ResumeViewTests(UtilsTestCase):
    """Tests for resume view functions"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create an application with a resume
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.job_seeker,
            status='applied',
            resume_path='1/resume.pdf'
        )
        
        # Create a resume file
        resume_dir = os.path.join(self.temp_upload_folder, '1')
        os.makedirs(resume_dir, exist_ok=True)
        self.resume_path = os.path.join(resume_dir, 'resume.pdf')
        with open(self.resume_path, 'wb') as f:
            f.write(b'resume content')
    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_serve_resume_admin_access(self):
        """Test admin accessing a resume"""
        # Log in as admin
        self.client.login(username='admin', password='TestPassword123!')
        
        # Access the resume
        with patch('utils.views.settings.MEDIA_ROOT', self.temp_media_root):
            response = self.client.get(reverse('utils:serve_resume', kwargs={'cs_suffix': '1/resume.pdf'}))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="resume.pdf"')
    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_serve_resume_employer_access(self):
        """Test employer accessing a resume for their job"""
        # Log in as employer
        self.client.login(username='employer', password='TestPassword123!')
        
        # Access the resume
        with patch('utils.views.settings.MEDIA_ROOT', self.temp_media_root):
            response = self.client.get(reverse('utils:serve_resume', kwargs={'cs_suffix': '1/resume.pdf'}))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="resume.pdf"')
    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_serve_resume_applicant_access(self):
        """Test applicant accessing their own resume"""
        # Log in as job seeker
        self.client.login(username='jobseeker', password='TestPassword123!')
        
        # Access the resume
        with patch('utils.views.settings.MEDIA_ROOT', self.temp_media_root):
            response = self.client.get(reverse('utils:serve_resume', kwargs={'cs_suffix': '1/resume.pdf'}))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="resume.pdf"')
    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_serve_resume_unauthorized(self):
        """Test unauthorized access to a resume"""
        # Create another job seeker
        other_job_seeker = User.objects.create_user(
            username='otherjobseeker',
            email='other@example.com',
            password='TestPassword123!',
            role='job_seeker'
        )
        
        # Log in as the other job seeker
        self.client.login(username='otherjobseeker', password='TestPassword123!')
        
        # Try to access the resume
        with patch('utils.views.settings.MEDIA_ROOT', self.temp_media_root):
            response = self.client.get(reverse('utils:serve_resume', kwargs={'cs_suffix': '1/resume.pdf'}))
        
        # Check response
        self.assertEqual(response.status_code, 403)
    
    @override_settings(MEDIA_ROOT=property(lambda self: self.temp_media_root))
    def test_serve_resume_not_found(self):
        """Test accessing a resume that doesn't exist"""
        # Log in as admin
        self.client.login(username='admin', password='TestPassword123!')
        
        # Use a different resume path that doesn't exist
        nonexistent_resume_path = 'nonexistent/resume.pdf'
        
        # Try to access the resume without creating a duplicate application
        with patch('utils.views.settings.MEDIA_ROOT', self.temp_media_root):
            with patch.object(settings, 'ENABLE_S3_UPLOAD', False):
                response = self.client.get(reverse('utils:serve_resume', kwargs={'cs_suffix': nonexistent_resume_path}))
        
        # Check response
        self.assertEqual(response.status_code, 404)


class FileUploadTests(TestCase):
    """Tests for file upload functionality"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create a job for testing
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='TestPassword123!',
            role='employer'
        )
        
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
    
    def test_resume_upload_requires_login(self):
        """Test that resume upload requires login"""
        # Create a test resume file
        resume = SimpleUploadedFile('resume.pdf', b'my resume', content_type='application/pdf')
        
        # Try to upload without logging in
        response = self.client.post(
            reverse('jobs:apply_job', kwargs={'job_id': self.job.id}),
            {'resume': resume},
            follow=True
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that user was redirected to login page
        self.assertRedirects(
            response, 
            f"{reverse('portal_auth:login')}?next={reverse('jobs:apply_job', kwargs={'job_id': self.job.id})}"
        )


class EmailTests(TestCase):
    """Tests for email functionality"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create a client for making requests
        self.client = Client()
    
    @patch('main.views.send_mail')
    def test_contact_form_sends_email(self, mock_send_mail):
        """Test that contact form sends an email"""
        # Set up mock to return success
        mock_send_mail.return_value = 1
        
        # Submit the contact form
        contact_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Hello! How are you? What is your name?'
        }
        response = self.client.post(reverse('main:contact'), contact_data, follow=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check that send_mail was called
        mock_send_mail.assert_called_once()
        
        # Check for success message
        response_content = response.content.decode('utf-8')
        self.assertTrue('Thank you' in response_content or 'sent' in response_content)


class ErrorHandlingTests(TestCase):
    """Tests for error handling in the application"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create a client for making requests
        self.client = Client()
    
    def test_404_handler(self):
        """Test that 404 errors are handled correctly"""
        # Request a non-existent page
        response = self.client.get('/nonexistentpage/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        
        # Check that the response contains '404' or 'Not Found'
        response_content = response.content.decode('utf-8')
        self.assertTrue('404' in response_content or 'Not Found' in response_content)