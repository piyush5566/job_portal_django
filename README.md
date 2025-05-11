# Job Portal Django

A full-featured job portal web application built with Django, allowing job seekers to find and apply for jobs, employers to post job listings, and administrators to manage the entire platform.

Live Deployment: https://oco78cjc1j.execute-api.us-east-1.amazonaws.com/demo

## 🌟 Features

### For Job Seekers
- Create and manage user profiles
- Search and filter job listings
- Apply to jobs with resume upload
- Track application status
- View application history

### For Employers
- Post and manage job listings
- Upload company logos
- Review job applications
- Update application statuses
- Manage company profile

### For Administrators
- Comprehensive dashboard with statistics
- User management (create, edit, delete)
- Job management (create, edit, delete)
- Application oversight
- Platform monitoring

## 📋 Tech Stack

- **Backend**: Django 5.2
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Storage**: AWS S3 for static and media files
- **Deployment**: AWS Lambda with Zappa (serverless)
- **Authentication**: Django's built-in authentication system
- **Package Management**: Poetry
- **Testing**: Django Test Framework with coverage

## 🚀 Installation

### Prerequisites
- Python 3.12+
- Poetry (package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job_portal_django
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run migrations**
   ```bash
   poetry run python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   poetry run python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   poetry run python manage.py runserver
   ```

7. **Access the application**
   - Main site: http://localhost:8000/
   - Admin interface: http://localhost:8000/admin/

## 🌐 Deployment

### AWS Lambda Deployment with Zappa

1. **Install deployment dependencies**
   ```bash
   poetry install --with dev
   ```

2. **Configure AWS credentials**
   ```bash
   aws configure
   ```

3. **Update zappa_settings.json if needed**
   ```json
   {
       "demo": {
           "django_settings": "config.settings.prod",
           "profile_name": "default",
           "s3_bucket": "zappa-job-portal-demo",
           "aws_region": "us-east-1",
           "manage_roles": false,
           "role_name": "job-portal-demo-ZappaLambdaExecutionRole"
       }
   }
   ```

4. **Deploy to AWS Lambda**
   ```bash
   zappa deploy demo
   ```

5. **Run migrations on Lambda**
   ```bash
   zappa manage demo migrate
   ```

6. **Create superuser on Lambda**
   ```bash
   zappa invoke --raw demo "from portal_auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'securepassword', role='admin')"
   ```

7. **Upload static files to S3**
   ```bash
   python manage.py collectstatic --no-input --settings=config.settings.prod
   aws s3 sync staticfiles/ s3://job-portal-demo-static/static/ --no-progress
   aws s3 sync media/ s3://job-portal-demo-static/static/ --no-progress
   ```

## 📁 Project Structure

```
job_portal_django/
├── config/                 # Project configuration
│   ├── settings/           # Settings modules (base, dev, prod)
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── employer/               # Employer app
├── job_seeker/             # Job seeker app
├── jobs/                   # Jobs app (listings and applications)
├── main/                   # Main app (home, about, contact)
├── portal_admin/           # Admin portal app
├── portal_auth/            # Authentication app
├── static/                 # Static files
├── templates/              # HTML templates
├── utils/                  # Utility functions
├── .env.example            # Example environment variables
├── manage.py               # Django management script
├── pyproject.toml          # Poetry configuration
└── zappa_settings.json     # Zappa deployment configuration
```

## 🔍 Models

### User Model
- Extended Django's AbstractUser
- Role-based (job_seeker, employer, admin)
- Profile picture support

### Job Model
- Title, description, salary, location, category
- Company information and logo
- Posted date and poster reference

### Application Model
- Job and applicant references
- Application date and status tracking
- Resume upload support

## 🧪 Testing

Run tests with coverage:

```bash
poetry env activate

coverage run manage.py test
coverage report
coverage html  # For detailed HTML report
```

## 🛠️ Development

### Adding New Features

1. Create a new branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests
   ```bash
   poetry run python manage.py test
   ```

4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributors

- Piyush Kumar - Initial work and maintenance

## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap for the frontend components
- AWS for hosting infrastructure