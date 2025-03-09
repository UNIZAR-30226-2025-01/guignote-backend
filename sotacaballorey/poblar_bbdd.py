import random
from django.db import transaction
from usuarios.models import Usuario, SolicitudAmistad
from django.contrib.auth.hashers import make_password


# Lista de usuarios a crear
nombres_usuarios = [
    "Julia", "Julio", "Julito", "María", "Marta", "Marcelo", "Mario", "Marcos",
    "Adrían", "Adriana", "Jorge", "Diego", "Oscar", "Javier"
]

# Función para crear usuarios
def crear_usuarios():
    usuarios = {
        usuario.id: usuario
        for usuario in Usuario.objects.bulk_create([
            Usuario(
                nombre=nombre,
                correo=f'{nombre.lower()}@ejemplo.com',
                contrasegna=make_password('123')
            )
            for nombre in nombres_usuarios
        ])
    }
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