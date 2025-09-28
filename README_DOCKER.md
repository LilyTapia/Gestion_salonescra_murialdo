# Proyecto Django + MySQL con Docker

Este proyecto utiliza Docker y Docker Compose para levantar un entorno de desarrollo con Django y MySQL.

## Requisitos previos
- Docker
- Docker Compose

## Estructura de servicios
- **db**: Contenedor MySQL 8.0
- **web**: Contenedor Django

## Variables de entorno
Las variables necesarias están definidas en el archivo `.env.docker`:
- `DB_USER=root`
- `DB_PASSWORD=Ene0208.`
- `DB_HOST=db` (nombre del servicio Docker)
- `DB_PORT=3306` (puerto interno del contenedor)
- `MYSQL_ROOT_PASSWORD=Ene0208.` (configurado en docker-compose.yml)

## Levantar el entorno

```bash
docker-compose up --build
```

Esto construirá la imagen de Django y levantará ambos servicios. El servicio web esperará a que la base de datos esté lista antes de iniciar.

## Acceso a la aplicación
- Django: [http://localhost:8000](http://localhost:8000)
- MySQL: Puerto 3308 en tu máquina local (mapeado desde 3306 del contenedor)

## Conexión a MySQL desde tu máquina local
Puedes conectarte usando cualquier cliente MySQL:
- **Host**: 127.0.0.1
- **Puerto**: 3308 (mapeado desde el contenedor)
- **Usuario**: root
- **Contraseña**: Ene0208.
- **Base de datos**: salones_cra

## Comandos útiles
- Parar los servicios:
  ```bash
  docker-compose down
  ```
- Ver logs:
  ```bash
  docker-compose logs -f
  ```

## Reiniciar el servidor web
- **Reiniciar solo el contenedor web:**
  ```bash
  docker-compose restart web
  ```
- **Parar y levantar el servicio web:**
  ```bash
  docker-compose stop web
  docker-compose start web
  ```
- **Reiniciar todos los servicios:**
  ```bash
  docker-compose restart
  ```
- **Reconstruir y reiniciar (si cambiaste dependencias):**
  ```bash
  docker-compose down
  docker-compose up --build
  ```
- **Solo el contenedor web con reconstrucción:**
  ```bash
  docker-compose up --build web
  ```
- **Ver logs del servidor:**
  ```bash
  docker-compose logs -f web
  ```

## Notas
- Los datos de MySQL se almacenan en el volumen `db_data` y persisten entre reinicios.
- La configuración MySQL usa solo `MYSQL_ROOT_PASSWORD` (no `MYSQL_USER`/`MYSQL_PASSWORD` para evitar conflictos con root).
- Django se conecta usando las credenciales root definidas en `.env.docker`.

---

Para cualquier duda, revisa los archivos `docker-compose.yml`, `.env.docker` y `entrypoint.sh` para entender el flujo de arranque y conexión.
