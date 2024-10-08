# Generated by Django 5.1 on 2024-08-26 01:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_alter_timelog_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timelog',
            name='action',
            field=models.CharField(choices=[('IN', 'Time In'), ('OUT', 'Time Out')], max_length=3),
        ),
        migrations.AlterField(
            model_name='timelog',
            name='duration',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='timelog',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='timelogs/%Y/%m/%d/'),
        ),
    ]
