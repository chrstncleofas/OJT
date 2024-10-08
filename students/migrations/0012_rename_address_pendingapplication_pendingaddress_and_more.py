# Generated by Django 5.1 on 2024-09-17 01:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0011_alter_datatablestudents_status_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Address',
            new_name='PendingAddress',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Course',
            new_name='PendingCourse',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Email',
            new_name='PendingEmail',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Firstname',
            new_name='PendingFirstname',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Image',
            new_name='PendingImage',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Lastname',
            new_name='PendingLastname',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Middlename',
            new_name='PendingMiddlename',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Number',
            new_name='PendingNumber',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Password',
            new_name='PendingPassword',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Prefix',
            new_name='PendingPrefix',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='StudentID',
            new_name='PendingStudentID',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Username',
            new_name='PendingUsername',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='Year',
            new_name='PendingYear',
        ),
        migrations.RenameField(
            model_name='pendingapplication',
            old_name='status',
            new_name='StatusApplication',
        ),
    ]
