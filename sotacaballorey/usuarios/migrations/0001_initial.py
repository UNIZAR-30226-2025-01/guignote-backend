# Generated by Django 5.1.6 on 2025-02-28 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=64, unique=True)),
                ('correo', models.CharField(max_length=320, unique=True)),
                ('contrasegna', models.CharField(max_length=128)),
            ],
        ),
    ]
