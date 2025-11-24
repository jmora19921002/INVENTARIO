import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuración de PostgreSQL
    # Formato: postgresql://usuario:contraseña@host:puerto/nombre_base_datos
    # Ejemplo: postgresql://postgres:password@localhost:5432/inventario
    DATABASE_USER = os.environ.get('DATABASE_USER') or 'postgres'
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD') or 'dimasoftwares'
    DATABASE_HOST = os.environ.get('DATABASE_HOST') or 'localhost'
    DATABASE_PORT = os.environ.get('DATABASE_PORT') or '5432'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'inventario'
    
    # Si DATABASE_URL está definida, usarla directamente (útil para servicios como Heroku, Railway, etc.)
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    else:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

