# Generated by Django 5.1.6 on 2025-03-01 15:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='amigos',
            field=models.ManyToManyField(blank=True, to='usuarios.usuario'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='correo',
            field=models.EmailField(max_length=320, unique=True),
        ),
        migrations.CreateModel(
            name='SolicitudAmistad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_enviadas', to='usuarios.usuario')),
                ('receptor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_recibidas', to='usuarios.usuario')),
            ],
            options={
                'unique_together': {('emisor', 'receptor')},
            },
        ),
    ]
