# Guía de Migración a PostgreSQL

## Requisitos Previos

1. **Instalar PostgreSQL**
   - Windows: Descargar desde https://www.postgresql.org/download/windows/
   - Durante la instalación, anota el usuario y contraseña del superusuario (por defecto: `postgres`)

2. **Instalar dependencias de Python**
   ```bash
   pip install -r requirements.txt
   ```

## Configuración de PostgreSQL

### 1. Crear la base de datos

Abre una terminal de PostgreSQL (psql) o usa pgAdmin y ejecuta:

```sql
CREATE DATABASE inventario;
```

O desde la línea de comandos:
```bash
createdb -U postgres inventario
```

### 2. Configurar las credenciales

Edita el archivo `config.py` o configura las variables de entorno:

**Opción 1: Editar config.py directamente**
```python
DATABASE_USER = 'postgres'
DATABASE_PASSWORD = 'tu_contraseña'
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5432'
DATABASE_NAME = 'inventario'
```

**Opción 2: Usar variables de entorno (recomendado)**
```bash
# Windows PowerShell
$env:DATABASE_USER="postgres"
$env:DATABASE_PASSWORD="tu_contraseña"
$env:DATABASE_HOST="localhost"
$env:DATABASE_PORT="5432"
$env:DATABASE_NAME="inventario"

# Linux/Mac
export DATABASE_USER="postgres"
export DATABASE_PASSWORD="tu_contraseña"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export DATABASE_NAME="inventario"
```

## Migración de Datos

### Opción 1: Migración Automática (Recomendada)

Si tienes datos en SQLite que quieres migrar:

```bash
python migrate_to_postgresql.py
```

Este script:
- Conecta a la base de datos SQLite existente
- Crea las tablas en PostgreSQL
- Migra todos los datos preservando las relaciones

### Opción 2: Crear Tablas desde Cero

Si no necesitas migrar datos existentes, simplemente ejecuta la aplicación:

```bash
python app.py
```

Las tablas se crearán automáticamente en PostgreSQL.

## Verificación

Para verificar que la migración fue exitosa:

```bash
# Conectar a PostgreSQL
psql -U postgres -d inventario

# Listar tablas
\dt

# Ver registros de una tabla
SELECT * FROM user;
SELECT * FROM equipment;
```

## Solución de Problemas

### Error: "could not connect to server"
- Verifica que PostgreSQL esté corriendo
- En Windows: Servicios → PostgreSQL
- En Linux: `sudo systemctl status postgresql`

### Error: "password authentication failed"
- Verifica las credenciales en `config.py`
- Asegúrate de que el usuario tenga permisos en la base de datos

### Error: "database does not exist"
- Crea la base de datos: `CREATE DATABASE inventario;`

### Error: "module 'psycopg2' not found"
- Instala: `pip install psycopg2-binary`

## Variables de Entorno para Producción

Para producción, usa variables de entorno:

```bash
export DATABASE_URL="postgresql://usuario:contraseña@host:puerto/inventario"
```

O en servicios como Heroku, Railway, etc., la variable `DATABASE_URL` se configura automáticamente.

## Notas Importantes

- **Backup**: Siempre haz un backup de tu base de datos SQLite antes de migrar
- **Pruebas**: Prueba la aplicación en un entorno de desarrollo antes de migrar en producción
- **Seguridad**: Nunca subas credenciales a repositorios públicos. Usa variables de entorno

