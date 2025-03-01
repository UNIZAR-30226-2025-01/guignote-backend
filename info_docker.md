# Requisitos Descarga Docker

**1. Instalar paquetes necesarios:**

```
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release
```

**2. Agregar clave GPG oficial de Docker:**

```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

**3. Configurar repositorio Docker:**

```
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

**4. Actualizar índice de paquetes e instalar Docker Engine:**

```
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io
```

**5. Iniciar y habilitar servicio Docker:**

```
sudo systemctl start docker
sudo systemctl enable docker
```

**6. Verificar que Docker esté funcionando:**

```
sudo docker run hello-world
```

**7. Ejecutar Docker sin contraseña:**

```
sudo usermod -aG docker $USER
```

---

# Comandos Docker

- **Descargar una imagen de un repositorio:**

  ```
  docker pull nombre_imagen:tag
  ```
  
  *Nota:* Si no se especifica el tag, se usa "latest" por defecto.

- **Construir una imagen a partir de un Dockerfile:**

  ```
  docker build -t nombre_imagen:tag ruta_del_dockerfile
  ```

- **Crear y ejecutar un contenedor basado en una imagen específica:**

  ```
  docker run [opciones] nombre_imagen:tag
  ```
  
  - Con la opción `-d` se ejecuta el contenedor en segundo plano.
  - Con la opción `--name <nombre-contenedor>` se asigna un nombre personalizado al contenedor.

- **Mostrar la lista de contenedores en ejecución:**

  ```
  docker ps
  ```
  
  Para ver todos, incluidos los detenidos:

  ```
  docker ps -a
  ```

- **Detener un contenedor en ejecución:**

  ```
  docker stop <nombre-contenedor>
  ```

- **Eliminar un contenedor detenido:**

  ```
  docker rm <nombre-contenedor>
  ```

- **Ejecutar un comando dentro de un contenedor en ejecución:**

  ```
  docker exec -it nombre_contenedor comando
  ```
  
  *Ejemplo:* Para abrir una sesión interactiva con Bash:

  ```
  docker exec -it mi_contenedor bash
  ```

- **Listar todas las imágenes descargadas:**

  ```
  docker images
  ```

