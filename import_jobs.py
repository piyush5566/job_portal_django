#!/usr/bin/env python
"""
Script to import job data from a CSV file into the jobs_job table using Django's ORM.
Run this script from the Django project root using:
python manage.py shell < import_jobs.py
"""

import csv
import os
import sys
import django
from datetime import datetime
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

# Import models after Django setup
from jobs.models import Job
from portal_auth.models import User

def import_jobs_from_csv(csv_file_path):
    """Import jobs from CSV file into the database."""
    
    print(f"Importing jobs from {csv_file_path}...")
    
    # Check if file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: File {csv_file_path} not found.")
        return
    
    # Count existing jobs
    existing_jobs_count = Job.objects.count()
    print(f"Current job count in database: {existing_jobs_count}")
    
    # Track stats
    jobs_created = 0
    jobs_skipped = 0
    errors = 0
    
    # Get all users for reference
    users = {user.id: user for user in User.objects.all()}
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            try:
                # Skip if job with this ID already exists
                job_id = int(row['id'])
                if Job.objects.filter(id=job_id).exists():
                    print(f"Job ID {job_id} already exists. Skipping.")
                    jobs_skipped += 1
                    continue
                
                # Get poster user object
                poster_id = int(row['poster_id'])
                poster = users.get(poster_id)
                
                if not poster:
                    print(f"User with ID {poster_id} not found. Skipping job ID {job_id}.")
                    jobs_skipped += 1
                    continue
                
                # Parse posted_date
                try:
                    posted_date = datetime.fromisoformat(row['posted_date'])
                    # Make timezone-aware if it's naive
                    if posted_date.tzinfo is None:
                        posted_date = timezone.make_aware(posted_date)
                except ValueError:
                    # Default to current time if date parsing fails
                    posted_date = timezone.now()
                    print(f"Warning: Invalid date format for job ID {job_id}. Using current time.")
                
                # Create job object
                job = Job(
                    id=job_id,
                    title=row['title'],
                    description=row['description'],
                    salary=row['salary'],
                    location=row['location'],
                    category=row['category'],
                    company=row['company'],
                    posted_date=posted_date,
                    poster=poster,
                    company_logo=row['company_logo']
                )
                
                # Save to database
                job.save()
                jobs_created += 1
                print(f"Created job: {job.title} (ID: {job.id})")
                
            except Exception as e:
                print(f"Error processing row {row.get('id', 'unknown')}: {str(e)}")
                errors += 1
    
    # Print summary
    print("\nImport Summary:")
    print(f"Jobs created: {jobs_created}")
    print(f"Jobs skipped: {jobs_skipped}")
    print(f"Errors: {errors}")
    print(f"Total jobs in database: {Job.objects.count()}")

if __name__ == "__main__":
    # Path to CSV file - adjust as needed
    csv_file_path = os.path.join('jobs', 'jobs.csv')
    import_jobs_from_csv(csv_file_path)
