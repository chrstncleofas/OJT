# Generated by Django 5.1 on 2024-10-24 01:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0032_rename_hte_datatablestudents_department_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendingapplication',
            name='ContactNumber',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
        migrations.AddField(
            model_name='pendingapplication',
            name='Department',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='pendingapplication',
            name='HTEAddress',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='pendingapplication',
            name='NameOfSupervisor',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='rejectapplication',
            name='ContactNumber',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
        migrations.AddField(
            model_name='rejectapplication',
            name='Department',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='rejectapplication',
            name='HTEAddress',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='rejectapplication',
            name='NameOfSupervisor',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
