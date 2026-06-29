# Usa una imagen oficial de Python ligera
FROM python:3.11-slim

# Variables de entorno para optimizar Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Variables de Django
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8000

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL y compilar paquetes
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias
COPY requirements.txt /app/

# Instalar las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto al contenedor
COPY . /app/

# Exponer el puerto en el que correrá Django
EXPOSE 8000

# El comando por defecto levantará el servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
