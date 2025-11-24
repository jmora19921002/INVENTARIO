import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuración de PostgreSQL
    # Formato: postgresql://usuario:contraseña@host:puerto/nombre_base_datos
    # Ejemplo: postgresql://postgres:password@localhost:5432/inventario
    # Valores por defecto para la base de datos de Render
    DATABASE_USER = os.environ.get('DATABASE_USER') or 'inventario_0etk_user'
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD') or 'cMmhn0IfeHBHr0hXQgoml2GUzqLICjpY'
    DATABASE_HOST = os.environ.get('DATABASE_HOST') or 'dpg-d4i7qo6mcj7s73cep8fg-a'
    DATABASE_PORT = os.environ.get('DATABASE_PORT') or '5432'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'inventario_0etk'
    
    # Si DATABASE_URL está definida, usarla directamente (útil para servicios como Heroku, Railway, Render, etc.)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render puede usar postgres:// en lugar de postgresql://
        # SQLAlchemy requiere postgresql://, así que lo convertimos si es necesario
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

