# Generated by Django 5.1 on 2024-09-19 13:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0014_pendingapplication_pendingstatusarchive_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evaluation', models.FloatField()),
                ('docs', models.FloatField()),
                ('oral_interview', models.FloatField()),
                ('final_grade', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(default='Pending', max_length=10)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='students.datatablestudents')),
            ],
        ),
    ]