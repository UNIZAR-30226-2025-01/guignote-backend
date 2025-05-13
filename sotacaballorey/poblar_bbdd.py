import random
from django.db import transaction
from usuarios.models import Usuario, SolicitudAmistad
from django.contrib.auth.hashers import make_password


# Lista de usuarios a crear
nombres_usuarios = [
    "Julia", "Julio", "Julito", "María", "Marta", "Marcelo", "Mario", "Marcos",
    "Adrían", "Adriana", "Jorge", "Diego", "Oscar", "Javier", "José", "Alberto", "Alejandro",
    "Guiri", "Casual", "Octogenario", "Leyenda", "Parroquiano"
]

# Función para crear usuarios
def crear_usuarios():
    elo_personalizado = {
            "Guiri": 1000,
            "Casual": 1400,
            "Parroquiano": 1800,
            "Octogenario": 2400,
            "Leyenda": 3000
    }
    usuarios = {
        usuario.nombre: usuario
        for usuario in Usuario.objects.bulk_create([
            Usuario(
                nombre=nombre,
                correo=f'{nombre.lower()}@ejemplo.com',
                contrasegna=make_password('123'),
                elo=1200
            )
            for nombre in nombres_usuarios
        ])
    }
    
    for nombre, elo in elo_personalizado.items():
        user = usuarios.get(nombre)
        if user:
            user.elo = elo
            user.save()

    return usuarios

# Función para crear solicitudes de amistad
def crear_solicitudes_amistad(usuarios):
    usuarios_lista = list(usuarios.values())
    solicitudes = []

    for emisor in usuarios_lista:
        posibles_receptores = [u for u in usuarios_lista if u != emisor]
        random.shuffle(posibles_receptores)
        for receptor in posibles_receptores[:random.randint(2, 4)]:
            solicitudes.append(SolicitudAmistad(emisor=emisor, receptor=receptor))

    SolicitudAmistad.objects.bulk_create(solicitudes)

# Función para aceptar solicitudes y convertirlas en amistades
def aceptar_solicitudes():
    solicitudes = list(SolicitudAmistad.objects.all())
    random.shuffle(solicitudes)

    for solicitud in solicitudes[:len(solicitudes)//2]:
        solicitud.emisor.amigos.add(solicitud.receptor)
        solicitud.receptor.amigos.add(solicitud.emisor)
        solicitud.delete()

with transaction.atomic():
    usuarios = crear_usuarios()
    crear_solicitudes_amistad(usuarios)
    aceptar_solicitudes()
