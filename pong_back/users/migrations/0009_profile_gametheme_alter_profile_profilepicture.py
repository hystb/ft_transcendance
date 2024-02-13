# Generated by Django 5.0.1 on 2024-02-08 13:54

import users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_remove_profile_is_2fa'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='gameTheme',
            field=models.CharField(default='default', max_length=64),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profilePicture',
            field=models.ImageField(blank=True, default='pokemon.png', upload_to=users.models.generateUniqueImageID),
        ),
    ]
