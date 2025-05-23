# Generated by Django 5.2 on 2025-05-02 10:44

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('applied', 'Applied'), ('pending', 'Pending Review'), ('reviewed', 'Reviewed'), ('rejected', 'Rejected'), ('shortlisted', 'Shortlisted'), ('hired', 'Hired')], db_index=True, default='applied', max_length=20)),
                ('resume_path', models.FileField(blank=True, null=True, upload_to='resumes/')),
            ],
            options={
                'verbose_name': 'Application',
                'verbose_name_plural': 'Applications',
                'ordering': ['-application_date'],
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('salary', models.CharField(blank=True, max_length=50, null=True)),
                ('location', models.CharField(db_index=True, max_length=100)),
                ('category', models.CharField(db_index=True, max_length=50)),
                ('company', models.CharField(db_index=True, max_length=100)),
                ('company_logo', models.ImageField(blank=True, default='img/company_logos/default.png', null=True, upload_to='img/company_logos/')),
                ('posted_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Job',
                'verbose_name_plural': 'Jobs',
                'ordering': ['-posted_date'],
            },
        ),
    ]
