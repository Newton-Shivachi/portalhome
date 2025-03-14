# Generated by Django 5.0.4 on 2025-03-07 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0002_alter_house_latitude_alter_house_longitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')], default='pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='payment',
            name='expires_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
