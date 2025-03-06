# guignote-backend
Repositorio correspondiente al desarrollo del backend de la aplicación 'Sota, caballo y rey' para jugar al guiñote.
---
## Poner en funcionamiento
>./build.sh  
>./run.sh

---
Todos los datos deben enviarse en **JSON**. Cuando se inicia sesión o crea cuenta el frontend deberá encargarse de almacenar el token jwt generado. **Se pasará este token en la cabecera de algunas peticiones que requieren de autenticacion**.

## Crear un usuario
**Endpoint**
> POST http://188.165.76.134:8000/usuarios/crear_usuario/

**Parámetros en el cuerpo (JSON)**
>{  
>"nombre": ___,  
>"correo": ___,  
>"contrasegna": ____  
>}

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 400: faltan campos | correo o nombre ya en uso
- 405: método no permitido

**Respuesta exitosa (201)**
>{  
>"token": jwt_generado_para_el_usuario  
>}

## Inciar sesión
**Endpoint**
> POST http://188.165.76.134:8000/usuarios/iniciar_sesion/

**Parámetros en el cuerpo (JSON)**  
Puedes poner solo el nombre y la contraseña, o el correo y la contraseña. No es necesario rellenar todos los campos del cuerpo.
>{  
>"nombre": ___,  
>"correo": ___,  
>"contrasegna": ____  
>}

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 400: faltan campos | contraseña incorrecta
- 404: usuario no encontrado
- 405: método no permitido

**Respuesta exitosa (201)**
>{  
>"token": jwt_generado_para_el_usuario  
>}

## Eliminar usuario
**Endpoint**
> POST http://188.165.76.134:8000/usuarios/eliminar_usuario/

**Encabezado (Obligatorio)**
> Auth: <tu_token_jwt>

**Respuestas erróneas**
- 401: token inválido o expirado

**Respuesta exitosa (200)**
>{  
>"mensaje": "Usuario eliminado con éxito"  
>}

## Obtener lista de amigos

**Endpoint**
> GET http://188.165.76.134:8000/usuarios/obtener_amigos/

**Encabezado (Obligatorio)**
> Auth: <tu_token_jwt>

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 401: token inválido o expirado
- 405: método no permitido

**Respuesta exitosa**
>{  
>"amigos":  
>[  
>{"id": "id_usuario", "nombre": "nombre_usuario"},  
>...  
>]  
>}

## Enviar solicitud de amistad

**Endpoint**
> POST http://188.165.76.134:8000/usuarios/enviar_solicitud_amistad/

**Encabezado (Obligatorio)**
> Auth: <tu_token_jwt>

**Parámetros en el cuerpo (JSON)**
>{  
> "destinatario_id": "id_del_usuario"  
>}

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 400: faltan campos | la solicitud ya fue enviada
- 401: token inválido o expirado
- 404: destinatario no encontrado
- 405: método no permitido

**Respuesta exitosa (201)**
>{  
>"mensaje": "Solicitud enviada con éxito"  
>}

## Aceptar solicitud de amistad

**Endpoint**
> POST http://188.165.76.134:8000/usuarios/aceptar_solicitud_amistad/

**Encabezado (Obligatorio)**
> Auth: <tu_token_jwt>

**Parámetros en el cuerpo (JSON)**
>{  
> "solicitud_id": "id_de_la_solicitud"  
>}

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 400: faltan campos
- 401: token inválido o expirado
- 403: no puedes aceptar una solicitud que no te pertenece
- 404: solicitud no encontrada
- 405: método no permitido

**Respuesta exitosa (201)**
>{  
>"mensaje": "Solicitud aceptada con éxito"  
>}

## Listar solicitudes de amistad pendientes

**Endpoint**
> GET http://188.165.76.134:8000/usuarios/listar_solicitudes_amistad/

**Encabezado (Obligatorio)**
> Auth: <tu_token_jwt>

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 401: token inválido o expirado
- 405: método no permitido

**Respuesta exitosa (200)**
>{  
>"solicitudes":  
>[  
>{"id": "id_solicitud", "solicitante": "nombre_solicitabte"},  
>...  
>]  
>}

## Eliminar amigo

**Endpoint**
> GET DELETE http://188.165.76.134:8000/usuarios/eliminar_amigo/

**Encabezado (Obligatorio)**
> Auth: <tu_token_jwt>

**Parámetros de la URL**
>?amigo_id=id_del_usuario

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 400: faltan campos
- 401: token inválido o expirado
- 404: amigo no encontrado
- 405: método no permitido

**Respuesta exitosa (200)**
>{"mensaje": "Amigo eliminado con éxito"}

## Buscar usuarios por nombre

**Endpoint**
> GET http://188.165.76.134:8000/usuarios/buscar_usuarios/

**Encabezado (Obligatorio)**
> Auth: <tu_token_jwt>

**Parámetros de la URL**
> ?nombre=nombre_a_buscar&incluir_amigos=true|false

**Respuestas erróneas**
>{"error": "descripción_del_error"}
- 401: token inválido o expirado
- 405: método no permitido

**Respuesta exitosa (200)**
>{  
>"usuarios":  
>[  
>{"id": "id_usuario", "nombre": "nombre_usuario"},  
>...  
>]  
>}

