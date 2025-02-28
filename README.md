# guignote-backend
Repositorio correspondiente al desarrollo del backend de la aplicación 'Sota, caballo y rey' para jugar al guiñote.
---
## Poner en funcionamiento
>git clone \<repositorio\>  
>cd guignote-backend/sotacaballorey/  
>python -m venv env  
>source env/bin/activate  
>pip install django PyJWT  
>python manage.py migrate  
>python manage.py makemigrations  
>python manage.py runserver  

---
Todos los datos deben enviarse en **JSON**. Cuando se inicia sesión o crea cuenta el frontend deberá encargarse de almacenar el token jwt generado. **Se pasará este token en la cabecera de algunas peticiones que requieren de autenticacion**.

## Crear un usuario
**Endpoint**

> POST http://127.0.0.1:8000/usuarios/crear_usuario/

**Parámetros en el cuerpo (JSON)**
>{  
>"nombre": ___,  
>"correo": ___,  
>"contrasegna": ____  
>}

**Respuestas erróneas**
>{"error": descripción_del_error}
- 400: faltan campos | correo o nombre ya en uso
- 405: método no permitido

**Respuesta exitosa (201)**
>{  
>"token": jwt_generado_para_el_usuario  
>}

## Inciar sesión
**Endpoint**

> POST http://127.0.0.1:8000/usuarios/iniciar_sesion/

**Parámetros en el cuerpo (JSON)**

Puedes poner solo el nombre y la contraseña, o el correo y la contraseña. No es necesario rellenar todos los campos del cuerpo.
>{  
>"nombre": ___,  
>"correo": ___,  
>"contrasegna": ____  
>}

**Respuestas erróneas**
>{"error": descripción_del_error}
- 400: faltan campos | contraseña incorrecta
- 404: usuario no encontrado
- 405: método no permitido

**Respuesta exitosa (201)**
>{  
>"token": jwt_generado_para_el_usuario  
>}

## Eliminar usuario
**Endpoint**

> POST http://127.0.0.1:8000/usuarios/eliminar_usuario/

**Encabezado (Obligatorio)**

> Auth: <tu_token_jwt>

**Respuestas erróneas**
- 401: token inválido o expirado
- 405: método no permitido

**Respuesta exitosa (200)**
>{"mensaje": "Usuario eliminado con éxito"}
